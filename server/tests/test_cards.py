import copy
import pytest
from salon.cards import CardDataError, Color, _check_fields, _is_int, parse_cards

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
    _check_fields({"id": "cios", "cots": 1}, {"id", "cost"}, {"id", "cost"}, "cards[0]", errors)
    assert errors == ["cards[0]: missing field 'cost'", "cards[0]: unknown field 'cots'"]


def test_check_fields_optional_field_can_be_missing():
    errors = []
    _check_fields({"card": "cios"}, {"card", "count", "tabs"}, {"card"}, "entry", errors)
    assert errors == []


CIOS = {"id": "cios", "name": "Cios", "colors": ["red"], "cost": 1, "effects": {"damage": 5}, "rarity": "starter"}

def card(**changes):
    raw = copy.deepcopy(CIOS)
    raw.update(changes)
    return raw


def test_valid_card():
    c = parse_cards({"cards": [CIOS]})["cios"]
    assert c.name == "Cios"
    assert c.colors == (Color.RED,)
    assert c.cost == 1
    assert (c.damage, c.shield, c.draw) == (5, 0, 0)
    assert c.rarity == "starter"


def test_two_color_card_ok():
    raw = card(id="przemyslany_cios", colors=["red", "blue"], cost=2, effects={"damage": 5, "draw": 1})
    assert parse_cards({"cards": [raw]})["przemyslany_cios"].colors == (Color.RED, Color.BLUE)


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
    card(id="przemyślany"),
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
        parse_cards({"cards": [CIOS, CIOS]})


def test_all_errors_are_reported():
    with pytest.raises(CardDataError) as e:
        parse_cards({"cards": [card(cost=5, rarity="x")]})
    assert len(e.value.errors) == 2


def test_cards_must_be_a_list():
    with pytest.raises(CardDataError):
        parse_cards({"karty": []})