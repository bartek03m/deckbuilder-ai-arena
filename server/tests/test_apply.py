import pytest

from salon.automata.interface import EndTurn, PlayCard
from salon.cards import CardDef, CardInstance, Color, Tab
from salon.engine.apply import apply
from salon.engine.battle import create_battle
from salon.engine.events import CardPlayed, EnergyChanged

CIOS = CardDef("cios", "Cios", (Color.RED,), 1, 5, 0, 0, "starter")


def deck():
    return [CardInstance(CIOS, (Tab(Color.GREEN, 2),)) for _ in range(10)]


def test_play_card_moves_card_and_spends_energy():
    s = create_battle(1, deck(), deck())
    uid = s.player.hand[0].uid
    new, events = apply(s, PlayCard(card_uid=uid, connect=False))
    assert uid not in [c.uid for c in new.player.hand]
    assert [e.card.uid for e in new.row] == [uid]
    assert new.player.energy == s.player.energy - 1
    assert [type(e) for e in events] == [CardPlayed, EnergyChanged]


def test_illegal_action_is_rejected():
    s = create_battle(1, deck(), deck())
    with pytest.raises(ValueError):
        apply(s, PlayCard(card_uid=9999, connect=False))


def test_apply_does_not_change_the_given_state():
    s = create_battle(1, deck(), deck())
    uid = s.player.hand[0].uid
    apply(s, PlayCard(card_uid=uid, connect=False))
    assert s.row == [] and len(s.player.hand) == 5


def test_end_turn_switches_side_and_discards_row():
    s = create_battle(1, deck(), deck())
    s, _ = apply(s, PlayCard(card_uid=s.player.hand[0].uid, connect=False))
    new, events = apply(s, EndTurn())
    assert new.player_turn is False
    assert new.row == [] and len(new.player.discard) == 1