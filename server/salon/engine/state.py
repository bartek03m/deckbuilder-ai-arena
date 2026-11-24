from __future__ import annotations

import random
import copy
from dataclasses import dataclass, field
from salon.cards import CardInstance, Tab
from enum import Enum

class BattleResult(str, Enum):
    ONGOING = "ongoing"
    WON = "won"
    LOST = "lost"

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
class RowCard:
    card: GameCard
    connected: bool = False # by default card is not connected
    tab: Tab | None = None  # tab is Tab if there is connection or is None (by default is None)

@dataclass
class BattleState:
    player: SideState
    enemy: SideState
    row: list[RowCard]
    round: int
    rng: random.Random      # the ONLY source of randomness in a battle
    player_turn: bool = True    # True -> player's turn , False = bot
    result: BattleResult = BattleResult.ONGOING # game starts as ongoing

    # two properties to check whose turn is it
    @property
    def active_side(self) -> SideState:
        return self.player if self.player_turn else self.enemy

    @property
    def inactive_side(self) -> SideState:
        return self.enemy if self.player_turn else self.player

    def clone_state(self) -> BattleState:
        return copy.deepcopy(self)