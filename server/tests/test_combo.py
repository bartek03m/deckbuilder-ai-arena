import pytest
import random
from hypothesis import given, strategies as st
from salon.engine.events import CardsDrawn, TabActivated
from salon.automata.interface import EndTurn, PlayCard
from salon.cards import CardDef, CardInstance, Color, Tab
from salon.engine.apply import apply
from salon.engine.battle import create_battle
from salon.engine.rules import legal_actions
from salon.engine.state import GameCard, RowCard

CIOS = CardDef("cios", "Cios", (Color.RED,), 1, 5, 0, 0, "starter")
BLOK = CardDef("blok", "Blok", (Color.GREEN,), 1, 0, 4, 0, "starter")
NAMYSL = CardDef("namysl", "Namysl", (Color.BLUE,), 1, 0, 0, 2, "starter")
CIEZKI_CIOS = CardDef("ciezki_cios", "Ciezki cios", (Color.RED,), 2, 9, 0, 0, "common")
DUAL = CardDef("dual", "Dual", (Color.RED, Color.GREEN), 1, 3, 3, 0, "common")


def deck():
    return [CardInstance(CIOS, ()) for _ in range(10)]


def card(uid, card_def, tabs=()):
    return GameCard(uid, CardInstance(card_def, tuple(tabs)))


def battle(hand, row=(), energy=3):
    """Battle with a hand-set state instead of a random starting hand."""
    s = create_battle(1, deck(), deck())
    s.player.hand = list(hand)
    s.row = [RowCard(c) for c in row]
    s.player.energy = energy
    return s

def test_zero_value_tab_gives_discount_but_no_bonus():
    blok = card(101, BLOK)
    s = battle(hand=[blok], row=[card(100, CIOS, [Tab(Color.GREEN, 0)])], energy=3)

    s, _ = apply(s, PlayCard(card_uid=blok.uid, connect=True))
    assert s.player.energy == 3 # connected cost 1 - 1 = 0

    s, _ = apply(s, EndTurn())
    assert s.player.shield == 4 # only blok card own shield is added (tab adds 0)

def test_declining_connection_costs_full_and_gives_no_bonus():
    blok = card(101, BLOK)
    s = battle(hand=[blok], row=[card(100, CIOS, [Tab(Color.GREEN, 2)])], energy=3)

    s, _ = apply(s, PlayCard(card_uid=blok.uid, connect=False))
    assert s.player.energy == 2 # cost without connection 3 - 1 = 2

    s, _ = apply(s, EndTurn())
    assert s.player.shield == 4 # only blok own shield, tab not activated

def test_two_tabs_matching_but_only_chosen_counts():
    dual = card(101, DUAL)
    s = battle(hand=[dual], row=[card(100, NAMYSL, [Tab(Color.GREEN, 2), Tab(Color.RED, 3)])], energy=3)

    s, _ = apply(s, PlayCard(card_uid=dual.uid, connect=True, tab_color=Color.GREEN))
    assert s.player.energy == 3

    s, _ = apply(s, EndTurn())
    assert s.player.shield == 5 # dual 3 + chosen green tab 2 = 5
    assert s.enemy.hp == 27 # only dual 3 damage, red tab 3 damage is lost

def test_last_card_tabs_lost():
    cios = card(101, CIOS, [Tab(Color.RED, 2)])
    s = battle(hand=[cios], energy=3)

    s, _ = apply(s, PlayCard(card_uid=cios.uid, connect=False))
    assert s.player.energy == 2

    s, _ = apply(s, EndTurn())
    assert s.enemy.hp == 25 # only 5 damage, red tab 2 damage is lost
    assert s.row == [] # row doesn't carry over
    assert not any(isinstance(a, PlayCard) and a.connect for a in legal_actions(s))

def test_two_chains_in_one_row_both_give_bonuses():
    cios = card(101, CIOS, [Tab(Color.GREEN, 2)])
    blok = card(102, BLOK)
    namysl = card(103, NAMYSL, [Tab(Color.RED, 3)])
    cios_no_tabs = card(104, CIOS)
    s = battle(hand=[cios, blok, namysl, cios_no_tabs])

    s, _ = apply(s, PlayCard(card_uid=cios.uid, connect=False))
    assert s.player.energy == 2

    s, _ = apply(s, PlayCard(card_uid=blok.uid, connect=True))
    assert s.player.energy == 2

    s, _ = apply(s, PlayCard(card_uid=namysl.uid, connect=False))
    assert s.player.energy == 1

    s, _ = apply(s, PlayCard(card_uid=cios_no_tabs.uid, connect=True))
    assert s.player.energy == 1

    s, _ = apply(s, EndTurn())
    assert s.enemy.hp == 17 # 5 + 5 both cios + 3 tab chain 2
    assert s.player.shield == 6 # 4 shield blok + 2 tab chain 1
    

def example_hand():
    return {
        "cios": card(101, CIOS, [Tab(Color.GREEN, 3)]),
        "blok": card(102, BLOK, [Tab(Color.RED, 3)]),
        "ciezki_cios": card(103, CIEZKI_CIOS),
        "namysl": card(104, NAMYSL, [Tab(Color.RED, 2)]),
    }

@pytest.mark.parametrize("plays, damage, shield, drawn, energy_left", [
    ([("ciezki_cios", False), ("cios", False)], 14, 0, 3, 0),
    ([("cios", False), ("blok", True), ("ciezki_cios", True), ("namysl",False)], 17, 7, 5, 0),
    ([("namysl", False), ("cios", True), ("blok", True), ("ciezki_cios", True)], 19, 7, 5, 1)
])

def test_rules_example_order_changes_result(plays, damage, shield, drawn, energy_left):
    cards = example_hand()
    s = battle(hand=list(cards.values()))

    for name, connect in plays:
        s, _ = apply(s, PlayCard(card_uid=cards[name].uid, connect=connect))
    assert s.player.energy == energy_left

    s, events = apply(s, EndTurn())
    assert s.enemy.hp == 30 - damage
    assert s.player.shield == shield
    assert CardsDrawn(player=True, count=drawn) in events


TAB_COLORS = [Color.RED, Color.GREEN, Color.BLUE]
CARD_DEFS = [CIOS, BLOK, NAMYSL, CIEZKI_CIOS, DUAL]

@st.composite
def random_card(draw, uid):
    """Random card definition with 0-2 random tabs."""
    card_def = draw(st.sampled_from(CARD_DEFS))
    colors = draw(st.lists(st.sampled_from(TAB_COLORS), max_size=2, unique=True))
    tabs = [Tab(color, draw(st.integers(0, 3))) for color in colors]
    return card(uid, card_def, tabs)


@st.composite
def random_hand(draw):
    size = draw(st.integers(1, 5))
    return [draw(random_card(100 + i)) for i in range(size)]


@given(hand=random_hand(), seed=st.integers(0, 10_000))
def test_resolution_matches_played_cards_and_activated_tabs(hand, seed):
    rng = random.Random(seed)
    s = battle(hand=hand)
    s.enemy.hp = 1000 # battle can't end during the test
    damage = shield = 0

    while True:
        plays = [a for a in legal_actions(s) if isinstance(a, PlayCard)]
        if not plays:
            break
        action = rng.choice(plays)
        played = next(c for c in s.player.hand if c.uid == action.card_uid).instance.card
        energy_before = s.player.energy

        s, events = apply(s, action)

        activated = [e.tab for e in events if isinstance(e, TabActivated)]
        assert len(activated) == (1 if action.connect else 0)
        expected_cost = max(0, played.cost - 1) if action.connect else played.cost
        assert energy_before - s.player.energy == expected_cost

        damage += played.damage
        shield += played.shield
        for tab in activated:
            assert tab.color in played.colors
            if tab.color == Color.RED:
                damage += tab.value
            if tab.color == Color.GREEN:
                shield += tab.value

    s, _ = apply(s, EndTurn())
    assert s.enemy.hp == 1000 - damage
    assert s.player.shield == shield