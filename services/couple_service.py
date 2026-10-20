"""
Couple Management and Pairing Service for TogetherList.
Handles creating couple spaces, generating invitation codes, validating pairings,
enforcing maximum 2 partners, and couple disconnection.
"""

import secrets
import string
import datetime
from typing import Dict, Optional, Any, List
import streamlit as st
from services.supabase_client import get_supabase_client, is_supabase_configured
from services.demo_store import get_store


def generate_invitation_code() -> str:
    """Generate a clean, readable, secure invitation code like TOGETHER-9X4K2P."""
    chars = string.ascii_uppercase + string.digits
    # avoid easily confused characters like O, 0, I, 1
    safe_chars = [c for c in chars if c not in "O0I1"]
    token = "".join(secrets.choice(safe_chars) for _ in range(6))
    return f"TOGETHER-{token}"


def create_couple_space(user_id: str, couple_name: str = "Our Couple Space") -> Dict[str, Any]:
    """Create a new couple space and generate an invitation code for the partner."""
    client = get_supabase_client()
    invitation_code = generate_invitation_code()

    if client and is_supabase_configured():
        try:
            # 1. Create couple
            c_res = client.table("couples").insert({
                "name": couple_name,
                "status": "active"
            }).execute()
            if not c_res.data:
                return {"success": False, "error": "Failed to create couple space."}

            couple_id = c_res.data[0]["id"]

            # 2. Add creator to couple_members
            client.table("couple_members").insert({
                "couple_id": couple_id,
                "user_id": user_id,
                "role": "creator",
                "status": "active"
            }).execute()

            # 3. Create invitation
            inv_res = client.table("couple_invitations").insert({
                "couple_id": couple_id,
                "created_by": user_id,
                "code": invitation_code,
                "status": "pending"
            }).execute()

            return {
                "success": True,
                "couple_id": couple_id,
                "invitation_code": invitation_code,
                "message": "Couple space created! Share your invitation code with your partner."
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to create couple: {str(e)}"}

    # Demo Fallback
    store = get_store()
    # Check if user already in an active couple
    for m in store["couple_members"].values():
        if m["user_id"] == user_id and m["status"] == "active":
            return {"success": False, "error": "You are already part of an active couple space."}

    import uuid
    couple_id = str(uuid.uuid4())
    store["couples"][couple_id] = {
        "id": couple_id,
        "name": couple_name,
        "status": "active",
        "created_at": datetime.datetime.now().isoformat()
    }
    member_id = str(uuid.uuid4())
    store["couple_members"][member_id] = {
        "id": member_id,
        "couple_id": couple_id,
        "user_id": user_id,
        "role": "creator",
        "status": "active",
        "joined_at": datetime.datetime.now().isoformat()
    }
    inv_id = str(uuid.uuid4())
    store["couple_invitations"][inv_id] = {
        "id": inv_id,
        "couple_id": couple_id,
        "created_by": user_id,
        "code": invitation_code,
        "status": "pending",
        "expires_at": (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat(),
        "accepted_by": None,
        "accepted_at": None,
        "created_at": datetime.datetime.now().isoformat()
    }

    return {
        "success": True,
        "couple_id": couple_id,
        "invitation_code": invitation_code,
        "message": "Demo couple space created! Share your invitation code with your partner."
    }


def get_user_couple_status(user_id: str) -> Dict[str, Any]:
    """
    Get the user's couple membership status, partner information,
    and active pending invitation if waiting for partner to join.
    """
    client = get_supabase_client()

    if client and is_supabase_configured():
        try:
            # Find active membership
            m_res = client.table("couple_members").select("*, couples(*)").eq("user_id", user_id).eq("status", "active").execute()
            if not m_res.data:
                return {"is_paired": False, "has_couple": False, "couple": None, "partner": None, "invitation_code": None}

            membership = m_res.data[0]
            couple = membership.get("couples")
            couple_id = membership["couple_id"]

            # Find other members in this couple
            partners_res = client.table("couple_members").select("*, profiles(*)").eq("couple_id", couple_id).eq("status", "active").neq("user_id", user_id).execute()

            partner = None
            if partners_res.data and len(partners_res.data) > 0:
                p_mem = partners_res.data[0]
                partner = p_mem.get("profiles")

            # If no partner yet, get the latest pending invitation code
            invitation_code = None
            if not partner:
                inv_res = client.table("couple_invitations").select("*").eq("couple_id", couple_id).eq("status", "pending").order("created_at", desc=True).limit(1).execute()
                if inv_res.data:
                    invitation_code = inv_res.data[0]["code"]

            return {
                "is_paired": partner is not None,
                "has_couple": True,
                "couple": couple,
                "couple_id": couple_id,
                "partner": partner,
                "invitation_code": invitation_code
            }
        except Exception as e:
            return {"is_paired": False, "has_couple": False, "error": str(e)}

    # Demo Fallback
    store = get_store()
    user_mem = None
    for m in store["couple_members"].values():
        if m["user_id"] == user_id and m["status"] == "active":
            user_mem = m
            break

    if not user_mem:
        return {"is_paired": False, "has_couple": False, "couple": None, "partner": None, "invitation_code": None}

    couple_id = user_mem["couple_id"]
    couple = store["couples"].get(couple_id)

    # Find partner
    partner = None
    for m in store["couple_members"].values():
        if m["couple_id"] == couple_id and m["status"] == "active" and m["user_id"] != user_id:
            partner_id = m["user_id"]
            partner = store["profiles"].get(partner_id)
            break

    # Find invitation if waiting
    invitation_code = None
    if not partner:
        for inv in store["couple_invitations"].values():
            if inv["couple_id"] == couple_id and inv["status"] == "pending":
                invitation_code = inv["code"]
                break

    return {
        "is_paired": partner is not None,
        "has_couple": True,
        "couple": couple,
        "couple_id": couple_id,
        "partner": partner,
        "invitation_code": invitation_code
    }


def join_couple_with_code(user_id: str, code: str) -> Dict[str, Any]:
    """
    Validate and accept an invitation code to join a partner's couple space.
    Enforces:
    - Code exists and is pending
    - User is not self-joining
    - User is not already in an active couple
    - Space does not already have 2 active members
    """
    code = code.strip().upper()
    if not code:
        return {"success": False, "error": "Please enter an invitation code."}

    client = get_supabase_client()

    if client and is_supabase_configured():
        try:
            # 1. Lookup invitation
            inv_res = client.table("couple_invitations").select("*").eq("code", code).execute()
            if not inv_res.data:
                return {"success": False, "error": "Invalid invitation code. Please check and try again."}

            invitation = inv_res.data[0]
            if invitation["status"] != "pending":
                return {"success": False, "error": "This invitation code has already been used or expired."}

            if invitation["created_by"] == user_id:
                return {"success": False, "error": "You cannot join your own invitation code!"}

            couple_id = invitation["couple_id"]

            # 2. Check if user is already in a couple
            cur_mem = client.table("couple_members").select("*").eq("user_id", user_id).eq("status", "active").execute()
            if cur_mem.data:
                return {"success": False, "error": "You are already connected to a couple space. Please disconnect first if you wish to switch."}

            # 3. Check active member count
            active_members = client.table("couple_members").select("*").eq("couple_id", couple_id).eq("status", "active").execute()
            if len(active_members.data) >= 2:
                return {"success": False, "error": "This couple space is already full (maximum 2 partners permitted)."}

            # 4. Join member
            client.table("couple_members").insert({
                "couple_id": couple_id,
                "user_id": user_id,
                "role": "partner",
                "status": "active"
            }).execute()

            # 5. Mark invitation accepted
            client.table("couple_invitations").update({
                "status": "accepted",
                "accepted_by": user_id,
                "accepted_at": datetime.datetime.now().isoformat()
            }).eq("id", invitation["id"]).execute()

            return {"success": True, "couple_id": couple_id, "message": "Successfully connected to your partner's space!"}
        except Exception as e:
            return {"success": False, "error": f"Failed to join couple: {str(e)}"}

    # Demo Fallback
    store = get_store()
    invitation = None
    for inv in store["couple_invitations"].values():
        if inv["code"] == code:
            invitation = inv
            break

    if not invitation:
        return {"success": False, "error": "Invalid invitation code in demo mode."}

    if invitation["status"] != "pending":
        return {"success": False, "error": "This invitation code has already been used."}

    if invitation["created_by"] == user_id:
        return {"success": False, "error": "You cannot join your own invitation code!"}

    couple_id = invitation["couple_id"]

    # Check if user already in a couple
    for m in store["couple_members"].values():
        if m["user_id"] == user_id and m["status"] == "active":
            return {"success": False, "error": "You are already connected to a couple space."}

    # Count members
    active_count = sum(1 for m in store["couple_members"].values() if m["couple_id"] == couple_id and m["status"] == "active")
    if active_count >= 2:
        return {"success": False, "error": "This couple space is already full (maximum 2 partners permitted)."}

    import uuid
    member_id = str(uuid.uuid4())
    store["couple_members"][member_id] = {
        "id": member_id,
        "couple_id": couple_id,
        "user_id": user_id,
        "role": "partner",
        "status": "active",
        "joined_at": datetime.datetime.now().isoformat()
    }

    invitation["status"] = "accepted"
    invitation["accepted_by"] = user_id
    invitation["accepted_at"] = datetime.datetime.now().isoformat()

    return {"success": True, "couple_id": couple_id, "message": "Successfully connected to your partner in demo mode!"}


def disconnect_couple(user_id: str, couple_id: str) -> Dict[str, Any]:
    """Disconnect from the current couple space with confirmation."""
    client = get_supabase_client()

    if client and is_supabase_configured():
        try:
            # Mark user's membership as disconnected
            client.table("couple_members").update({
                "status": "disconnected"
            }).eq("couple_id", couple_id).eq("user_id", user_id).execute()

            # If no active members remain or creator left, update couple status
            active = client.table("couple_members").select("*").eq("couple_id", couple_id).eq("status", "active").execute()
            if len(active.data) == 0:
                client.table("couples").update({"status": "disconnected"}).eq("id", couple_id).execute()

            return {"success": True, "message": "Successfully disconnected from the couple space."}
        except Exception as e:
            return {"success": False, "error": f"Failed to disconnect: {str(e)}"}

    # Demo Fallback
    store = get_store()
    for m in store["couple_members"].values():
        if m["couple_id"] == couple_id and m["user_id"] == user_id:
            m["status"] = "disconnected"

    # Check remaining
    active_count = sum(1 for m in store["couple_members"].values() if m["couple_id"] == couple_id and m["status"] == "active")
    if active_count == 0 and couple_id in store["couples"]:
        store["couples"][couple_id]["status"] = "disconnected"

    return {"success": True, "message": "Successfully disconnected in demo mode."}
