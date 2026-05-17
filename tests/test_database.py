import pytest
from database import Database


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    return Database(db_path)


def test_create_and_get_order(db):
    order = db.create_order(
        user_id=123,
        username="testuser",
        game_id="12345678",
        server="9010",
        package_name="💎 86 алмазов",
        diamonds=86,
        price=15000,
    )
    assert order is not None
    assert order["user_id"] == 123
    assert order["game_id"] == "12345678"
    assert order["status"] == "new"


def test_order_id_format(db):
    order = db.create_order(
        user_id=123,
        username="testuser",
        game_id="12345678",
        server="9010",
        package_name="💎 86 алмазов",
        diamonds=86,
        price=15000,
    )
    assert order["order_id"].startswith("SAINT-123-")


def test_get_latest_order(db):
    order1 = db.create_order(
        user_id=1, username="u1", game_id="111",
        server="1", package_name="pkg", diamonds=86, price=15000,
    )
    order2 = db.create_order(
        user_id=1, username="u1", game_id="222",
        server="2", package_name="pkg", diamonds=172, price=29000,
    )
    latest = db.get_latest_order(1)
    assert latest["id"] == order2["id"]
    assert latest["diamonds"] == 172


def test_update_status(db):
    order = db.create_order(
        user_id=1, username="u", game_id="123",
        server="1", package_name="pkg", diamonds=86, price=15000,
    )
    db.update_status(order["id"], "completed")
    updated = db.get_order(order["id"])
    assert updated["status"] == "completed"


def test_no_orders_for_unknown_user(db):
    assert db.get_latest_order(99999) is None


def test_get_by_order_id(db):
    order = db.create_order(
        user_id=1, username="u", game_id="123",
        server="1", package_name="pkg", diamonds=86, price=15000,
    )
    found = db.get_order_by_order_id(order["order_id"])
    assert found is not None
    assert found["id"] == order["id"]
