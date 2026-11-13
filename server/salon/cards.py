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


def _parse_card(raw: Any, where: str, errors: list[str]) -> CardDef | None:
    if not isinstance(raw, dict):
        errors.append(f"{where}: card must be an object")
        return None
    n = len(errors)
    _check_fields(raw, CARD_FIELDS, CARD_FIELDS, where, errors)
    if len(errors) > n:
        return None

    card_id, name = raw["id"], raw["name"]
    if not isinstance(card_id, str) or not card_id or not card_id.isascii() or not card_id.replace("_", "").isalnum():
        errors.append(f"{where}: 'id' must be a non-empty ASCII name (letters, digits, _), got {card_id!r}")
    else:
        where = f"card '{card_id}'"
    if not isinstance(name, str) or not name.strip():
        errors.append(f"{where}: 'name' must be a non-empty string")

    colors: list[Color] = []
    raw_colors = raw["colors"]
    if not isinstance(raw_colors, list) or not 1 <= len(raw_colors) <= 2:
        errors.append(f"{where}: 'colors' must be a list of 1 or 2 colors")
    else:
        for c in raw_colors:
            try:
                color = Color(c)
            except ValueError:
                color = None
            if color not in CARD_COLORS:
                errors.append(f"{where}: unknown card color {c!r}")
            else:
                colors.append(color)
        if len(set(colors)) != len(colors):
            errors.append(f"{where}: colors must be different")
        if Color.PURPLE in colors and len(raw_colors) > 1:
            errors.append(f"{where}: 'purple' (Joker) cannot have a second color")

    cost = raw["cost"]
    if not _is_int(cost) or not MIN_COST <= cost <= MAX_COST:
        errors.append(f"{where}: 'cost' must be {MIN_COST}-{MAX_COST}, got {cost!r}")

    effects = raw["effects"]
    values = {e: 0 for e in EFFECTS}
    if not isinstance(effects, dict):
        errors.append(f"{where}: 'effects' must be an object")
    else:
        for key, val in effects.items():
            if key not in EFFECTS:
                errors.append(f"{where}: unknown effect {key!r} (allowed: {', '.join(EFFECTS)})")
            elif not _is_int(val) or val < 0:
                errors.append(f"{where}: effect '{key}' must be an integer >= 0, got {val!r}")
            else:
                values[key] = val

    rarity = raw["rarity"]
    if rarity not in RARITIES:
        errors.append(f"{where}: unknown rarity {rarity!r}")

    if len(errors) > n:
        return None
    return CardDef(id=card_id, name=name, colors=tuple(colors), cost=cost,
                   damage=values["damage"], shield=values["shield"], draw=values["draw"], rarity=rarity)


def parse_cards(data: Any) -> dict[str, CardDef]:
    """Validate the content of cards.json and return definitions by id."""

    errors: list[str] = []
    cards: dict[str, CardDef] = {}

    if not isinstance(data, dict) or not isinstance(data.get("cards"), list):
        raise CardDataError(["cards.json: expected an object with a 'cards' list"])
    for i, raw in enumerate(data["cards"]):
        card = _parse_card(raw, f"cards[{i}]", errors)
        if card is None:
            continue
        if card.id in cards:
            errors.append(f"card '{card.id}': duplicate id")
        else:
            cards[card.id] = card
    if errors:
        raise CardDataError(errors)
    return cards