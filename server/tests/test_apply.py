import pytest

from salon.automata.interface import EndTurn, PlayCard
from salon.cards import CardDef, CardInstance, Color, Tab
from salon.engine.apply import apply
from salon.engine.battle import create_battle
from salon.engine.events import CardPlayed, CardsDiscarded, EnergyChanged, TabActivated
from salon.engine.rules import legal_actions
from salon.engine.state import BattleResult, GameCard, RowCard

CIOS = CardDef("cios", "Cios", (Color.RED,), 1, 5, 0, 0, "starter")
BLOK = CardDef("blok", "Blok", (Color.GREEN,), 1, 0, 5, 0, "starter")
FREE_BLOK = CardDef("free_blok", "Free Blok", (Color.GREEN,), 0, 0, 3, 0, "starter")
DUAL = CardDef("dual", "Dual", (Color.RED, Color.GREEN), 1, 3, 3, 0, "common")


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


def card(uid, card_def, tabs=()):
    return GameCard(uid, CardInstance(card_def, tuple(tabs)))


def battle(hand, row=(), energy=3):
    """Battle with a hand-set state instead of a random starting hand."""
    s = create_battle(1, deck(), deck())
    s.player.hand = list(hand)
    s.row = [RowCard(c) for c in row]
    s.player.energy = energy
    return s


def connects(actions):
    return [a for a in actions if isinstance(a, PlayCard) and a.connect]


# legal_actions

def test_end_turn_is_always_legal():
    s = battle(hand=[card(100, CIOS)], row=[card(101, CIOS, [Tab(Color.RED, 1)])], energy=0)
    assert EndTurn() in legal_actions(s)
    s = battle(hand=[], energy=3)
    assert EndTurn() in legal_actions(s)


def test_card_too_expensive_is_not_legal():
    s = battle(hand=[card(100, CIOS), card(101, BLOK)], energy=0)
    assert legal_actions(s) == [EndTurn()]


def test_connect_offered_when_tab_matches():
    blok = card(101, BLOK)
    s = battle(hand=[blok], row=[card(100, CIOS, [Tab(Color.GREEN, 2)])])
    actions = legal_actions(s)
    assert PlayCard(card_uid=blok.uid, connect=False) in actions
    assert PlayCard(card_uid=blok.uid, connect=True) in actions


@pytest.mark.parametrize("row", [
    [],                                         # empty row
    [card(100, CIOS)],                          # previous card has no tabs
    [card(100, CIOS, [Tab(Color.BLUE, 2)])],    # tab in another color
])
def test_no_connect_without_matching_tab(row):
    s = battle(hand=[card(101, BLOK)], row=row)
    assert connects(legal_actions(s)) == []


def test_connect_legal_with_one_energy_less():
    blok = card(101, BLOK)
    s = battle(hand=[blok], row=[card(100, CIOS, [Tab(Color.GREEN, 2)])], energy=0)
    actions = legal_actions(s)
    assert PlayCard(card_uid=blok.uid, connect=True) in actions
    assert PlayCard(card_uid=blok.uid, connect=False) not in actions


def two_tab_battle():
    dual = card(101, DUAL)
    previous = card(100, CIOS, [Tab(Color.RED, 1), Tab(Color.GREEN, 2)])
    return battle(hand=[dual], row=[previous]), dual


def test_two_color_card_chooses_tab():
    s, dual = two_tab_battle()
    connected = connects(legal_actions(s))
    assert {a.tab_color for a in connected} == {Color.RED, Color.GREEN}
    assert len(connected) == 2
    assert all(a.card_uid == dual.uid for a in connected)
    assert all(a.tab_color is not None for a in connected)


def test_no_actions_after_battle_ended():
    s = battle(hand=[card(100, CIOS)])
    s.result = BattleResult.WON
    assert legal_actions(s) == []


# apply

def test_connected_card_costs_less_and_activates_tab():
    cios = card(100, CIOS, [Tab(Color.GREEN, 2)])
    blok = card(101, BLOK)
    s = battle(hand=[blok], row=[cios], energy=2)
    new, events = apply(s, PlayCard(card_uid=blok.uid, connect=True))
    assert new.player.energy == 2
    assert [type(e) for e in events] == [CardPlayed, TabActivated, EnergyChanged]
    activated = events[1]
    assert activated.card_uid == cios.uid
    assert activated.tab == Tab(Color.GREEN, 2)
    last = new.row[-1]
    assert last.card.uid == blok.uid
    assert last.connected is True
    assert last.tab == Tab(Color.GREEN, 2)


def test_connected_cost_never_below_zero():
    free = card(101, FREE_BLOK)
    s = battle(hand=[free], row=[card(100, CIOS, [Tab(Color.GREEN, 2)])], energy=2)
    new, _ = apply(s, PlayCard(card_uid=free.uid, connect=True))
    assert new.player.energy == 2


def test_apply_uses_chosen_tab_color():
    s, dual = two_tab_battle()
    _, events = apply(s, PlayCard(card_uid=dual.uid, connect=True, tab_color=Color.GREEN))
    activated = [e for e in events if isinstance(e, TabActivated)]
    assert len(activated) == 1
    assert activated[0].tab == Tab(Color.GREEN, 2)


def test_end_turn_events_and_round():
    cios = card(100, CIOS)
    s = battle(hand=[cios], energy=3)
    s, _ = apply(s, PlayCard(card_uid=cios.uid, connect=False))
    s, events = apply(s, EndTurn())
    discarded = [e for e in events if isinstance(e, CardsDiscarded)]
    assert len(discarded) == 1
    assert discarded[0].card_uids == (cios.uid,)

    s, events = apply(s, EndTurn())  # enemy ends the turn with an empty row
    assert not any(isinstance(e, CardsDiscarded) for e in events)
    assert s.round == 2
    assert s.player_turn is True


def test_illegal_connect_is_rejected():
    blok = card(101, BLOK)
    s = battle(hand=[blok], row=[card(100, CIOS, [Tab(Color.RED, 2)])])
    with pytest.raises(ValueError):
        apply(s, PlayCard(card_uid=blok.uid, connect=True))
