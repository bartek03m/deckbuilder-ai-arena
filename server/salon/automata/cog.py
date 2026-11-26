"""Cog - the simplest automaton.

Plays random legal moves with one simple rule - activate a tab if it can.
"""

import random

from salon.automata.interface import EndTurn, Observation, PlayCard, Action

class Cog:
    name = "Cog"

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def choose_action(self, obs: Observation, legal: list[Action]) -> Action:
        """Pick a connecting play if there is one, else a random play, else end the turn."""
        connecting = [a for a in legal if isinstance(a, PlayCard) and a.connect]
        if connecting: # activate a tab if possible
            return self.rng.choice(connecting)

        plays = [a for a in legal if isinstance(a, PlayCard)]
        if plays: # otherwise play a random card
            return self.rng.choice(plays)
        
        return EndTurn()