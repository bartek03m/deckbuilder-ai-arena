"""Card types. Loading and validating /data is added in S1-09."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Color(str, Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"    # card color only (Joker)
    RAINBOW = "rainbow"  # tab color only (Joker)


@dataclass(frozen=True)
class Tab:
    """Tab: color + bonus value."""
    color: Color
    value: int


@dataclass(frozen=True)
class CardDef:
    """Card definition (one entry in cards.json)."""
    id: str
    name: str
    colors: tuple[Color, ...]
    cost: int
    damage: int
    shield: int
    draw: int
    rarity: str


@dataclass(frozen=True)
class CardInstance:
    """A concrete copy in a deck: definition + its own tabs."""
    card: CardDef
    tabs: tuple[Tab, ...]
