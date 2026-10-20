"""
Authentication Service for TogetherList.
Handles registration, login, logout, password reset, and profile management
using Supabase Auth (with graceful local demo fallback).
"""

import uuid
import datetime
from typing import Dict, Optional, Any
import streamlit as st
from services.supabase_client import get_supabase_client, is_supabase_configured, reset_session_client
from services.demo_store import get_store


def sign_up(email: str, password: str, display_name: str, avatar_url: Optional[str] = None) -> Dict[str, Any]:
    """Register a new user with email, password, and display name."""
    email = email.strip().lower()
    display_name = display_name.strip()

    if not email or "@" not in email:
        return {"success": False, "error": "Please enter a valid email address."}
    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters long."}
    if not display_name:
        return {"success": False, "error": "Please enter a display name."}

    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            res = client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "display_name": display_name,
                        "avatar_url": avatar_url or ""
                    }
                }
            })
            if res.user:
                # Also ensure profile record exists in public.profiles
                try:
                    client.table("profiles").upsert({
                        "id": res.user.id,
                        "display_name": display_name,
                        "avatar_url": avatar_url or ""
                    }).execute()
                except Exception:
                    pass

                user_data = {
                    "id": res.user.id,
                    "email": email,
                    "display_name": display_name,
                    "avatar_url": avatar_url or ""
                }
                st.session_state.current_user = user_data
                return {"success": True, "user": user_data, "message": "Account created successfully!"}
            else:
                return {"success": False, "error": "Registration failed. Please check your details."}
        except Exception as e:
            err_msg = str(e)
            if "already registered" in err_msg.lower():
                return {"success": False, "error": "This email is already registered. Please log in."}
            return {"success": False, "error": f"Registration error: {err_msg}"}

    # Demo Fallback
    store = get_store()
    for uid, u in store["users"].items():
        if u["email"] == email:
            return {"success": False, "error": "This email is already registered in demo mode."}

    user_id = str(uuid.uuid4())
    store["users"][user_id] = {
        "id": user_id,
        "email": email,
        "password": password,
        "display_name": display_name,
        "avatar_url": avatar_url or "",
        "created_at": datetime.datetime.now().isoformat()
    }
    store["profiles"][user_id] = {
        "id": user_id,
        "display_name": display_name,
        "avatar_url": avatar_url or "",
        "created_at": datetime.datetime.now().isoformat()
    }

    user_data = {
        "id": user_id,
        "email": email,
        "display_name": display_name,
        "avatar_url": avatar_url or ""
    }
    st.session_state.current_user = user_data
    return {"success": True, "user": user_data, "message": "Demo account registered successfully!"}


def sign_in(email: str, password: str) -> Dict[str, Any]:
    """Sign in an existing user with email and password."""
    email = email.strip().lower()
    password = password.strip()

    if not email or not password:
        return {"success": False, "error": "Please enter both email and password."}

    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            res = client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if res.user:
                # Fetch profile details
                profile_res = client.table("profiles").select("*").eq("id", res.user.id).single().execute()
                profile_data = profile_res.data if profile_res and profile_res.data else {}

                user_data = {
                    "id": res.user.id,
                    "email": email,
                    "display_name": profile_data.get("display_name") or (res.user.user_metadata or {}).get("display_name", email.split("@")[0]),
                    "avatar_url": profile_data.get("avatar_url") or (res.user.user_metadata or {}).get("avatar_url", "")
                }
                st.session_state.current_user = user_data
                return {"success": True, "user": user_data}
            return {"success": False, "error": "Invalid email or password."}
        except Exception as e:
            return {"success": False, "error": f"Login failed: {str(e)}"}

    # Demo Fallback
    store = get_store()
    for uid, u in store["users"].items():
        if u["email"] == email and u["password"] == password:
            user_data = {
                "id": uid,
                "email": email,
                "display_name": u["display_name"],
                "avatar_url": u["avatar_url"]
            }
            st.session_state.current_user = user_data
            return {"success": True, "user": user_data}

    return {"success": False, "error": "Invalid email or password in demo mode."}


def sign_out() -> Dict[str, Any]:
    """Sign out the current user and reset session state."""
    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            client.auth.sign_out()
        except Exception:
            pass

    reset_session_client()
    st.session_state.pop("current_user", None)
    st.session_state.pop("couple_info", None)
    st.session_state.pop("partner_info", None)
    return {"success": True}


def reset_password(email: str) -> Dict[str, Any]:
    """Request a password reset email."""
    email = email.strip().lower()
    if not email or "@" not in email:
        return {"success": False, "error": "Please enter a valid email address."}

    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            client.auth.reset_password_for_email(email)
            return {"success": True, "message": "Password reset instructions sent to your email!"}
        except Exception as e:
            return {"success": False, "error": f"Failed to send reset email: {str(e)}"}

    return {"success": True, "message": "In demo mode: Password reset email simulated successfully."}


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return the currently authenticated user dictionary or None."""
    return st.session_state.get("current_user")


def update_profile(display_name: str, avatar_url: Optional[str] = None) -> Dict[str, Any]:
    """Update display name and avatar URL for current user."""
    user = get_current_user()
    if not user:
        return {"success": False, "error": "User not authenticated."}

    display_name = display_name.strip()
    if not display_name:
        return {"success": False, "error": "Display name cannot be empty."}

    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            client.table("profiles").update({
                "display_name": display_name,
                "avatar_url": avatar_url if avatar_url is not None else user.get("avatar_url", ""),
                "updated_at": datetime.datetime.now().isoformat()
            }).eq("id", user["id"]).execute()

            user["display_name"] = display_name
            if avatar_url is not None:
                user["avatar_url"] = avatar_url
            st.session_state.current_user = user
            return {"success": True, "message": "Profile updated successfully!"}
        except Exception as e:
            return {"success": False, "error": f"Failed to update profile: {str(e)}"}

    # Demo Fallback
    store = get_store()
    uid = user["id"]
    if uid in store["profiles"]:
        store["profiles"][uid]["display_name"] = display_name
        if avatar_url is not None:
            store["profiles"][uid]["avatar_url"] = avatar_url
    if uid in store["users"]:
        store["users"][uid]["display_name"] = display_name
        if avatar_url is not None:
            store["users"][uid]["avatar_url"] = avatar_url

    user["display_name"] = display_name
    if avatar_url is not None:
        user["avatar_url"] = avatar_url
    st.session_state.current_user = user
    return {"success": True, "message": "Profile updated successfully in demo mode!"}
