import random

from hypothesis import given
from hypothesis import strategies as st

from salon.automata.interface import EndTurn, PlayCard
from salon.cards import CardDef, CardInstance, Color
from salon.engine.apply import apply
from salon.engine.battle import create_battle
from salon.engine.observation import observe
from salon.engine.rules import legal_actions

STRIKE = CardDef("strike", "Strike", (Color.RED,), 1, 5, 0, 0, "starter")
HEAVY = CardDef("heavy_strike", "Heavy Strike", (Color.RED,), 2, 9, 0, 0, "common")
BLOCK = CardDef("block", "Block", (Color.GREEN,), 1, 0, 4, 0, "starter")


def mixed_deck():
    return [CardInstance(STRIKE, ()) for _ in range(5)] + [CardInstance(BLOCK, ()) for _ in range(5)]


def red_deck():
    """Only red cards, but of two different kinds."""
    return [CardInstance(STRIKE, ()) for _ in range(5)] + [CardInstance(HEAVY, ()) for _ in range(5)]


def battle(seed=1):
    return create_battle(seed, mixed_deck(), mixed_deck())


def mid_turn(s):
    """Play the first legal card, so one card lies in the row."""
    play = next(a for a in legal_actions(s) if isinstance(a, PlayCard))
    new, _ = apply(s, play)
    return new


def uids(cards):
    return [c.uid for c in cards]


def test_fields_match_state():
    s = battle()
    for for_player, me, opp in ((True, s.player, s.enemy), (False, s.enemy, s.player)):
        obs = observe(s, for_player)
        assert obs.me.hp == me.hp
        assert obs.opponent.hp == opp.hp
        assert obs.me.deck_count == me.deck_count
        assert obs.opponent.deck_count == opp.deck_count
        assert uids(obs.hand) == uids(me.hand)
        assert obs.round == s.round


def test_opponent_hand_shows_only_colors():
    s = battle()
    assert observe(s, True).opponent_hand == tuple(c.instance.card.colors for c in s.enemy.hand)
    assert observe(s, False).opponent_hand == tuple(c.instance.card.colors for c in s.player.hand)


def test_deck_lists_have_all_cards():
    s = battle()
    enemy_mid_turn, _ = apply(s, EndTurn())
    for state in (s, mid_turn(s), mid_turn(enemy_mid_turn)):
        for for_player in (True, False):
            obs = observe(state, for_player)
            assert len(obs.deck_list) == 10
            assert len(obs.opponent_deck_list) == 10


@given(st.integers(min_value=0, max_value=10_000))
def test_deck_list_never_changes(seed):
    rng = random.Random(seed)
    s = create_battle(seed, mixed_deck(), mixed_deck())
    player_start = observe(s, True).deck_list
    enemy_start = observe(s, False).deck_list
    for _ in range(300):
        actions = legal_actions(s)
        if not actions:
            break
        s, _ = apply(s, rng.choice(actions))
        assert observe(s, True).deck_list == player_start
        assert observe(s, False).deck_list == enemy_start


def test_shuffling_deck_does_not_change_observation():
    s = battle()
    before = observe(s, True)
    random.Random(1).shuffle(s.enemy.deck)
    random.Random(2).shuffle(s.player.deck)
    assert observe(s, True) == before


def test_swapping_same_color_cards_does_not_change_observation():
    s = create_battle(1, red_deck(), red_deck())
    before_player = observe(s, True)
    before_enemy = observe(s, False)
    hand, deck = s.enemy.hand, s.enemy.deck
    i, j = next(
        (i, j) for i, h in enumerate(hand) for j, d in enumerate(deck) if h.instance.card.id != d.instance.card.id
    )
    hand[i], deck[j] = deck[j], hand[i]
    assert observe(s, True) == before_player
    assert observe(s, False).hand != before_enemy.hand  # the swap really changed the enemy hand


def test_side_without_turn_sees_empty_row():
    s2 = mid_turn(battle())
    assert observe(s2, False).row == ()
    assert len(observe(s2, True).row) == 1


def test_observation_is_symmetric():
    s2 = mid_turn(battle())
    p = observe(s2, True)
    e = observe(s2, False)
    assert p.deck_list == e.opponent_deck_list
    assert p.opponent_deck_list == e.deck_list
    assert p.discard == e.opponent_discard
    assert p.opponent_discard == e.discard


def snapshot(s):
    return (
        uids(s.player.deck),
        uids(s.player.hand),
        uids(s.player.discard),
        uids(s.enemy.deck),
        uids(s.enemy.hand),
        uids(s.enemy.discard),
        [rc.card.uid for rc in s.row],
    )


def test_observe_does_not_change_state():
    s = mid_turn(battle())
    before = snapshot(s)
    observe(s, True)
    observe(s, False)
    assert snapshot(s) == before
