import pytest
import random
from hypothesis import given, strategies as st
from salon.engine.events import BattleEnded, CardsDrawn, Damage, ShieldChanged
from salon.automata.interface import EndTurn, PlayCard
from salon.cards import CardDef, CardInstance, Color, Tab
from salon.engine.apply import apply
from salon.engine.battle import create_battle
from salon.engine.events import CardPlayed, CardsDiscarded, EnergyChanged, TabActivated
from salon.engine.rules import legal_actions
from salon.engine.state import BattleResult, GameCard, RowCard

STRIKE = CardDef("strike", "Strike", (Color.RED,), 1, 5, 0, 0, "starter")
BLOCK = CardDef("block", "Block", (Color.GREEN,), 1, 0, 5, 0, "starter")
FREE_BLOCK = CardDef("free_block", "Free Block", (Color.GREEN,), 0, 0, 3, 0, "starter")
DUAL = CardDef("dual", "Dual", (Color.RED, Color.GREEN), 1, 3, 3, 0, "common")


def deck():
    return [CardInstance(STRIKE, (Tab(Color.GREEN, 2),)) for _ in range(10)]


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
    s = battle(hand=[card(100, STRIKE)], row=[card(101, STRIKE, [Tab(Color.RED, 1)])], energy=0)
    assert EndTurn() in legal_actions(s)
    s = battle(hand=[], energy=3)
    assert EndTurn() in legal_actions(s)


def test_card_too_expensive_is_not_legal():
    s = battle(hand=[card(100, STRIKE), card(101, BLOCK)], energy=0)
    assert legal_actions(s) == [EndTurn()]


def test_connect_offered_when_tab_matches():
    block = card(101, BLOCK)
    s = battle(hand=[block], row=[card(100, STRIKE, [Tab(Color.GREEN, 2)])])
    actions = legal_actions(s)
    assert PlayCard(card_uid=block.uid, connect=False) in actions
    assert PlayCard(card_uid=block.uid, connect=True) in actions


@pytest.mark.parametrize("row", [
    [],                                         # empty row
    [card(100, STRIKE)],                          # previous card has no tabs
    [card(100, STRIKE, [Tab(Color.BLUE, 2)])],    # tab in another color
])
def test_no_connect_without_matching_tab(row):
    s = battle(hand=[card(101, BLOCK)], row=row)
    assert connects(legal_actions(s)) == []


def test_connect_legal_with_one_energy_less():
    block = card(101, BLOCK)
    s = battle(hand=[block], row=[card(100, STRIKE, [Tab(Color.GREEN, 2)])], energy=0)
    actions = legal_actions(s)
    assert PlayCard(card_uid=block.uid, connect=True) in actions
    assert PlayCard(card_uid=block.uid, connect=False) not in actions


def two_tab_battle():
    dual = card(101, DUAL)
    previous = card(100, STRIKE, [Tab(Color.RED, 1), Tab(Color.GREEN, 2)])
    return battle(hand=[dual], row=[previous]), dual


def test_two_color_card_chooses_tab():
    s, dual = two_tab_battle()
    connected = connects(legal_actions(s))
    assert {a.tab_color for a in connected} == {Color.RED, Color.GREEN}
    assert len(connected) == 2
    assert all(a.card_uid == dual.uid for a in connected)
    assert all(a.tab_color is not None for a in connected)


def test_no_actions_after_battle_ended():
    s = battle(hand=[card(100, STRIKE)])
    s.result = BattleResult.WON
    assert legal_actions(s) == []


# apply

def test_connected_card_costs_less_and_activates_tab():
    strike = card(100, STRIKE, [Tab(Color.GREEN, 2)])
    block = card(101, BLOCK)
    s = battle(hand=[block], row=[strike], energy=2)
    new, events = apply(s, PlayCard(card_uid=block.uid, connect=True))
    assert new.player.energy == 2
    assert [type(e) for e in events] == [CardPlayed, TabActivated, EnergyChanged]
    activated = events[1]
    assert activated.card_uid == strike.uid
    assert activated.tab == Tab(Color.GREEN, 2)
    last = new.row[-1]
    assert last.card.uid == block.uid
    assert last.connected is True
    assert last.tab == Tab(Color.GREEN, 2)


def test_connected_cost_never_below_zero():
    free = card(101, FREE_BLOCK)
    s = battle(hand=[free], row=[card(100, STRIKE, [Tab(Color.GREEN, 2)])], energy=2)
    new, _ = apply(s, PlayCard(card_uid=free.uid, connect=True))
    assert new.player.energy == 2


def test_apply_uses_chosen_tab_color():
    s, dual = two_tab_battle()
    _, events = apply(s, PlayCard(card_uid=dual.uid, connect=True, tab_color=Color.GREEN))
    activated = [e for e in events if isinstance(e, TabActivated)]
    assert len(activated) == 1
    assert activated[0].tab == Tab(Color.GREEN, 2)


def test_end_turn_events_and_round():
    strike = card(100, STRIKE)
    s = battle(hand=[strike], energy=3)
    s, _ = apply(s, PlayCard(card_uid=strike.uid, connect=False))
    s, events = apply(s, EndTurn())
    discarded = [e for e in events if isinstance(e, CardsDiscarded)]
    assert len(discarded) == 1
    assert discarded[0].card_uids == (strike.uid,)

    s, events = apply(s, EndTurn())  # enemy ends the turn with an empty row
    assert not any(isinstance(e, CardsDiscarded) for e in events)
    assert s.round == 2
    assert s.player_turn is True


def test_illegal_connect_is_rejected():
    block = card(101, BLOCK)
    s = battle(hand=[block], row=[card(100, STRIKE, [Tab(Color.RED, 2)])])
    with pytest.raises(ValueError):
        apply(s, PlayCard(card_uid=block.uid, connect=True))

PONDER = CardDef("ponder", "Ponder", (Color.BLUE,), 1, 0, 0, 2, "starter")

def play_and_end(s, *plays):
    """Play the given (card, connect) pairs, then end the turn."""
    events = []
    for c, connect in plays:
        s, ev = apply(s, PlayCard(card_uid=c.uid, connect=connect))
        events += ev
    s, ev = apply(s, EndTurn())
    return s, events + ev


def test_attack_from_the_rules_example():
    # zasady.md: Strike(+green 2) -> Block(+red 2) -> Strike = 12 damage, cost 1
    c1 = card(100, STRIKE, [Tab(Color.GREEN, 2)])
    block = card(101, BLOCK, [Tab(Color.RED, 2)])
    c2 = card(102, STRIKE)
    s = battle(hand=[c1, block, c2], energy=3)
    s, events = play_and_end(s, (c1, False), (block, True), (c2, True))
    assert s.enemy.hp == 30 - 12
    assert s.round == 1
    damage = [e for e in events if isinstance(e, Damage)]
    assert damage == [Damage(to_player=False, amount=12, absorbed=0)]
    assert s.player.shield == 5 + 2          # Block 5 + green tab 2
    assert s.player.energy == 2              # 1 + 0 + 0 spent


def test_attack_adds_shield_to_attacker():
    block = card(100, BLOCK)
    s = battle(hand=[block])
    s, _ = apply(s, PlayCard(card_uid=block.uid, connect=False))
    s, events = apply(s, EndTurn())
    assert ShieldChanged(player=True, value=5) in events
    assert s.player.shield == 5


def test_shield_absorbs_damage():
    strike = card(100, STRIKE)
    s = battle(hand=[strike])
    s.enemy.shield = 3
    s, events = play_and_end(s, (strike, False))
    assert Damage(to_player=False, amount=5, absorbed=3) in events
    assert s.enemy.hp == 30 - 2
    assert s.enemy.shield == 0


def test_shield_disappears_at_start_of_owners_turn():
    s = battle(hand=[])
    s.player.shield = 4
    s, _ = apply(s, EndTurn())              # automaton's turn: the player's shield stays
    assert s.player.shield == 4
    s, events = apply(s, EndTurn())         # player's turn again
    assert s.player.shield == 0
    assert ShieldChanged(player=True, value=0) in events


def test_no_shield_event_when_shield_was_zero():
    s = battle(hand=[])
    s, events = apply(s, EndTurn())
    assert not any(isinstance(e, ShieldChanged) for e in events)


def test_end_of_turn_draws_three_and_resets_energy():
    s = battle(hand=[], energy=1)
    s, events = apply(s, EndTurn())
    assert len(s.player.hand) == 3
    assert CardsDrawn(player=True, count=3) in events
    assert s.enemy.energy == 3
    assert EnergyChanged(player=False, value=3) in events


def test_blue_tab_adds_cards_to_draw():
    c1 = card(100, STRIKE, [Tab(Color.BLUE, 2)])
    ponder = card(101, PONDER)
    s = battle(hand=[c1, ponder])
    s.player.deck += [card(300 + i, STRIKE) for i in range(5)]    # enough cards to draw 7
    s, events = play_and_end(s, (c1, False), (ponder, True))
    # 3 base + 2 from Ponder + 2 from the blue tab = 7 cards, the hand was empty
    assert CardsDrawn(player=True, count=7) in events
    assert len(s.player.hand) == 7


def test_hand_is_capped_at_seven():
    s = battle(hand=[card(100 + i, STRIKE) for i in range(6)])
    s, events = apply(s, EndTurn())
    assert len(s.player.hand) == 7
    assert CardsDrawn(player=True, count=1) in events


def test_empty_deck_is_refilled_from_discard():
    s = battle(hand=[])
    s.player.discard = s.player.deck[:2] + s.player.discard
    s.player.deck = s.player.deck[2:3]
    total = len(s.player.deck) + len(s.player.discard)
    s, events = apply(s, EndTurn())
    assert len(s.player.hand) == 3
    assert len(s.player.deck) + len(s.player.discard) + len(s.player.hand) == total


def test_battle_ended_is_the_last_event():
    strike = card(100, STRIKE)
    s = battle(hand=[strike])
    s.enemy.hp = 5
    s, events = play_and_end(s, (strike, False))
    assert events[-1] == BattleEnded(BattleResult.WON)
    assert sum(isinstance(e, BattleEnded) for e in events) == 1
    assert s.result == BattleResult.WON
    assert legal_actions(s) == []


def test_player_loses_when_automaton_kills_them():
    s = battle(hand=[])
    s.player.hp = 3
    s.enemy.hand = [card(200, STRIKE)]
    s.enemy.energy = 3
    s, _ = apply(s, EndTurn())                                   # to the automaton's turn
    s, _ = apply(s, PlayCard(card_uid=200, connect=False))
    s, events = apply(s, EndTurn())
    assert s.result == BattleResult.LOST
    assert events[-1] == BattleEnded(BattleResult.LOST)


@given(st.integers(min_value=0, max_value=10_000))
def test_random_games_keep_the_rules(seed):
    rng = random.Random(seed)
    s = create_battle(seed, deck(), deck())
    played = set()
    for _ in range(600):
        actions = legal_actions(s)
        if not actions:
            break
        new, events = apply(s, rng.choice(actions))
        cards = sum(len(x.deck) + len(x.hand) + len(x.discard) for x in (new.player, new.enemy)) + len(new.row)
        assert cards == 20
        assert new.player.energy >= 0 and new.enemy.energy >= 0
        assert new.player.hp >= 0 and new.enemy.hp >= 0
        assert len(new.player.hand) <= 7 and len(new.enemy.hand) <= 7
        for e in events:                          # CardPlayed comes before references to its uid
            if isinstance(e, CardPlayed):
                played.add(e.card.uid)
            elif isinstance(e, TabActivated):
                assert e.card_uid in played
            elif isinstance(e, CardsDiscarded):
                assert set(e.card_uids) <= played
        ended = [isinstance(e, BattleEnded) for e in events]
        if new.result != BattleResult.ONGOING:
            assert ended[-1] and sum(ended) == 1
        else:
            assert not any(ended)
        s = new