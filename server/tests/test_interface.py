import random

from salon.automata.interface import Automaton, EndTurn, Observation, PlayCard, SideView


class RandomAutomaton:
    name = "random"

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def choose_action(self, obs, legal):
        return self.rng.choice(legal)


def _empty_obs() -> Observation:
    side = SideView(hp=50, max_hp=50, shield=0, energy=3, deck_count=5, discard_count=0)
    return Observation(me=side, opponent=side, hand=(), row=(), opponent_hand=(), opponent_deck_list=(), round=1)


def test_automaton_returns_legal_action():
    bot: Automaton = RandomAutomaton(seed=1)
    legal = [PlayCard(card_uid=0), EndTurn()]

    for _ in range(20):
        assert bot.choose_action(_empty_obs(), legal) in legal
