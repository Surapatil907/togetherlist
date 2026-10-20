"""
Wishlist Management Service for TogetherList.
Handles CRUD operations for wishlist items, image uploads to Supabase Storage,
filtering by category/priority, and sorting by price or date.
"""

import base64
import uuid
import datetime
from typing import Dict, List, Optional, Any
from services.supabase_client import get_supabase_client, is_supabase_configured
from services.demo_store import get_store

# Default placeholder image data URL (soft romantic gift box SVG)
DEFAULT_PLACEHOLDER_IMAGE = "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500&auto=format&fit=crop&q=80"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def upload_gift_image(uploaded_file, user_id: str) -> Dict[str, Any]:
    """
    Upload a product image to Supabase Storage 'wishlist-images' bucket
    or convert to base64 data URL in demo mode.
    Validates file format and file size limit.
    """
    if uploaded_file is None:
        return {"success": False, "error": "No file uploaded."}

    # Validate file size
    uploaded_file.seek(0, 2)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)

    if file_size > MAX_FILE_SIZE_BYTES:
        return {"success": False, "error": "Image file too large. Maximum size is 5MB."}

    # Validate file type
    filename = uploaded_file.name.lower()
    ext = filename.split(".")[-1] if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return {"success": False, "error": f"Invalid image format '.{ext}'. Supported: PNG, JPG, JPEG, WEBP."}

    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            file_bytes = uploaded_file.read()
            unique_name = f"{user_id}/{uuid.uuid4().hex}.{ext}"
            content_type = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"

            # Upload to Supabase Storage bucket 'wishlist-images'
            client.storage.from_("wishlist-images").upload(
                path=unique_name,
                file=file_bytes,
                file_options={"content-type": content_type}
            )

            # Get public URL
            public_url = client.storage.from_("wishlist-images").get_public_url(unique_name)
            return {"success": True, "url": public_url}
        except Exception as e:
            return {"success": False, "error": f"Failed to upload to Supabase Storage: {str(e)}"}

    # Demo Fallback: Convert to Base64 Data URL for instant local preview
    try:
        file_bytes = uploaded_file.read()
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        mime = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
        data_url = f"data:{mime};base64,{b64}"
        return {"success": True, "url": data_url}
    except Exception as e:
        return {"success": False, "error": f"Failed to process image: {str(e)}"}


def add_wishlist_item(
    couple_id: str,
    user_id: str,
    title: str,
    description: str = "",
    image_url: Optional[str] = None,
    price: float = 0.0,
    currency: str = "GBP",
    retailer: str = "",
    url: str = "",
    category: str = "General",
    priority: str = "Really want",
    preferred_size: str = "",
    preferred_color: str = "",
    brand_or_model: str = "",
    notes: str = "",
    occasion_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new item to the user's wishlist."""
    title = title.strip()
    if not title:
        return {"success": False, "error": "Gift title is required."}

    if price < 0:
        return {"success": False, "error": "Price cannot be negative."}

    valid_priorities = ["Must-have", "Really want", "Nice to have"]
    if priority not in valid_priorities:
        priority = "Really want"

    item_data = {
        "couple_id": couple_id,
        "user_id": user_id,
        "title": title,
        "description": description.strip(),
        "image_url": image_url.strip() if image_url else DEFAULT_PLACEHOLDER_IMAGE,
        "price": round(float(price), 2),
        "currency": currency.upper() if currency else "GBP",
        "retailer": retailer.strip(),
        "url": url.strip(),
        "category": category.strip() if category else "General",
        "priority": priority,
        "preferred_size": preferred_size.strip(),
        "preferred_color": preferred_color.strip(),
        "brand_or_model": brand_or_model.strip(),
        "notes": notes.strip(),
        "occasion_id": occasion_id if occasion_id else None,
        "status": "active"
    }

    client = get_supabase_client()
    if client and is_supabase_configured():
        try:
            res = client.table("wishlist_items").insert(item_data).execute()
            if res.data:
                return {"success": True, "item": res.data[0], "message": "Gift added to your wishlist!"}
            return {"success": False, "error": "Failed to save gift item."}
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}

    # Demo Fallback
    store = get_store()
    item_id = str(uuid.uuid4())
    item_data["id"] = item_id
    item_data["created_at"] = datetime.datetime.now().isoformat()
    item_data["updated_at"] = datetime.datetime.now().isoformat()
    store["wishlist_items"][item_id] = item_data
    return {"success": True, "item": item_data, "message": "Gift added to wishlist in demo mode!"}


def update_wishlist_item(
    item_id: str,
    user_id: str,
    **updates
) -> Dict[str, Any]:
    """Update a wishlist item. Strict rule: only the item owner can edit."""
    client = get_supabase_client()

    if client and is_supabase_configured():
        try:
            # Check ownership
            item_res = client.table("wishlist_items").select("*").eq("id", item_id).execute()
            if not item_res.data:
                return {"success": False, "error": "Item not found."}
            if item_res.data[0]["user_id"] != user_id:
                return {"success": False, "error": "Permission denied: You can only edit your own wishlist items."}

            updates["updated_at"] = datetime.datetime.now().isoformat()
            res = client.table("wishlist_items").update(updates).eq("id", item_id).eq("user_id", user_id).execute()
            return {"success": True, "item": res.data[0] if res.data else None, "message": "Gift updated!"}
        except Exception as e:
            return {"success": False, "error": f"Failed to update gift: {str(e)}"}

    # Demo Fallback
    store = get_store()
    item = store["wishlist_items"].get(item_id)
    if not item:
        return {"success": False, "error": "Item not found in demo mode."}
    if item["user_id"] != user_id:
        return {"success": False, "error": "Permission denied: You can only edit your own wishlist items."}

    for k, v in updates.items():
        item[k] = v
    item["updated_at"] = datetime.datetime.now().isoformat()
    return {"success": True, "item": item, "message": "Gift updated in demo mode!"}


def delete_wishlist_item(item_id: str, user_id: str) -> Dict[str, Any]:
    """Delete a wishlist item. Strict rule: only the item owner can delete."""
    client = get_supabase_client()

    if client and is_supabase_configured():
        try:
            # Check ownership
            item_res = client.table("wishlist_items").select("*").eq("id", item_id).execute()
            if not item_res.data:
                return {"success": False, "error": "Item not found."}
            if item_res.data[0]["user_id"] != user_id:
                return {"success": False, "error": "Permission denied: You can only delete your own wishlist items."}

            client.table("wishlist_items").delete().eq("id", item_id).eq("user_id", user_id).execute()
            return {"success": True, "message": "Gift removed from wishlist."}
        except Exception as e:
            return {"success": False, "error": f"Failed to delete gift: {str(e)}"}

    # Demo Fallback
    store = get_store()
    item = store["wishlist_items"].get(item_id)
    if not item:
        return {"success": False, "error": "Item not found in demo mode."}
    if item["user_id"] != user_id:
        return {"success": False, "error": "Permission denied: You can only delete your own wishlist items."}

    del store["wishlist_items"][item_id]
    return {"success": True, "message": "Gift removed from wishlist in demo mode."}


def get_wishlist_items(
    couple_id: str,
    user_id: str,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: str = "active",
    search_query: Optional[str] = None,
    sort_by: str = "date_desc"
) -> List[Dict[str, Any]]:
    """
    Retrieve wishlist items for a given user within a couple space,
    with filtering by category, priority, status, search term, and sorting.
    """
    client = get_supabase_client()

    if client and is_supabase_configured():
        try:
            query = client.table("wishlist_items").select("*, occasions(title, event_date)").eq("couple_id", couple_id).eq("user_id", user_id)

            if status and status != "all":
                query = query.eq("status", status)

            if category and category != "All":
                query = query.eq("category", category)

            if priority and priority != "All":
                query = query.eq("priority", priority)

            if search_query:
                query = query.ilike("title", f"%{search_query.strip()}%")

            # Sorting
            if sort_by == "price_asc":
                query = query.order("price", desc=False)
            elif sort_by == "price_desc":
                query = query.order("price", desc=True)
            elif sort_by == "date_asc":
                query = query.order("created_at", desc=False)
            else:  # default date_desc
                query = query.order("created_at", desc=True)

            res = query.execute()
            return res.data or []
        except Exception:
            return []

    # Demo Fallback
    store = get_store()
    items = []
    for item in store["wishlist_items"].values():
        if item["couple_id"] != couple_id or item["user_id"] != user_id:
            continue
        if status and status != "all" and item.get("status") != status:
            continue
        if category and category != "All" and item.get("category") != category:
            continue
        if priority and priority != "All" and item.get("priority") != priority:
            continue
        if search_query:
            sq = search_query.lower()
            t = (item.get("title") or "").lower()
            d = (item.get("description") or "").lower()
            r = (item.get("retailer") or "").lower()
            if sq not in t and sq not in d and sq not in r:
                continue

        # Attach occasion info if available
        item_copy = dict(item)
        occ_id = item.get("occasion_id")
        if occ_id and occ_id in store["occasions"]:
            occ = store["occasions"][occ_id]
            item_copy["occasions"] = {"title": occ["title"], "event_date": occ["event_date"]}
        items.append(item_copy)

    # Sort items
    if sort_by == "price_asc":
        items.sort(key=lambda x: float(x.get("price", 0)))
    elif sort_by == "price_desc":
        items.sort(key=lambda x: float(x.get("price", 0)), reverse=True)
    elif sort_by == "date_asc":
        items.sort(key=lambda x: x.get("created_at", ""))
    else:  # date_desc
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return items
