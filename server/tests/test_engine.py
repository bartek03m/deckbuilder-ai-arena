import copy

from hypothesis import given, strategies as st

from salon.cards import CardDef, CardInstance, Color, Tab
from salon.engine.battle import MAX_HAND, START_HAND, draw_cards, new_battle

CIOS = CardDef("cios", "Cios", (Color.RED,), 1, 5, 0, 0, "starter")
BLOK = CardDef("blok", "Blok", (Color.GREEN,), 1, 0, 4, 0, "starter")
NAMYSL = CardDef("namysl", "Namysl", (Color.BLUE,), 1, 0, 0, 2, "starter")


def starter_deck():
    return (
        [CardInstance(CIOS, (Tab(Color.GREEN, 2),))]
        + [CardInstance(CIOS, ()) for _ in range(3)]
        + [CardInstance(BLOK, (Tab(Color.RED, 2),))]
        + [CardInstance(BLOK, ()) for _ in range(3)]
        + [CardInstance(NAMYSL, (Tab(Color.RED, 1),)), CardInstance(NAMYSL, ())]
    )


def uids(cards):
    return [c.uid for c in cards]


def snapshot(state):
    """Comparable summary of a state (Random objects cannot be compared)."""
    return (
        uids(state.player.deck), uids(state.player.hand), uids(state.player.discard),
        uids(state.enemy.deck), uids(state.enemy.hand), uids(state.enemy.discard),
    )


def battle(seed):
    return new_battle(seed, starter_deck(), starter_deck())


def test_new_battle_start_values():
    s = battle(1)
    assert len(s.player.hand) == START_HAND
    assert len(s.enemy.hand) == START_HAND
    assert s.player.deck_count == 5
    assert s.player.hp == 50 and s.round == 1


def test_same_seed_same_battle():
    assert snapshot(battle(7)) == snapshot(battle(7))


def test_different_seed_different_battle():
    assert snapshot(battle(1)) != snapshot(battle(2))


@given(st.integers(min_value=0, max_value=2**32))
def test_same_seed_same_battle_for_any_seed(seed):
    assert snapshot(battle(seed)) == snapshot(battle(seed))


def test_uids_are_unique_across_both_sides():
    s = battle(3)
    every = s.player.deck + s.player.hand + s.enemy.deck + s.enemy.hand
    assert len(set(uids(every))) == 20


def test_cards_are_never_lost():
    s = battle(4)
    draw_cards(s, s.player, 3)
    s.player.discard.append(s.player.hand.pop())
    side = s.player
    assert len(side.deck) + len(side.hand) + len(side.discard) == 10


def test_hand_is_capped():
    s = battle(5)
    draw_cards(s, s.player, 100)
    assert len(s.player.hand) == MAX_HAND
    assert s.player.deck_count == 3          # the rest stayed in the deck


def test_empty_deck_reshuffles_discard_deterministically():
    def run(seed):
        s = battle(seed)
        side = s.player
        side.discard, side.hand = side.hand, []   # whole hand to discard
        side.discard += side.deck
        side.deck = []
        draw_cards(s, side, 4)
        return uids(side.hand), side.deck_count

    assert run(9) == run(9)
    hand, left = run(9)
    assert len(hand) == 4 and left == 6


def test_deepcopy_behaves_the_same_and_is_independent():
    original = battle(11)
    clone = copy.deepcopy(original)
    draw_cards(original, original.player, 1)     # hand 5 -> 6 (limit is 7)
    draw_cards(clone, clone.player, 1)
    assert snapshot(original) == snapshot(clone)

    draw_cards(clone, clone.player, 1)           # change only the clone
    assert snapshot(original) != snapshot(clone)