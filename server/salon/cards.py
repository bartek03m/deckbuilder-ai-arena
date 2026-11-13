"""Card types. Loading and validating /data is added in S1-09."""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


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

    @property
    def is_joker(self) -> bool:
        return Color.PURPLE in self.colors


@dataclass(frozen=True)
class CardInstance:
    """A concrete copy in a deck: definition + its own tabs."""
    card: CardDef
    tabs: tuple[Tab, ...]


DATA_DIR = Path(__file__).resolve().parents[2]/"data"

CARD_COLORS = {Color.RED, Color.GREEN, Color.BLUE, Color.PURPLE}
TAB_COLORS = {Color.RED, Color.GREEN, Color.BLUE, Color.RAINBOW}
RARITIES = {"starter", "common", "uncommon", "rare"}
EFFECTS = ("damage", "shield", "draw")
MIN_COST, MAX_COST, MAX_TABS = 0, 2, 2 
MAX_JOKERS_PER_DECK = 1

CARD_FIELDS = {"id", "name", "colors", "cost", "effects", "rarity"}
DECK_FIELDS = {"id", "cards"}
ENTRY_FIELDS = {"card", "count", "tabs"}
TAB_FIELDS = {"color", "value"}


class CardDataError(ValueError):
    """Invalid card or deck data. `errors` lists every problem found."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid card data:\n- "+"\n- ".join(errors))

def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)

def _check_fields(obj: dict, allowed: set[str], required: set[str], where: str, errors: list[str]) -> None:
    for key in sorted(required - obj.keys()):
        errors.append(f"{where}: missing field '{key}'")
    for key in sorted(obj.keys() - allowed):
        errors.append(f"{where}: unknown field '{key}'")