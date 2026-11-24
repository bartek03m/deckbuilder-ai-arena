from __future__ import annotations

from dataclasses import dataclass
from typing import Union
from salon.cards import Tab
from salon.engine.state import GameCard, BattleResult


@dataclass(frozen=True)
class CardPlayed:
    by_player: bool
    card: GameCard

@dataclass(frozen=True)
class TabActivated:
    card_uid: int
    tab: Tab

@dataclass(frozen=True)
class Damage:
    to_player: bool
    amount: int
    absorbed: int

@dataclass(frozen=True)
class ShieldChanged:
    player: bool
    value: int

@dataclass(frozen=True)
class CardsDrawn:
    player: bool
    count: int

@dataclass(frozen=True)
class EnergyChanged:
    player: bool
    value: int

@dataclass(frozen=True)
class CardsDiscarded:
    player: bool
    card_uids: tuple[int, ...] # unchangeable list of any length

@dataclass(frozen=True)
class BattleEnded:
    result: BattleResult

Event = Union[CardPlayed, TabActivated, Damage, ShieldChanged,      # Event can be any of the Union types
              CardsDrawn, EnergyChanged, CardsDiscarded, BattleEnded]