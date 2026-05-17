import pytest
from config import format_price, PACKAGES


def test_format_price():
    assert format_price(15000) == "15 000 сум"
    assert format_price(0) == "0 сум"
    assert format_price(1_000_000) == "1 000 000 сум"


def test_packages_structure():
    for name, pkg in PACKAGES.items():
        assert "diamonds" in pkg
        assert "price" in pkg
        assert pkg["diamonds"] > 0
        assert pkg["price"] > 0


def test_packages_sorted():
    prices = [p["price"] for p in PACKAGES.values()]
    assert prices == sorted(prices)
