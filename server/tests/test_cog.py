from hypothesis import given, settings, strategies as st

from salon.automata.cog import Cog
from salon.automata.interface import EndTurn, Observation, PlayCard, SideView
from salon.cards import CardInstance, Color, Tab, load_cards, load_deck
from salon.engine.apply import apply
from salon.engine.battle import create_battle
from salon.engine.observation import observe
from salon.engine.rules import legal_actions
from salon.engine.state import BattleResult, GameCard, RowCard

def _empty_obs() -> Observation:
    side = SideView(hp=50, max_hp=50, shield=0, energy=3, deck_count=5, discard_count=0)
    return Observation(
        me=side,
        opponent=side,
        hand=(),
        row=(),
        deck_list=(),
        discard=(),
        opponent_hand=(),
        opponent_deck_list=(),
        opponent_discard=(),
        round=1,
    )

@given(st.integers())
def test_cog_prefers_connecting_play(seed):
    legal = [PlayCard(card_uid=1, connect=False), PlayCard(card_uid=2, connect=True), EndTurn()]
    action = Cog(seed).choose_action(_empty_obs(), legal) 
    assert action == PlayCard(card_uid=2, connect=True)

@given(st.integers())
def test_cog_plays_card_instead_of_ending_turn(seed):
    legal = [PlayCard(card_uid=1, connect=False), PlayCard(card_uid=2, connect=False), EndTurn()]
    action = Cog(seed).choose_action(_empty_obs(), legal)  
    assert isinstance(action, PlayCard)

@given(st.integers())
def test_cog_ends_turn_when_no_card_can_be_played(seed):
    legal = [EndTurn()]
    action = Cog(seed).choose_action(_empty_obs(), legal)  
    assert action == EndTurn()

@given(st.integers())
def test_cog_returns_legal_action(seed):
    legal = [PlayCard(card_uid=1, connect=False), PlayCard(card_uid=2, connect=True), 
             PlayCard(card_uid=3, connect=True), PlayCard(card_uid=4, connect=False), EndTurn()]
    action = Cog(seed).choose_action(_empty_obs(), legal)
    assert action in legal

@given(st.integers())
def test_cog_same_seed_same_moves(seed):
    legal = [PlayCard(card_uid=1, connect=False), PlayCard(card_uid=2, connect=False), 
             PlayCard(card_uid=3, connect=False), EndTurn()]
    first, second = Cog(seed), Cog(seed)

    first_action = [first.choose_action(_empty_obs(), legal) for _ in range(20)]
    second_action = [second.choose_action(_empty_obs(), legal) for _ in range(20)]
    assert first_action == second_action


MAX_STEPS = 1000

@given(st.integers())
@settings(max_examples=20, deadline=None)
def test_cog_vs_cog_battle_ends(seed):
    deck =load_deck("starter")
    state = create_battle(seed, deck, deck)
    player, enemy = Cog(seed), Cog(seed + 11)

    for _ in range(MAX_STEPS):
        if state.result != BattleResult.ONGOING:
            break
        bot = player if state.player_turn else enemy
        obs = observe(state, state.player_turn)
        action = bot.choose_action(obs, legal_actions(state))
        state, _ = apply(state, action)

    assert state.result != BattleResult.ONGOING

def _force_connect_chance(state):
    """Put a strike with a green tab in the row and a block in the player's hand
    so the first move of the battle can always connect."""
    cards = load_cards()
    strike = GameCard(1000, CardInstance(cards["strike"], (Tab(Color.GREEN, 2),)))
    block = GameCard(1001, CardInstance(cards["block"], ()))
    state.row = [RowCard(strike)]
    state.player.hand.append(block)

@given(st.integers())
@settings(max_examples=20, deadline=None)
def test_cog_always_connects_in_real_battle(seed):
    deck = load_deck("starter")
    state = create_battle(seed, deck, deck)
    _force_connect_chance(state)
    player, enemy = Cog(seed), Cog(seed + 11)
    connect_chances = 0

    for _ in range(MAX_STEPS):
        if state.result != BattleResult.ONGOING:
            break
        bot = player if state.player_turn else enemy
        legal = legal_actions(state)
        action = bot.choose_action(observe(state, state.player_turn), legal)

        if any(isinstance(a, PlayCard) and a.connect for a in legal):
            connect_chances += 1
            assert isinstance(action, PlayCard) and action.connect
        state, _ = apply(state, action)

    assert connect_chances > 0