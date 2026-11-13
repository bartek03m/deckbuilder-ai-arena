from salon.cards import CardDataError, _check_fields, _is_int

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