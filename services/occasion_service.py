"""
Special Dates and Occasions Service for TogetherList.
Handles birthdays, anniversaries, custom occasions, annual recurrence calculations,
and countdown timers for upcoming celebrations.
"""

import uuid
import datetime
from typing import Dict, List, Optional, Any
from services.supabase_client import get_supabase_client, is_supabase_configured
from services.demo_store import get_store


def calculate_next_occurrence_and_days(event_date: datetime.date, is_recurring: bool) -> tuple[datetime.date, int]:
    """
    Calculate the next occurrence date and days remaining from today.
    If recurring, shifts the year to current or next year so the event is in the future.
    """
    today = datetime.date.today()

    if not is_recurring:
        days = (event_date - today).days
        return event_date, days

    # Annual recurring event: find next occurrence
    try:
        candidate = datetime.date(today.year, event_date.month, event_date.day)
    except ValueError:
        # Handle Leap Day Feb 29 on non-leap years
        candidate = datetime.date(today.year, event_date.month, 28)

    if candidate < today:
        try:
            candidate = datetime.date(today.year + 1, event_date.month, event_date.day)
        except ValueError:
            candidate = datetime.date(today.year + 1, event_date.month, 28)

    days = (candidate - today).days
    return candidate, days


def add_occasion(
    couple_id: str,
    created_by: str,
    title: str,
    event_date: datetime.date,
    is_recurring: bool = False,
    occasion_type: str = "custom",
    description: str = "",
    budget: Optional[float] = None
) -> Dict[str, Any]:
    """Create a new special date for the couple space."""
    title = title.strip()
    if not title:
        return {"success": False, "error": "Occasion title is required."}

    valid_types = ["birthday", "anniversary", "valentines", "christmas", "custom"]
    if occasion_type not in valid_types:
        occasion_type = "custom"

    date_str = event_date.isoformat() if isinstance(event_date, datetime.date) else str(event_date)

    data = {
        "couple_id": couple_id,
        "created_by": created_by,
        "title": title,
        "event_date": date_str,
        "is_recurring": bool(is_recurring),
        "occasion_type": occasion_type,
        "description": description.strip(),
        "budget": round(float(budget), 2) if budget is not None and budget >= 0 else None
    }

    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            res = client.table("occasions").insert(data).execute()
            if res.data:
                return {"success": True, "occasion": res.data[0], "message": "Special date added!"}
            return {"success": False, "error": "Failed to add occasion."}
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}

    # Demo Fallback
    store = get_store()
    occ_id = str(uuid.uuid4())
    data["id"] = occ_id
    data["created_at"] = datetime.datetime.now().isoformat()
    store["occasions"][occ_id] = data
    return {"success": True, "occasion": data, "message": "Special date added in demo mode!"}


def delete_occasion(occasion_id: str, couple_id: str) -> Dict[str, Any]:
    """Delete an occasion."""
    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            client.table("occasions").delete().eq("id", occasion_id).eq("couple_id", couple_id).execute()
            return {"success": True, "message": "Occasion removed."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    store = get_store()
    if occasion_id in store["occasions"]:
        del store["occasions"][occasion_id]
    return {"success": True, "message": "Occasion removed in demo mode."}


def get_couple_occasions(couple_id: str) -> List[Dict[str, Any]]:
    """Retrieve all occasions for a couple space with calculated countdown days."""
    client = get_supabase_client()
    raw_list = []

    if client and is_supabase_configured():
        try:
            res = client.table("occasions").select("*").eq("couple_id", couple_id).execute()
            raw_list = res.data or []
        except Exception:
            raw_list = []
    else:
        store = get_store()
        raw_list = [occ for occ in store["occasions"].values() if occ["couple_id"] == couple_id]

    enriched = []
    for occ in raw_list:
        try:
            d_val = occ["event_date"]
            if isinstance(d_val, str):
                parsed_date = datetime.date.fromisoformat(d_val)
            else:
                parsed_date = d_val

            next_date, days = calculate_next_occurrence_and_days(parsed_date, occ.get("is_recurring", False))
            occ_copy = dict(occ)
            occ_copy["next_occurrence"] = next_date
            occ_copy["days_remaining"] = days
            enriched.append(occ_copy)
        except Exception:
            continue

    # Sort by upcoming days (positive days first, past events next)
    enriched.sort(key=lambda x: (x["days_remaining"] < 0, abs(x["days_remaining"])))
    return enriched


def get_next_upcoming_occasion(couple_id: str) -> Optional[Dict[str, Any]]:
    """Get the single closest upcoming occasion."""
    occasions = get_couple_occasions(couple_id)
    future = [o for o in occasions if o.get("days_remaining", -1) >= 0]
    return future[0] if future else (occasions[0] if occasions else None)
