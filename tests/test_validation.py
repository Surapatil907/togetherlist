"""
Validation Unit Tests for TogetherList.
Tests form validation rules, price validations, date recurrence calculations,
and required inputs.
"""

import pytest
import datetime
from services.auth_service import sign_up, sign_in
from services.wishlist_service import add_wishlist_item
from services.occasion_service import calculate_next_occurrence_and_days, add_occasion
from services.demo_store import reset_store


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


def test_sign_up_validation():
    # Invalid email
    res1 = sign_up("invalid-email", "password123", "User")
    assert not res1["success"]
    assert "email" in res1["error"].lower()

    # Short password
    res2 = sign_up("test@example.com", "123", "User")
    assert not res2["success"]
    assert "password" in res2["error"].lower()

    # Empty display name
    res3 = sign_up("test@example.com", "password123", "")
    assert not res3["success"]
    assert "display name" in res3["error"].lower()

    # Valid registration
    res4 = sign_up("valid@example.com", "securePassword123", "Suraj")
    assert res4["success"]
    assert res4["user"]["display_name"] == "Suraj"


def test_wishlist_item_validation():
    # Empty title should fail
    res1 = add_wishlist_item("couple-1", "user-1", title="")
    assert not res1["success"]
    assert "required" in res1["error"].lower()

    # Negative price should fail
    res2 = add_wishlist_item("couple-1", "user-1", title="Sneakers", price=-10.0)
    assert not res2["success"]
    assert "negative" in res2["error"].lower()

    # Valid item creation
    res3 = add_wishlist_item(
        couple_id="couple-1",
        user_id="user-1",
        title="Kindle Paperwhite",
        price=139.99,
        currency="GBP",
        priority="Must-have"
    )
    assert res3["success"]
    assert res3["item"]["price"] == 139.99
    assert res3["item"]["currency"] == "GBP"


def test_occasion_annual_recurrence():
    # Test anniversary recurrence calculation
    today = datetime.date.today()
    past_date = today - datetime.timedelta(days=10)  # 10 days ago this year

    next_occ, days = calculate_next_occurrence_and_days(past_date, is_recurring=True)
    # The next recurrence must be next year, so days remaining > 0
    assert days > 0
    assert next_occ.year == today.year + 1

    # Future date this year
    future_date = today + datetime.timedelta(days=25)
    next_occ2, days2 = calculate_next_occurrence_and_days(future_date, is_recurring=True)
    assert days2 == 25
    assert next_occ2.year == today.year
