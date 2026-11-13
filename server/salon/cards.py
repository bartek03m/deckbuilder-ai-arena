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

def _parse_tabs(raw_tabs: Any, card: CardDef, where: str, errors: list[str]) -> tuple[Tab, ...]:
    if not isinstance(raw_tabs, list):
        errors.append(f"{where}: 'tabs' must be a list")
        return ()
    if len(raw_tabs) > MAX_TABS:
        errors.append(f"{where}: at most {MAX_TABS} tabs, got {len(raw_tabs)}")
    tabs: list[Tab] = []
    for j, raw in enumerate(raw_tabs):
        tw = f"{where} tabs[{j}]"
        if not isinstance(raw, dict):
            errors.append(f"{tw}: tab must be an object")
            continue
        n = len(errors)
        _check_fields(raw, TAB_FIELDS, TAB_FIELDS, tw, errors)
        if len(errors) > n:
            continue
        try:
            color = Color(raw["color"])
        except ValueError:
            color = None
        if color not in TAB_COLORS:
            errors.append(f"{tw}: unknown tab color {raw['color']!r}")
            continue
        value = raw["value"]
        if not _is_int(value) or value < 0:
            errors.append(f"{tw}: 'value' must be an integer >= 0, got {value!r}")
            continue
        tabs.append(Tab(color, value))

    colors = [t.color for t in tabs]
    if len(set(colors)) != len(colors):
        errors.append(f"{where}: tab colors must be different")
    if card.is_joker:
        if colors != [Color.RAINBOW]:
            errors.append(f"{where}: Joker must have exactly one 'rainbow' tab")
    elif Color.RAINBOW in colors:
        errors.append(f"{where}: 'rainbow' tab is only allowed on the Joker")
    return tuple(tabs)


def parse_deck(data: Any, cards: dict[str, CardDef]) -> list[CardInstance]:
    """Validate the content of a deck file and return its card copies (count expanded)."""

    errors: list[str] = []
    if not isinstance(data, dict):
        raise CardDataError(["deck: expected an object"])
    _check_fields(data, DECK_FIELDS, DECK_FIELDS, "deck", errors)
    if errors:
        raise CardDataError(errors)
    deck_id = data["id"]
    if not isinstance(deck_id, str) or not deck_id:
        errors.append("deck: 'id' must be a non-empty string")
    if not isinstance(data["cards"], list):
        raise CardDataError(errors + [f"deck '{deck_id}': 'cards' must be a list"])

    instances: list[CardInstance] = []
    for i, raw in enumerate(data["cards"]):
        where = f"deck '{deck_id}' cards[{i}]"
        if not isinstance(raw, dict):
            errors.append(f"{where}: entry must be an object")
            continue
        n = len(errors)
        _check_fields(raw, ENTRY_FIELDS, {"card"}, where, errors)
        if len(errors) > n:
            continue
        card = cards.get(raw["card"])
        if card is None:
            errors.append(f"{where}: unknown card id {raw['card']!r}")
            continue
        where = f"{where} ('{card.id}')"
        count = raw.get("count", 1)
        if not _is_int(count) or count < 1:
            errors.append(f"{where}: 'count' must be an integer >= 1, got {count!r}")
            continue
        tabs = _parse_tabs(raw.get("tabs", []), card, where, errors)
        instances.extend(CardInstance(card, tabs) for _ in range(count))

    jokers = sum(1 for inst in instances if inst.card.is_joker)
    if jokers > MAX_JOKERS_PER_DECK:
        errors.append(f"deck '{deck_id}': at most {MAX_JOKERS_PER_DECK} Joker, got {jokers}")
    if not instances and not errors:
        errors.append(f"deck '{deck_id}': deck is empty")
    if errors:
        raise CardDataError(errors)
    return instances

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

def parse_deck(data: Any, cards: dict[str, CardDef]) -> list[CardInstance]:
    """Validate the content of a deck file and return its card copies (count expanded)."""

    errors: list[str] = []
    if not isinstance(data, dict):
        raise CardDataError(["deck: expected an object"])
    _check_fields(data, DECK_FIELDS, DECK_FIELDS, "deck", errors)
    if errors:
        raise CardDataError(errors)
    deck_id = data["id"]
    if not isinstance(deck_id, str) or not deck_id:
        errors.append("deck: 'id' must be a non-empty string")
    if not isinstance(data["cards"], list):
        raise CardDataError(errors + [f"deck '{deck_id}': 'cards' must be a list"])
 
    instances: list[CardInstance] = []
    for i, raw in enumerate(data["cards"]):
        where = f"deck '{deck_id}' cards[{i}]"
        if not isinstance(raw, dict):
            errors.append(f"{where}: entry must be an object")
            continue
        n = len(errors)
        _check_fields(raw, ENTRY_FIELDS, {"card"}, where, errors)
        if len(errors) > n:
            continue
        card = cards.get(raw["card"])
        if card is None:
            errors.append(f"{where}: unknown card id {raw['card']!r}")
            continue
        where = f"{where} ('{card.id}')"
        count = raw.get("count", 1)
        if not _is_int(count) or count < 1:
            errors.append(f"{where}: 'count' must be an integer >= 1, got {count!r}")
            continue
        tabs = _parse_tabs(raw.get("tabs", []), card, where, errors)
        instances.extend(CardInstance(card, tabs) for _ in range(count))
 
    jokers = sum(1 for inst in instances if inst.card.is_joker)
    if jokers > MAX_JOKERS_PER_DECK:
        errors.append(f"deck '{deck_id}': at most {MAX_JOKERS_PER_DECK} Joker, got {jokers}")
    if not instances and not errors:
        errors.append(f"deck '{deck_id}': deck is empty")
    if errors:
        raise CardDataError(errors)
    return instances


def _read_json(path: Path) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise CardDataError([f"{path.name}: invalid JSON ({e})"]) from e


def load_cards(path: Path | str | None = None) -> dict[str, CardDef]:
    """Load and validate data/cards.json."""

    return parse_cards(_read_json(Path(path) if path else DATA_DIR / "cards.json"))


def load_deck(deck_id: str, cards: dict[str, CardDef] | None = None, data_dir: Path | str | None = None) -> list[CardInstance]:
    """Load and validate data/decks/<deck_id>.json."""

    base = Path(data_dir) if data_dir else DATA_DIR
    if cards is None:
        cards = load_cards(base / "cards.json")
    data = _read_json(base / "decks" / f"{deck_id}.json")
    if isinstance(data, dict) and data.get("id") != deck_id:
        raise CardDataError([f"decks/{deck_id}.json: 'id' is {data.get('id')!r}, expected {deck_id!r}"])
    return parse_deck(data, cards)