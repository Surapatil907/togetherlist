"""
In-memory store for TogetherList when Supabase credentials are not configured yet.
Mirrors the exact tables, constraints, and Row Level Security isolation rules
from database/schema.sql so the full application workflow can be demonstrated and tested.
"""

import uuid
import datetime
from typing import Dict, List, Optional, Any

# Global simulated persistent database for local demonstration
_STORE: Dict[str, Any] = {
    "users": {},            # id -> {email, password, display_name, avatar_url, created_at}
    "profiles": {},         # id -> {id, display_name, avatar_url, created_at}
    "couples": {},          # id -> {id, name, status, created_at}
    "couple_members": {},   # id -> {id, couple_id, user_id, role, status, joined_at}
    "couple_invitations": {}, # id -> {id, couple_id, created_by, code, status, expires_at, accepted_by, accepted_at}
    "occasions": {},        # id -> {id, couple_id, created_by, title, event_date, is_recurring, occasion_type, description, budget}
    "wishlist_items": {},   # id -> {id, couple_id, user_id, title, description, image_url, price, currency, retailer, url, category, priority, preferred_size, preferred_color, brand_or_model, notes, occasion_id, status, created_at}
    "private_gift_plans": {}, # id -> {id, couple_id, buyer_id, partner_id, title}
    "private_gift_plan_items": {} # id -> {id, plan_id, buyer_id, wishlist_item_id, status, private_notes, purchase_date, reveal_date, is_revealed, estimated_spend, actual_spend}
}

def get_store() -> Dict[str, Any]:
    return _STORE

def reset_store():
    global _STORE
    for k in _STORE:
        _STORE[k].clear()
