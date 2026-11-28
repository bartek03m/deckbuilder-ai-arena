import re

import pytest
from hypothesis import given, settings, strategies as st

from salon_proto import game_pb2 as pb

from salon.automata.cog import Cog
from salon.cards import Color, Tab, load_deck
from salon.engine.apply import apply
from salon.engine.battle import create_battle
from salon.engine.events import BattleEnded, TabActivated
from salon.engine.observation import observe
from salon.engine.rules import legal_actions
from salon.engine.state import BattleResult
from salon.grpc_server import convert

MAX_STEPS = 1000


def _battle(seed=1):
    deck = load_deck("starter")
    return create_battle(seed, deck, deck)


def _snake(name):
    """CardPlayed -> card_played (the oneof field name in proto)."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


@pytest.mark.parametrize("color", list(Color))
def test_color_round_trip(color):
    assert convert.color_from_proto(convert.color_to_proto(color)) == color


def test_unspecified_color_is_none():
    assert convert.color_from_proto(pb.COLOR_UNSPECIFIED) is None


def test_unknown_color_is_rejected():
    with pytest.raises(ValueError):
        convert.color_from_proto(99)


def test_card_keeps_all_fields():
    card = _battle().player.hand[0]
    d = card.instance.card
    msg = convert.card_to_proto(card)
    assert msg.uid == card.uid
    assert msg.def_id == d.id
    assert msg.name == d.name
    assert list(msg.colors) == [convert.color_to_proto(c) for c in d.colors]
    assert (msg.cost, msg.damage, msg.shield, msg.draw) == (d.cost, d.damage, d.shield, d.draw)
    assert len(msg.tabs) == len(card.instance.tabs)


def test_start_state():
    state = _battle()
    msg = convert.state_to_proto(state)
    assert [c.uid for c in msg.hand] == [c.uid for c in state.player.hand]
    assert len(msg.enemy_hand) == len(state.enemy.hand)
    assert msg.player.hp == state.player.hp
    assert msg.player.energy == state.player.energy
    assert msg.player.deck_count == state.player.deck_count
    assert msg.enemy.hp == state.enemy.hp
    assert msg.round == 1
    assert msg.result == pb.BATTLE_RESULT_ONGOING
    assert len(msg.row) == 0


def test_enemy_hand_shows_only_colors():
    state = _battle()
    msg = convert.state_to_proto(state)
    for back, card in zip(msg.enemy_hand, state.enemy.hand):
        assert list(back.colors) == [convert.color_to_proto(c) for c in card.instance.card.colors]


def test_tab_activated_event():
    msg = convert.event_to_proto(TabActivated(card_uid=3, tab=Tab(Color.GREEN, 2)))
    assert msg.tab_activated.card_uid == 3
    assert msg.tab_activated.tab.color == pb.COLOR_GREEN
    assert msg.tab_activated.tab.value == 2


def test_battle_ended_event():
    msg = convert.event_to_proto(BattleEnded(BattleResult.LOST))
    assert msg.battle_ended.result == pb.BATTLE_RESULT_LOST


def test_unknown_event_is_rejected():
    with pytest.raises(TypeError):
        convert.event_to_proto("not an event")


@given(st.integers())
@settings(max_examples=20, deadline=None)
def test_every_event_of_a_real_battle_converts(seed):
    state = _battle(seed)
    player, enemy = Cog(seed), Cog(seed + 11)
    for _ in range(MAX_STEPS):
        if state.result != BattleResult.ONGOING:
            break
        bot = player if state.player_turn else enemy
        action = bot.choose_action(observe(state, state.player_turn), legal_actions(state))
        state, events = apply(state, action)
        for event, msg in zip(events, convert.events_to_proto(events)):
            assert msg.WhichOneof("kind") == _snake(type(event).__name__)
        convert.state_to_proto(state)