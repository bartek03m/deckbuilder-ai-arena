import copy
import pytest
import json
from collections import Counter
from salon.cards import CardDataError, Color, Tab, _check_fields, _is_int, parse_cards, parse_deck, load_cards, load_deck
def test_card_data_error_lists_all_errors():
    e = CardDataError(["first problem", "second problem"])
    assert e.errors == ["first problem", "second problem"]
    assert "- first problem" in str(e)
    assert "- second problem" in str(e)


def test_is_int():
    assert _is_int(0)
    assert _is_int(5)
    assert not _is_int(True)
    assert not _is_int(1.5)
    assert not _is_int("1")


def test_check_fields_ok():
    errors = []
    _check_fields({"color": "red", "value": 2}, {"color", "value"}, {"color", "value"}, "tab", errors)
    assert errors == []


def test_check_fields_reports_missing_and_unknown():
    errors = []
    _check_fields({"id": "strike", "cots": 1}, {"id", "cost"}, {"id", "cost"}, "cards[0]", errors)
    assert errors == ["cards[0]: missing field 'cost'", "cards[0]: unknown field 'cots'"]


def test_check_fields_optional_field_can_be_missing():
    errors = []
    _check_fields({"card": "strike"}, {"card", "count", "tabs"}, {"card"}, "entry", errors)
    assert errors == []


STRIKE = {"id": "strike", "name": "Strike", "colors": ["red"], "cost": 1, "effects": {"damage": 5}, "rarity": "starter"}

def card(**changes):
    raw = copy.deepcopy(STRIKE)
    raw.update(changes)
    return raw


def test_valid_card():
    c = parse_cards({"cards": [STRIKE]})["strike"]
    assert c.name == "Strike"
    assert c.colors == (Color.RED,)
    assert c.cost == 1
    assert (c.damage, c.shield, c.draw) == (5, 0, 0)
    assert c.rarity == "starter"


def test_two_color_card_ok():
    raw = card(id="calculated_strike", colors=["red", "blue"], cost=2, effects={"damage": 5, "draw": 1})
    assert parse_cards({"cards": [raw]})["calculated_strike"].colors == (Color.RED, Color.BLUE)


def test_joker_card_ok():
    raw = card(id="joker", colors=["purple"], cost=2, effects={"damage": 4, "shield": 4, "draw": 1}, rarity="rare")
    assert parse_cards({"cards": [raw]})["joker"].is_joker


@pytest.mark.parametrize("bad", [
    card(colors=[]),
    card(colors=["red", "green", "blue"]),
    card(colors=["red", "red"]),
    card(colors=["purple", "red"]),
    card(colors=["yellow"]),
    card(colors=["rainbow"]),
    card(cost=3),
    card(cost=-1),
    card(cost=True),
    card(effects={"damage": -1}),
    card(effects={"heal": 2}),
    card(rarity="legendary"),
    card(id="café"),
    card(name=""),
    card(extra=1),
])
def test_invalid_card_rejected(bad):
    with pytest.raises(CardDataError):
        parse_cards({"cards": [bad]})


def test_missing_field_rejected():
    raw = card()
    del raw["cost"]
    with pytest.raises(CardDataError, match="missing field 'cost'"):
        parse_cards({"cards": [raw]})


def test_duplicate_id_rejected():
    with pytest.raises(CardDataError, match="duplicate id"):
        parse_cards({"cards": [STRIKE, STRIKE]})


def test_all_errors_are_reported():
    with pytest.raises(CardDataError) as e:
        parse_cards({"cards": [card(cost=5, rarity="x")]})
    assert len(e.value.errors) == 2


def test_cards_must_be_a_list():
    with pytest.raises(CardDataError):
        parse_cards({"items": []})

JOKER = {"id": "joker", "name": "Joker", "colors": ["purple"], "cost": 2,
         "effects": {"damage": 4, "shield": 4, "draw": 1}, "rarity": "rare"}
RAINBOW = [{"color": "rainbow", "value": 3}]


def known_cards():
    return parse_cards({"cards": [STRIKE, JOKER]})


def deck(*entries):
    return {"id": "test", "cards": list(entries)}


def test_deck_expands_count():
    cards = parse_deck(deck({"card": "strike", "count": 3}), known_cards())
    assert len(cards) == 3
    assert all(c.card.id == "strike" for c in cards)


def test_count_defaults_to_one_and_tabs_to_none():
    [inst] = parse_deck(deck({"card": "strike"}), known_cards())
    assert inst.tabs == ()


def test_tabs_are_read():
    [inst] = parse_deck(deck({"card": "strike", "tabs": [{"color": "green", "value": 2}]}), known_cards())
    assert inst.tabs == (Tab(Color.GREEN, 2),)


def test_joker_with_rainbow_ok():
    [inst] = parse_deck(deck({"card": "joker", "tabs": RAINBOW}), known_cards())
    assert inst.tabs == (Tab(Color.RAINBOW, 3),)


@pytest.mark.parametrize("entry", [
    {"card": "unknown"},
    {"card": ["strike"]},
    {"card": "strike", "count": 0},
    {"card": "strike", "amount": 2},
    {"card": "strike", "tabs": [{"color": "red", "value": 1}, {"color": "green", "value": 1},
                              {"color": "blue", "value": 1}]},
    {"card": "strike", "tabs": [{"color": "red", "value": 1}, {"color": "red", "value": 2}]},
    {"card": "strike", "tabs": [{"color": "red", "value": -1}]},
    {"card": "strike", "tabs": [{"color": "purple", "value": 1}]},
    {"card": "strike", "tabs": RAINBOW},
    {"card": "joker"},
    {"card": "joker", "tabs": [{"color": "red", "value": 3}]},
    {"card": "joker", "tabs": RAINBOW + [{"color": "red", "value": 1}]},
    {"card": "joker", "count": 2, "tabs": RAINBOW},
])
def test_invalid_deck_entry_rejected(entry):
    with pytest.raises(CardDataError):
        parse_deck(deck(entry), known_cards())


def test_two_jokers_in_separate_entries_rejected():
    entry = {"card": "joker", "tabs": RAINBOW}
    with pytest.raises(CardDataError, match="at most 1 Joker"):
        parse_deck(deck(entry, entry), known_cards())


def test_empty_deck_rejected():
    with pytest.raises(CardDataError, match="empty"):
        parse_deck(deck(), known_cards())

def test_cards_json_loads():
    cards = load_cards()
    assert set(cards) == {"strike", "block", "ponder"}
    assert (cards["strike"].damage, cards["block"].shield, cards["ponder"].draw) == (5, 4, 2)


def test_starter_deck_loads():
    starter = load_deck("starter")
    assert len(starter) == 10
    assert Counter(c.card.id for c in starter) == {"strike": 4, "block": 4, "ponder": 2}
    assert all(c.card.cost == 1 for c in starter)


def test_starter_deck_has_three_fixed_tabs():
    tabs = Counter((c.card.id, c.tabs) for c in load_deck("starter"))
    assert tabs[("strike", (Tab(Color.GREEN, 2),))] == 1
    assert tabs[("block", (Tab(Color.RED, 2),))] == 1
    assert tabs[("ponder", (Tab(Color.RED, 1),))] == 1
    assert sum(n for (_, t), n in tabs.items() if t) == 3


def write_data(tmp_path, deck):
    (tmp_path / "decks").mkdir()
    (tmp_path / "cards.json").write_text(json.dumps({"cards": [STRIKE]}), encoding="utf-8")
    (tmp_path / "decks" / "starter.json").write_text(deck, encoding="utf-8")


def test_deck_id_must_match_file_name(tmp_path):
    write_data(tmp_path, json.dumps({"id": "other", "cards": [{"card": "strike"}]}))
    with pytest.raises(CardDataError, match="expected 'starter'"):
        load_deck("starter", data_dir=tmp_path)


def test_invalid_json_reported(tmp_path):
    write_data(tmp_path, '{"id": "starter", "cards": [')
    with pytest.raises(CardDataError, match="invalid JSON"):
        load_deck("starter", data_dir=tmp_path)