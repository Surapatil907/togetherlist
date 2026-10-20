"""
Permission and Security Tests for TogetherList.
Enforces:
- Invitation validation (no self-joining, no reuse)
- Couple capacity limits (maximum 2 partners)
- Wishlist edit/delete authorization (owner only)
- Secret gift confidentiality (recipient cannot see notes/spend until revealed)
"""

import pytest
from services.auth_service import sign_up
from services.couple_service import create_couple_space, join_couple_with_code
from services.wishlist_service import add_wishlist_item, update_wishlist_item, delete_wishlist_item
from services.gift_planning_service import (
    record_private_plan_item, reveal_secret_gift, get_revealed_gifts_for_recipient
)
from services.demo_store import reset_store


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


def test_invitation_restrictions_and_pairing():
    # Register 2 users
    u1 = sign_up("user1@example.com", "pass123", "Partner 1")["user"]
    u2 = sign_up("user2@example.com", "pass123", "Partner 2")["user"]

    # Partner 1 creates couple space
    c_res = create_couple_space(u1["id"], "Our Cozy Space")
    assert c_res["success"]
    code = c_res["invitation_code"]

    # Partner 1 tries to join their own code (Self-join restriction)
    self_res = join_couple_with_code(u1["id"], code)
    assert not self_res["success"]
    assert "own invitation" in self_res["error"].lower()

    # Partner 2 joins successfully
    join_res = join_couple_with_code(u2["id"], code)
    assert join_res["success"]

    # Partner tries to reuse code (Invitation reuse restriction)
    reuse_res = join_couple_with_code(u2["id"], code)
    assert not reuse_res["success"]
    assert "already" in reuse_res["error"].lower()


def test_couple_max_two_members_limit():
    # Register 3 users
    u1 = sign_up("u1@example.com", "pass123", "P1")["user"]
    u2 = sign_up("u2@example.com", "pass123", "P2")["user"]
    u3 = sign_up("u3@example.com", "pass123", "P3")["user"]

    c_res = create_couple_space(u1["id"])
    code = c_res["invitation_code"]

    # P2 joins
    join_res = join_couple_with_code(u2["id"], code)
    assert join_res["success"]

    # P3 attempts to join already full couple space
    third_res = join_couple_with_code(u3["id"], code)
    assert not third_res["success"]
    assert "full" in third_res["error"].lower() or "already" in third_res["error"].lower()


def test_wishlist_owner_authorization():
    u1 = sign_up("owner@example.com", "pass123", "Owner")["user"]
    u2 = sign_up("partner@example.com", "pass123", "Partner")["user"]
    c_res = create_couple_space(u1["id"])
    couple_id = c_res["couple_id"]

    # Owner adds an item
    item_res = add_wishlist_item(couple_id, u1["id"], "Leather Bag", price=85.0)
    item_id = item_res["item"]["id"]

    # Partner tries to edit Owner's item
    edit_res = update_wishlist_item(item_id, user_id=u2["id"], title="Hacked Title")
    assert not edit_res["success"]
    assert "permission denied" in edit_res["error"].lower()

    # Partner tries to delete Owner's item
    del_res = delete_wishlist_item(item_id, user_id=u2["id"])
    assert not del_res["success"]
    assert "permission denied" in del_res["error"].lower()

    # Owner edits their own item successfully
    owner_edit = update_wishlist_item(item_id, user_id=u1["id"], title="Vintage Leather Bag")
    assert owner_edit["success"]
    assert owner_edit["item"]["title"] == "Vintage Leather Bag"


def test_secret_gift_confidentiality_and_reveal():
    u1 = sign_up("buyer@example.com", "pass123", "Buyer")["user"]
    u2 = sign_up("recipient@example.com", "pass123", "Recipient")["user"]
    c_res = create_couple_space(u1["id"])
    couple_id = c_res["couple_id"]
    join_couple_with_code(u2["id"], c_res["invitation_code"])

    # Recipient adds an item to their wishlist
    gift_res = add_wishlist_item(couple_id, u2["id"], "Cashmere Scarf", price=60.0)
    gift_id = gift_res["item"]["id"]

    # Buyer records private intention
    plan_res = record_private_plan_item(
        couple_id=couple_id,
        buyer_id=u1["id"],
        partner_id=u2["id"],
        wishlist_item_id=gift_id,
        status="Ordered",
        private_notes="Purchased Burgundy color, tracking #GB948271",
        estimated_spend=60.0,
        actual_spend=55.0
    )
    assert plan_res["success"]
    plan_item_id = plan_res["item"]["id"]

    # Verify recipient CANNOT see it before reveal
    revealed_before = get_revealed_gifts_for_recipient(u2["id"])
    assert len(revealed_before) == 0

    # Buyer deliberately reveals the gift
    rev_res = reveal_secret_gift(u1["id"], plan_item_id)
    assert rev_res["success"]

    # Verify recipient can now see the revealed gift
    revealed_after = get_revealed_gifts_for_recipient(u2["id"])
    assert len(revealed_after) == 1
    assert revealed_after[0]["wishlist_item_id"] == gift_id
