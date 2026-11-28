import grpc
import pytest

from salon_proto import game_pb2 as pb
from salon_proto import game_pb2_grpc as rpc

from salon.cards import CardInstance, Color, Tab, load_cards
from salon.engine.state import GameCard, RowCard
from salon.grpc_server.main import create_server
from salon.grpc_server.servicer import Game

@pytest.fixture
def game():
    return Game()

@pytest.fixture
def stub(game):
    server, port = create_server("127.0.0.1:0", game)   # 0 = any free port
    server.start()
    channel = grpc.insecure_channel(f"127.0.0.1:{port}")
    yield rpc.GameStub(channel)
    channel.close()
    server.stop(0)

def _card(def_id, uid, tabs=()):
    """A hand-made card, to set up an exact situation in the battle state."""
    return GameCard(uid, CardInstance(load_cards()[def_id], tabs))

def _start(stub, seed=1):
    return stub.StartRun(pb.StartRunRequest(seed=seed))

def _play(stub, run, card_uid, connect=False, tab_color=pb.COLOR_UNSPECIFIED):
    return stub.PlayCard(pb.PlayCardRequest(
        session_id=run.session_id, card_uid=card_uid, connect=connect, tab_color=tab_color))

def _end_turn(stub, run):
    return stub.EndTurn(pb.EndTurnRequest(session_id=run.session_id))

def kinds(result):
    return [e.WhichOneof("kind") for e in result.events]

def actor(event):
    """True = player, False = automaton, None = no side in the event."""
    kind = event.WhichOneof("kind")
    if kind == "card_played":
        return event.card_played.by_player
    if kind == "damage":
        return not event.damage.to_player  # to_player=True means the AUTOMATON attacked
    if kind in ("shield_changed", "cards_drawn", "cards_discarded", "energy_changed"):
        return getattr(event, kind).player
    return None


# StartRun


def test_start_run_returns_battle(stub):
    run = _start(stub)
    assert run.session_id
    assert run.battle.player.hp == 50
    assert run.battle.enemy.hp == 30
    assert run.battle.player.energy == 2
    assert len(run.battle.hand) == 5
    assert len(run.battle.enemy_hand) == 5
    assert run.battle.round == 1
    assert run.battle.result == pb.BATTLE_RESULT_ONGOING

def test_same_seed_same_start(stub):
    first = _start(stub, seed=7)
    second = _start(stub, seed=7)
    assert first.battle == second.battle


# PlayCard


def test_play_card_moves_card_to_row(stub):
    run = _start(stub)
    card = run.battle.hand[0]
    result = _play(stub, run, card.uid)
    assert [c.uid for c in result.state.row] == [card.uid]
    assert len(result.state.hand) == 4
    assert result.state.player.energy == 2 - card.cost
    assert kinds(result) == ["card_played", "energy_changed"]

def test_play_unknown_card_is_rejected(stub):
    run = _start(stub)
    with pytest.raises(grpc.RpcError) as err:
        _play(stub, run, card_uid=999)
    assert err.value.code() == grpc.StatusCode.INVALID_ARGUMENT

def test_wrong_session_is_rejected(stub):
    _start(stub)
    with pytest.raises(grpc.RpcError) as err:
        stub.EndTurn(pb.EndTurnRequest(session_id="wrong"))
    assert err.value.code() == grpc.StatusCode.NOT_FOUND

def test_play_before_start_run_is_rejected(stub, game):
    with pytest.raises(grpc.RpcError) as err:
        stub.PlayCard(pb.PlayCardRequest(session_id=game.session_id, card_uid=0))
    assert err.value.code() == grpc.StatusCode.FAILED_PRECONDITION

def test_play_without_energy_is_rejected(stub, game):
    run = _start(stub)
    game.state.player.energy = 0
    with pytest.raises(grpc.RpcError) as err:
        _play(stub, run, run.battle.hand[0].uid)
    assert err.value.code() == grpc.StatusCode.FAILED_PRECONDITION

def test_connect_with_empty_row_is_rejected(stub):
    run = _start(stub)
    with pytest.raises(grpc.RpcError) as err:
        _play(stub, run, run.battle.hand[0].uid, connect=True)
    assert err.value.code() == grpc.StatusCode.FAILED_PRECONDITION

@pytest.mark.parametrize("tab_color", [pb.COLOR_UNSPECIFIED, pb.COLOR_GREEN])
def test_connected_card_activates_tab_and_is_cheaper(stub, game, tab_color):
    run = _start(stub)
    game.state.row = [RowCard(_card("strike", 1000, (Tab(Color.GREEN, 2),)))]
    game.state.player.hand.append(_card("block", 1001))

    result = _play(stub, run, 1001, connect=True, tab_color=tab_color)
    assert kinds(result) == ["card_played", "tab_activated", "energy_changed"]
    assert result.events[1].tab_activated.card_uid == 1000
    assert result.state.player.energy == 2  # block costs 1, connected costs 0


# EndTurn


def test_end_turn_plays_automaton_turn(stub):
    run = _start(stub)
    _play(stub, run, run.battle.hand[0].uid)
    result = _end_turn(stub, run)

    assert result.state.round == 2
    assert len(result.state.row) == 0
    assert result.state.player.energy == 3
    assert result.state.result == pb.BATTLE_RESULT_ONGOING
    assert any(e.WhichOneof("kind") == "card_played" and not e.card_played.by_player
               for e in result.events)

def test_card_played_comes_before_events_that_refer_to_its_uid(stub):
    run = _start(stub)
    events = list(_play(stub, run, run.battle.hand[0].uid).events)
    events += list(_play(stub, run, run.battle.hand[1].uid).events)
    events += list(_end_turn(stub, run).events)

    played = set()
    for e in events:
        kind = e.WhichOneof("kind")
        if kind == "card_played":
            played.add(e.card_played.card.uid)
        elif kind == "tab_activated":
            assert e.tab_activated.card_uid in played
        elif kind == "cards_discarded":
            assert set(e.cards_discarded.card_uids) <= played


def test_player_and_automaton_events_do_not_interleave(stub):
    run = _start(stub)
    _play(stub, run, run.battle.hand[0].uid)
    result = _end_turn(stub, run)

    collapsed = []
    for e in result.events:
        a = actor(e)
        if a is not None and (not collapsed or collapsed[-1] != a):
            collapsed.append(a)
    # player attack -> automaton turn -> start of the player's new turn
    assert collapsed == [True, False, True]


def test_battle_ended_is_the_last_event(stub, game):
    run = _start(stub)
    game.state.enemy.hp = 5
    game.state.player.hand.append(_card("strike", 1000))  # one Strike (5 damage) wins

    _play(stub, run, 1000)
    result = _end_turn(stub, run)
    assert kinds(result) == ["damage", "battle_ended"]
    assert result.events[-1].battle_ended.result == pb.BATTLE_RESULT_WON
    assert result.state.result == pb.BATTLE_RESULT_WON

    with pytest.raises(grpc.RpcError) as err:  # nothing is allowed after the end
        _end_turn(stub, run)
    assert err.value.code() == grpc.StatusCode.FAILED_PRECONDITION

MAX_CALLS = 500


def _play_whole_battle(stub, seed):
    """Play a battle to the end: the player always plays the first affordable card,
    and ends the turn when none is left. Returns the final state and all events."""
    run = _start(stub, seed)
    state = run.battle
    events = []
    for _ in range(MAX_CALLS):
        if state.result != pb.BATTLE_RESULT_ONGOING:
            break
        playable = [c for c in state.hand if c.cost <= state.player.energy]
        result = _play(stub, run, playable[0].uid) if playable else _end_turn(stub, run)
        events += result.events
        state = result.state
    return state, events


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_full_battle_through_grpc(stub, seed):
    state, events = _play_whole_battle(stub, seed)

    assert state.result != pb.BATTLE_RESULT_ONGOING
    assert events[-1].WhichOneof("kind") == "battle_ended"
    assert events[-1].battle_ended.result == state.result
    assert [e.WhichOneof("kind") for e in events].count("battle_ended") == 1
    loser = state.player if state.result == pb.BATTLE_RESULT_LOST else state.enemy
    assert loser.hp == 0


def test_same_seed_same_battle_through_grpc(stub):
    first = _play_whole_battle(stub, seed=5)
    second = _play_whole_battle(stub, seed=5)
    assert first == second