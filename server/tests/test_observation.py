import random

from hypothesis import given
from hypothesis import strategies as st

from salon.automata.interface import EndTurn, PlayCard
from salon.cards import CardDef, CardInstance, Color, Tab
from salon.engine.apply import apply
from salon.engine.battle import create_battle
from salon.engine.observation import observe
from salon.engine.rules import legal_actions

STRIKE = CardDef("strike", "Strike", (Color.RED,), 1, 5, 0, 0, "starter")
HEAVY = CardDef("heavy_strike", "Heavy Strike", (Color.RED,), 2, 9, 0, 0, "common")
BLOCK = CardDef("block", "Block", (Color.GREEN,), 1, 0, 4, 0, "starter")
SPARK = CardDef("spark", "Spark", (Color.RED, Color.BLUE), 1, 3, 0, 1, "common")
JOKER = CardDef("joker", "Joker", (Color.PURPLE,), 2, 4, 4, 1, "rare")


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
        for view, side in ((obs.me, me), (obs.opponent, opp)):
            assert view.hp == side.hp
            assert view.max_hp == side.max_hp
            assert view.shield == side.shield
            assert view.energy == side.energy
            assert view.deck_count == side.deck_count
            assert view.discard_count == side.discard_count
        assert uids(obs.hand) == uids(me.hand)
        assert obs.round == s.round


def test_opponent_hand_shows_only_colors():
    s = battle()
    assert observe(s, True).opponent_hand == tuple(c.instance.card.colors for c in s.enemy.hand)
    assert observe(s, False).opponent_hand == tuple(c.instance.card.colors for c in s.player.hand)


def test_card_backs_of_two_color_card_and_joker():
    """A two-color card shows both colors, the Joker shows purple."""
    joker = CardInstance(JOKER, (Tab(Color.RAINBOW, 3),))
    spark = CardInstance(SPARK, (Tab(Color.GREEN, 2),))
    enemy_deck = [joker, spark] + [CardInstance(STRIKE, ()) for _ in range(3)]  # 5 cards, all in the start hand
    s = create_battle(1, mixed_deck(), enemy_deck)
    backs = observe(s, True).opponent_hand
    assert sorted(backs) == sorted([(Color.PURPLE,), (Color.RED, Color.BLUE)] + [(Color.RED,)] * 3)


def test_deck_lists_have_all_cards():
    s = battle()
    player_uids = sorted(uids(s.player.deck + s.player.hand))
    enemy_uids = sorted(uids(s.enemy.deck + s.enemy.hand))
    assert len(player_uids) == len(enemy_uids) == 10
    enemy_mid_turn, _ = apply(s, EndTurn())
    for state in (s, mid_turn(s), mid_turn(enemy_mid_turn)):  # the last two have a card in the row
        p = observe(state, True)
        e = observe(state, False)
        assert uids(p.deck_list) == uids(e.opponent_deck_list) == player_uids
        assert uids(e.deck_list) == uids(p.opponent_deck_list) == enemy_uids


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
    player_turn = mid_turn(battle())
    enemy_turn = mid_turn(apply(battle(), EndTurn())[0])
    for s, for_player in ((player_turn, True), (enemy_turn, False)):
        row_uids = [rc.card.uid for rc in s.row]
        assert len(row_uids) == 1
        assert uids(observe(s, for_player).row) == row_uids
        assert observe(s, not for_player).row == ()


def test_opponent_played_cards_are_in_discard_on_my_turn():
    """After ATTACK! the played row goes to the discard pile, so the next side sees it there."""
    s = battle()
    for _ in range(2):  # player turn, then enemy turn
        s = mid_turn(s)
        played = {rc.card.uid for rc in s.row}
        mover = s.player_turn
        s, _ = apply(s, EndTurn())
        obs = observe(s, not mover)  # the side whose turn it is now
        assert obs.row == ()
        assert played <= set(uids(obs.opponent_discard))


def test_observation_is_symmetric():
    s2 = mid_turn(battle())
    p = observe(s2, True)
    e = observe(s2, False)
    assert p.deck_list == e.opponent_deck_list
    assert p.opponent_deck_list == e.deck_list
    assert p.discard == e.opponent_discard
    assert p.opponent_discard == e.discard


def test_lists_belong_to_the_right_side():
    s = battle()
    for _ in range(2):  # one full round, so both discard piles are not empty
        s, _ = apply(mid_turn(s), EndTurn())
    assert s.player.discard and s.enemy.discard
    for for_player, me, opp in ((True, s.player, s.enemy), (False, s.enemy, s.player)):
        obs = observe(s, for_player)
        assert uids(obs.deck_list) == sorted(uids(me.deck + me.hand + me.discard))
        assert uids(obs.opponent_deck_list) == sorted(uids(opp.deck + opp.hand + opp.discard))
        assert uids(obs.discard) == sorted(uids(me.discard))
        assert uids(obs.opponent_discard) == sorted(uids(opp.discard))


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
