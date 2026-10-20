"""
My Wishlist Page — TogetherList
Allows the user to add, view, edit, archive, and delete items from their personal wishlist.
"""

import streamlit as st
from services.auth_service import get_current_user
from services.couple_service import get_user_couple_status
from services.wishlist_service import (
    get_wishlist_items, add_wishlist_item, update_wishlist_item,
    delete_wishlist_item, upload_gift_image, DEFAULT_PLACEHOLDER_IMAGE
)
from services.occasion_service import get_couple_occasions
from components.gift_card import render_card_styles, render_gift_card_html
from components.navigation import render_top_header, render_sidebar


def render_page():
    st.set_page_config(page_title="My Wishlist — TogetherList", page_icon="🎁", layout="wide")
    render_card_styles()
    render_sidebar()

    user = get_current_user()
    if not user:
        st.warning("Please log in on the Home page to view your wishlist.")
        st.stop()
        return

    couple_status = get_user_couple_status(user["id"])
    if not couple_status.get("has_couple"):
        st.warning("Please create or join a couple space on the Home page first.")
        st.stop()
        return

    couple_id = couple_status["couple_id"]

    st.title("🎁 My Wishlist")
    st.markdown("Add gifts you'd love to receive. Your partner can view this list anytime!")

    # Occasions for dropdown linking
    occasions = get_couple_occasions(couple_id)
    occ_options = {"None": None}
    for o in occasions:
        occ_options[f"{o['title']} ({str(o.get('next_occurrence', ''))})"] = o["id"]

    # --- ADD GIFT EXPANDER / FORM ---
    with st.expander("➕ Add a New Gift to My Wishlist", expanded=False):
        with st.form("add_gift_form", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                title = st.text_input("Gift Name *", placeholder="e.g. Cashmere Knit Sweater")
                description = st.text_area("Description / Details", placeholder="Why you'd love this, style notes, or specifications...")

                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    price = st.number_input("Price (£ GBP by default) *", min_value=0.0, value=0.0, step=5.0)
                    currency = st.selectbox("Currency", ["GBP", "USD", "EUR"], index=0)
                    category = st.selectbox("Category", ["Fashion & Clothing", "Tech & Gadgets", "Books & Stationery", "Home & Kitchen", "Experiences & Dates", "Fragrance & Beauty", "Jewellery & Watches", "General"], index=0)
                with col_sub2:
                    retailer = st.text_input("Retailer / Brand Name", placeholder="e.g. Uniqlo, Apple, Selfridges")
                    url = st.text_input("Product Web Link", placeholder="https://...")
                    priority = st.selectbox("Priority", ["Must-have", "Really want", "Nice to have"], index=1)

            with col2:
                st.markdown("**Product Image**")
                image_option = st.radio("Image Source", ["Upload Photo", "Image URL"], horizontal=True)
                uploaded_img = None
                manual_img_url = ""
                if image_option == "Upload Photo":
                    uploaded_img = st.file_uploader("Upload Product Photo (PNG, JPG, max 5MB)", type=["png", "jpg", "jpeg", "webp"])
                else:
                    manual_img_url = st.text_input("Direct Image URL", placeholder="https://example.com/item.jpg")

                st.markdown("---")
                st.markdown("**Personal Preferences**")
                size = st.text_input("Size (Optional)", placeholder="e.g. Medium, UK 6, 42mm")
                color = st.text_input("Preferred Colour (Optional)", placeholder="e.g. Forest Green, Heather Grey")
                brand_or_model = st.text_input("Model / Ref (Optional)", placeholder="e.g. Model A2848")
                chosen_occ_name = st.selectbox("Associate with Occasion (Optional)", list(occ_options.keys()))
                notes = st.text_input("Private Note for Partner (Optional)", placeholder="e.g. Wait until Black Friday if possible")

            submitted = st.form_submit_button("✨ Save to My Wishlist", use_container_width=True)
            if submitted:
                if not title.strip():
                    st.error("Gift Name is required.")
                else:
                    final_img_url = None
                    if uploaded_img:
                        with st.spinner("Processing image..."):
                            up_res = upload_gift_image(uploaded_img, user["id"])
                            if up_res.get("success"):
                                final_img_url = up_res.get("url")
                            else:
                                st.warning(f"Could not upload image: {up_res.get('error')}. Using default placeholder.")
                    elif manual_img_url.strip():
                        final_img_url = manual_img_url.strip()

                    occ_id = occ_options.get(chosen_occ_name)
                    res = add_wishlist_item(
                        couple_id=couple_id,
                        user_id=user["id"],
                        title=title,
                        description=description,
                        image_url=final_img_url,
                        price=price,
                        currency=currency,
                        retailer=retailer,
                        url=url,
                        category=category,
                        priority=priority,
                        preferred_size=size,
                        preferred_color=color,
                        brand_or_model=brand_or_model,
                        notes=notes,
                        occasion_id=occ_id
                    )
                    if res.get("success"):
                        st.success("🎉 Added gift to your wishlist!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Failed to add gift."))

    st.markdown("---")

    # --- SEARCH, FILTERS & SORTING ---
    col_search, col_cat, col_prio, col_sort, col_status = st.columns([2, 1.2, 1.2, 1.2, 1])
    with col_search:
        search_q = st.text_input("🔍 Search gifts", placeholder="Title, brand, retailer...")
    with col_cat:
        cat_filter = st.selectbox("Category", ["All", "Fashion & Clothing", "Tech & Gadgets", "Books & Stationery", "Home & Kitchen", "Experiences & Dates", "Fragrance & Beauty", "Jewellery & Watches", "General"])
    with col_prio:
        prio_filter = st.selectbox("Priority", ["All", "Must-have", "Really want", "Nice to have"])
    with col_sort:
        sort_filter = st.selectbox("Sort By", ["Newest First", "Oldest First", "Price: Low to High", "Price: High to Low"])
    with col_status:
        status_filter = st.selectbox("Status", ["Active", "Archived", "All"])

    sort_map = {
        "Newest First": "date_desc",
        "Oldest First": "date_asc",
        "Price: Low to High": "price_asc",
        "Price: High to Low": "price_desc"
    }

    items = get_wishlist_items(
        couple_id=couple_id,
        user_id=user["id"],
        category=cat_filter,
        priority=prio_filter,
        status="active" if status_filter == "Active" else ("archived" if status_filter == "Archived" else "all"),
        search_query=search_q,
        sort_by=sort_map[sort_filter]
    )

    if not items:
        st.info("No gifts found. Click **➕ Add a New Gift** above to get started!")
    else:
        st.caption(f"Showing {len(items)} gift{'s' if len(items) != 1 else ''}")

        cols_grid = st.columns(3)
        for idx, item in enumerate(items):
            col = cols_grid[idx % 3]
            with col:
                st.markdown(render_gift_card_html(item, is_owner=True), unsafe_allow_html=True)

                c_act1, c_act2, c_act3 = st.columns(3)
                with c_act1:
                    with st.popover("✏️ Edit"):
                        with st.form(f"edit_form_{item['id']}"):
                            new_title = st.text_input("Name", value=item.get("title", ""))
                            new_desc = st.text_area("Description", value=item.get("description", ""))
                            new_price = st.number_input("Price", value=float(item.get("price", 0.0)), step=5.0)
                            new_prio = st.selectbox("Priority", ["Must-have", "Really want", "Nice to have"], index=["Must-have", "Really want", "Nice to have"].index(item.get("priority", "Really want")))
                            new_url = st.text_input("URL", value=item.get("url", ""))
                            new_img = st.text_input("Image URL", value=item.get("image_url", ""))
                            new_ret = st.text_input("Retailer", value=item.get("retailer", ""))
                            if st.form_submit_button("Save Changes"):
                                up_res = update_wishlist_item(
                                    item_id=item["id"],
                                    user_id=user["id"],
                                    title=new_title,
                                    description=new_desc,
                                    price=new_price,
                                    priority=new_prio,
                                    url=new_url,
                                    image_url=new_img,
                                    retailer=new_ret
                                )
                                if up_res.get("success"):
                                    st.success("Updated!")
                                    st.rerun()
                                else:
                                    st.error(up_res.get("error"))
                with c_act2:
                    is_archived = item.get("status") == "archived"
                    label = "📦 Unarchive" if is_archived else "📦 Archive"
                    if st.button(label, key=f"arch_{item['id']}", use_container_width=True):
                        new_st = "active" if is_archived else "archived"
                        update_wishlist_item(item["id"], user["id"], status=new_st)
                        st.rerun()
                with c_act3:
                    with st.popover("🗑️ Delete"):
                        st.write("Are you sure?")
                        if st.button("Confirm Delete", key=f"del_{item['id']}", type="primary", use_container_width=True):
                            delete_wishlist_item(item["id"], user["id"])
                            st.rerun()


render_page()
