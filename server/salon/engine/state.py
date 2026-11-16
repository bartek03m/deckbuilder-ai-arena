from __future__ import annotations

import random
from dataclasses import dataclass, field
from salon.cards import CardInstance

@dataclass(frozen=True) # frozen means not changeable after creation
class GameCard:
    """concrete card in a battle"""
    uid: int # type here is only a suggestion / is not enforced
    instance: CardInstance

@dataclass
class SideState:
    """everything that belongs to one side (player or enemy)"""
    hp: int
    max_hp: int
    shield: int = 0
    energy: int = 0
    deck: list[GameCard] = field(default_factory=list)      # top of the deck = end of the list
    hand: list[GameCard] = field(default_factory=list)      # field(...) creates those lists by default
    discard: list[GameCard] = field(default_factory=list)

    @property
    def deck_count(self) -> int:
        return len(self.deck)

    @property
    def discard_count(self) -> int:
        return len(self.discard)


@dataclass
class BattleState:
    player: SideState
    enemy: SideState
    row: list[GameCard]
    round: int
    rng: random.Random      # the ONLY source of randomness in a battle