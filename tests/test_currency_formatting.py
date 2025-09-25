from src.utils.currency import format_cedis


def test_format_cedis_positive():
    assert format_cedis(1234.5) == "1,234.50 cedis"


def test_format_cedis_non_positive():
    assert format_cedis(0) == "0"
    assert format_cedis(-100) == "0"
