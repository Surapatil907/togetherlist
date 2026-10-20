"""
Secret Gift Planner Service for TogetherList.
Enforces strict database-level and service-level privacy for gift purchases:
Recipients CANNOT see status, spending, or private notes until deliberately revealed by buyer.
"""

import uuid
import datetime
from typing import Dict, List, Optional, Any
from services.supabase_client import get_supabase_client, is_supabase_configured
from services.demo_store import get_store

ALLOWED_STATUSES = ["Considering", "Reserved", "Purchased", "Ordered", "Delivered", "Revealed"]


def get_or_create_plan(couple_id: str, buyer_id: str, partner_id: str) -> Dict[str, Any]:
    """Retrieve or create the buyer's private gift plan container."""
    client = get_supabase_client()

    if client and is_supabase_configured():
        try:
            # Check existing plan
            res = client.table("private_gift_plans").select("*").eq("couple_id", couple_id).eq("buyer_id", buyer_id).execute()
            if res.data:
                return {"success": True, "plan": res.data[0]}

            # Create new plan
            new_plan = {
                "couple_id": couple_id,
                "buyer_id": buyer_id,
                "partner_id": partner_id,
                "title": "Secret Gift Plan"
            }
            create_res = client.table("private_gift_plans").insert(new_plan).execute()
            if create_res.data:
                return {"success": True, "plan": create_res.data[0]}
            return {"success": False, "error": "Could not create secret plan container."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Demo Fallback
    store = get_store()
    for p in store["private_gift_plans"].values():
        if p["couple_id"] == couple_id and p["buyer_id"] == buyer_id:
            return {"success": True, "plan": p}

    plan_id = str(uuid.uuid4())
    plan_obj = {
        "id": plan_id,
        "couple_id": couple_id,
        "buyer_id": buyer_id,
        "partner_id": partner_id,
        "title": "Secret Gift Plan",
        "created_at": datetime.datetime.now().isoformat()
    }
    store["private_gift_plans"][plan_id] = plan_obj
    return {"success": True, "plan": plan_obj}


def record_private_plan_item(
    couple_id: str,
    buyer_id: str,
    partner_id: str,
    wishlist_item_id: str,
    status: str = "Considering",
    private_notes: str = "",
    purchase_date: Optional[datetime.date] = None,
    reveal_date: Optional[datetime.date] = None,
    estimated_spend: float = 0.0,
    actual_spend: float = 0.0
) -> Dict[str, Any]:
    """
    Save or update a private intention on a partner's wishlist item.
    Status can be: Considering, Reserved, Purchased, Ordered, Delivered, Revealed.
    """
    if status not in ALLOWED_STATUSES:
        status = "Considering"

    plan_res = get_or_create_plan(couple_id, buyer_id, partner_id)
    if not plan_res.get("success"):
        return plan_res

    plan = plan_res["plan"]
    plan_id = plan["id"]

    data = {
        "plan_id": plan_id,
        "buyer_id": buyer_id,
        "wishlist_item_id": wishlist_item_id,
        "status": status,
        "private_notes": private_notes.strip(),
        "purchase_date": purchase_date.isoformat() if purchase_date else None,
        "reveal_date": reveal_date.isoformat() if reveal_date else None,
        "is_revealed": (status == "Revealed"),
        "estimated_spend": round(float(estimated_spend), 2),
        "actual_spend": round(float(actual_spend), 2)
    }

    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            # Check if record already exists for this wishlist_item_id and plan
            existing = client.table("private_gift_plan_items").select("*").eq("plan_id", plan_id).eq("wishlist_item_id", wishlist_item_id).execute()
            if existing.data:
                item_id = existing.data[0]["id"]
                data["updated_at"] = datetime.datetime.now().isoformat()
                upd = client.table("private_gift_plan_items").update(data).eq("id", item_id).execute()
                return {"success": True, "item": upd.data[0] if upd.data else None, "message": "Secret plan updated!"}
            else:
                ins = client.table("private_gift_plan_items").insert(data).execute()
                return {"success": True, "item": ins.data[0] if ins.data else None, "message": "Secret intention recorded!"}
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}

    # Demo Fallback
    store = get_store()
    for pi in store["private_gift_plan_items"].values():
        if pi["plan_id"] == plan_id and pi["wishlist_item_id"] == wishlist_item_id:
            pi.update(data)
            pi["updated_at"] = datetime.datetime.now().isoformat()
            return {"success": True, "item": pi, "message": "Secret plan updated in demo mode!"}

    pi_id = str(uuid.uuid4())
    data["id"] = pi_id
    data["created_at"] = datetime.datetime.now().isoformat()
    store["private_gift_plan_items"][pi_id] = data
    return {"success": True, "item": data, "message": "Secret intention recorded in demo mode!"}


def reveal_secret_gift(buyer_id: str, plan_item_id: str) -> Dict[str, Any]:
    """Deliberately reveal a secret gift to the partner."""
    client = get_supabase_client()

    updates = {
        "is_revealed": True,
        "status": "Revealed",
        "reveal_date": datetime.date.today().isoformat()
    }

    if client and is_supabase_configured():
        try:
            res = client.table("private_gift_plan_items").update(updates).eq("id", plan_item_id).eq("buyer_id", buyer_id).execute()
            return {"success": True, "message": "Gift revealed to your partner! 🎉"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    store = get_store()
    item = store["private_gift_plan_items"].get(plan_item_id)
    if not item or item["buyer_id"] != buyer_id:
        return {"success": False, "error": "Item not found or unauthorized."}

    item.update(updates)
    return {"success": True, "message": "Gift revealed to your partner in demo mode! 🎉"}


def delete_secret_plan_item(buyer_id: str, plan_item_id: str) -> Dict[str, Any]:
    """Delete a private gift intention."""
    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            client.table("private_gift_plan_items").delete().eq("id", plan_item_id).eq("buyer_id", buyer_id).execute()
            return {"success": True, "message": "Secret plan removed."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    store = get_store()
    item = store["private_gift_plan_items"].get(plan_item_id)
    if item and item["buyer_id"] == buyer_id:
        del store["private_gift_plan_items"][plan_item_id]
    return {"success": True, "message": "Secret plan removed."}


def get_buyer_private_plans(buyer_id: str) -> List[Dict[str, Any]]:
    """Retrieve all secret gift plan items created by the buyer."""
    client = get_supabase_client()

    if client and is_supabase_configured():
        try:
            res = client.table("private_gift_plan_items").select("*, wishlist_items(*)").eq("buyer_id", buyer_id).order("created_at", desc=True).execute()
            return res.data or []
        except Exception:
            return []

    store = get_store()
    plans = []
    for pi in store["private_gift_plan_items"].values():
        if pi["buyer_id"] == buyer_id:
            pi_copy = dict(pi)
            w_id = pi.get("wishlist_item_id")
            if w_id and w_id in store["wishlist_items"]:
                pi_copy["wishlist_items"] = dict(store["wishlist_items"][w_id])
            plans.append(pi_copy)

    plans.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return plans


def get_buyer_spending_summary(buyer_id: str) -> Dict[str, Any]:
    """Calculate the buyer's private budget summary."""
    items = get_buyer_private_plans(buyer_id)
    total_est = sum(float(i.get("estimated_spend") or 0.0) for i in items)
    total_act = sum(float(i.get("actual_spend") or 0.0) for i in items)
    counts: Dict[str, int] = {s: 0 for s in ALLOWED_STATUSES}
    for i in items:
        st_val = i.get("status")
        if st_val in counts:
            counts[st_val] += 1
    return {
        "total_estimated": total_est,
        "total_actual": total_act,
        "status_counts": counts,
        "total_planned_gifts": len(items)
    }


def get_revealed_gifts_for_recipient(recipient_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve gifts that the partner has deliberately revealed to the recipient.
    Strict privacy: only is_revealed = True items are returned.
    """
    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            # Queries wishlist_items owned by recipient that have revealed plan items
            res = client.table("private_gift_plan_items").select("*, wishlist_items!inner(*)").eq("is_revealed", True).eq("wishlist_items.user_id", recipient_id).execute()
            return res.data or []
        except Exception:
            return []

    store = get_store()
    revealed = []
    for pi in store["private_gift_plan_items"].values():
        if pi.get("is_revealed", False):
            w_id = pi.get("wishlist_item_id")
            if w_id and w_id in store["wishlist_items"]:
                w_item = store["wishlist_items"][w_id]
                if w_item["user_id"] == recipient_id:
                    pi_copy = dict(pi)
                    pi_copy["wishlist_items"] = dict(w_item)
                    revealed.append(pi_copy)
    return revealed
