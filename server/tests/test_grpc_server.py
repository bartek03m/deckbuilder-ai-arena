import grpc
import pytest
from salon.grpc_server.servicer import Game
from salon_proto import game_pb2 as pb
from salon_proto import game_pb2_grpc as rpc
from salon.grpc_server.main import create_server


@pytest.fixture
def stub():
    server, port = create_server("127.0.0.1:0")   # 0 = any free port
    server.start()
    channel = grpc.insecure_channel(f"127.0.0.1:{port}")
    yield rpc.GameStub(channel)
    channel.close()
    server.stop(0)


def test_start_run_returns_battle(stub):
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    assert run.session_id
    assert run.battle.player.hp == 50
    assert len(run.battle.hand) == 2


def test_play_card_moves_card_to_row(stub):
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    start_energy = run.battle.player.energy
    result = stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=0))
    assert len(result.state.row) == 1
    assert len(result.state.hand) == 1
    assert result.state.player.energy == start_energy - 1   # Strike costs 1
    assert result.events[0].WhichOneof("kind") == "card_played"


def test_play_unknown_card_is_rejected(stub):
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    with pytest.raises(grpc.RpcError) as err:
        stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=99))
    assert err.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_wrong_session_is_rejected(stub):
    stub.StartRun(pb.StartRunRequest(seed=1))
    with pytest.raises(grpc.RpcError) as err:
        stub.EndTurn(pb.EndTurnRequest(session_id="wrong"))
    assert err.value.code() == grpc.StatusCode.NOT_FOUND


def test_end_turn_next_round(stub):
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=0))
    result = stub.EndTurn(pb.EndTurnRequest(session_id=run.session_id))
    assert result.state.round == 2
    assert len(result.state.row) == 0
    assert result.events[0].damage.amount == 5


def kinds(result):
    return [e.WhichOneof("kind") for e in result.events]


def actor(event):
    """True = player, False = automaton, None = no side in the event."""
    kind = event.WhichOneof("kind")
    if kind == "card_played":
        return event.card_played.by_player
    if kind == "damage":
        return not event.damage.to_player       # to_player=True means the AUTOMATON attacked
    if kind in ("shield_changed", "cards_drawn", "cards_discarded", "energy_changed"):
        return getattr(event, kind).player
    return None


def test_play_card_event_order(stub):
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    first = stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=0))
    assert kinds(first) == ["card_played", "energy_changed"]

    second = stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=1, connect=True))
    assert kinds(second) == ["card_played", "tab_activated", "energy_changed"]


def test_card_played_comes_before_events_that_refer_to_its_uid(stub):
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    events = list(stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=0)).events)
    events += list(stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=1, connect=True)).events)
    events += list(stub.EndTurn(pb.EndTurnRequest(session_id=run.session_id)).events)

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
    run = stub.StartRun(pb.StartRunRequest(seed=1))
    stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=0))
    result = stub.EndTurn(pb.EndTurnRequest(session_id=run.session_id))

    collapsed = []
    for e in result.events:
        a = actor(e)
        if a is not None and (not collapsed or collapsed[-1] != a):
            collapsed.append(a)
    # player attack -> automaton turn -> start of the player's new turn
    assert collapsed == [True, False, True]


def test_battle_ended_is_the_last_event():
    server, port = create_server("127.0.0.1:0", Game(enemy_hp=5))   # one Strike (5 damage) wins
    server.start()
    channel = grpc.insecure_channel(f"127.0.0.1:{port}")
    stub = rpc.GameStub(channel)
    try:
        run = stub.StartRun(pb.StartRunRequest(seed=1))
        stub.PlayCard(pb.PlayCardRequest(session_id=run.session_id, card_uid=0))
        result = stub.EndTurn(pb.EndTurnRequest(session_id=run.session_id))

        assert kinds(result) == ["damage", "battle_ended"]
        assert result.events[-1].battle_ended.result == pb.BATTLE_RESULT_WON
        assert result.state.result == pb.BATTLE_RESULT_WON

        with pytest.raises(grpc.RpcError) as err:                    # nothing is allowed after the end
            stub.EndTurn(pb.EndTurnRequest(session_id=run.session_id))
        assert err.value.code() == grpc.StatusCode.FAILED_PRECONDITION
    finally:
        channel.close()
        server.stop(0)