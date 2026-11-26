from hypothesis import given, strategies as st

from salon.automata.cog import Cog
from salon.automata.interface import EndTurn, Observation, PlayCard, SideView


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