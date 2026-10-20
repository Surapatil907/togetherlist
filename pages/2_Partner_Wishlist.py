"""
Partner's Wishlist Page — TogetherList
Allows the user to view their partner's wishlist, browse gift details,
and privately record purchase intentions without the partner seeing.
"""

import datetime
import streamlit as st
from services.auth_service import get_current_user
from services.couple_service import get_user_couple_status
from services.wishlist_service import get_wishlist_items
from services.gift_planning_service import record_private_plan_item, get_buyer_private_plans
from components.gift_card import render_card_styles, render_gift_card_html
from components.navigation import render_sidebar


def render_page():
    st.set_page_config(page_title="Partner's Wishlist — TogetherList", page_icon="👀", layout="wide")
    render_card_styles()
    render_sidebar()

    user = get_current_user()
    if not user:
        st.warning("Please log in on the Home page to view your partner's wishlist.")
        st.stop()
        return

    couple_status = get_user_couple_status(user["id"])
    if not couple_status.get("has_couple"):
        st.warning("Please create or join a couple space on the Home page first.")
        st.stop()
        return

    if not couple_status.get("is_paired"):
        st.info("⏳ Your partner hasn't connected to your couple space yet. Once they join, their wishlist will appear here!")
        st.stop()
        return

    partner = couple_status["partner"]
    partner_id = partner["id"]
    partner_name = partner.get("display_name", "Partner")
    couple_id = couple_status["couple_id"]

    st.title(f"👀 {partner_name}'s Wishlist")
    st.markdown(f"Browse what **{partner_name}** is wishing for. You can privately mark items you plan to buy — they will never see your secret plans!")

    # Fetch buyer's existing secret plans to show subtle indicators
    buyer_plans = get_buyer_private_plans(user["id"])
    planned_item_ids = {p.get("wishlist_item_id"): p for p in buyer_plans}

    # --- SEARCH, FILTERS & SORTING ---
    col_search, col_cat, col_prio, col_sort = st.columns([2, 1.2, 1.2, 1.2])
    with col_search:
        search_q = st.text_input("🔍 Search partner's gifts", placeholder="Title, brand, retailer...")
    with col_cat:
        cat_filter = st.selectbox("Category", ["All", "Fashion & Clothing", "Tech & Gadgets", "Books & Stationery", "Home & Kitchen", "Experiences & Dates", "Fragrance & Beauty", "Jewellery & Watches", "General"])
    with col_prio:
        prio_filter = st.selectbox("Priority", ["All", "Must-have", "Really want", "Nice to have"])
    with col_sort:
        sort_filter = st.selectbox("Sort By", ["Newest First", "Oldest First", "Price: Low to High", "Price: High to Low"])

    sort_map = {
        "Newest First": "date_desc",
        "Oldest First": "date_asc",
        "Price: Low to High": "price_asc",
        "Price: High to Low": "price_desc"
    }

    items = get_wishlist_items(
        couple_id=couple_id,
        user_id=partner_id,
        category=cat_filter,
        priority=prio_filter,
        status="active",
        search_query=search_q,
        sort_by=sort_map[sort_filter]
    )

    if not items:
        st.info(f"{partner_name} hasn't added any active items to their wishlist yet. Check back soon!")
    else:
        st.caption(f"Showing {len(items)} gift{'s' if len(items) != 1 else ''} on {partner_name}'s wishlist")

        cols_grid = st.columns(3)
        for idx, item in enumerate(items):
            col = cols_grid[idx % 3]
            with col:
                st.markdown(render_gift_card_html(item, is_owner=False), unsafe_allow_html=True)

                existing_plan = planned_item_ids.get(item["id"])
                if existing_plan:
                    st_val = existing_plan.get("status", "Considering")
                    st.markdown(f"""
                    <div style="background: #FDF2F8; border: 1px solid #FBCFE8; padding: 4px 10px; border-radius: 10px; margin-bottom: 6px; font-size: 0.8rem; color: #9D174D; font-weight: 600;">
                        🤫 Secret Status: {st_val}
                    </div>
                    """, unsafe_allow_html=True)

                with st.popover("🤫 Plan Secret Surprise", use_container_width=True):
                    st.markdown(f"**Private Plan for: {item['title']}**")
                    st.caption("🔒 100% Private: Your partner CANNOT see these notes or status.")

                    cur_status = existing_plan.get("status", "Considering") if existing_plan else "Considering"
                    cur_notes = existing_plan.get("private_notes", "") if existing_plan else ""
                    cur_est = float(existing_plan.get("estimated_spend") or item.get("price", 0.0)) if existing_plan else float(item.get("price", 0.0))
                    cur_act = float(existing_plan.get("actual_spend") or 0.0) if existing_plan else 0.0

                    with st.form(f"plan_form_{item['id']}"):
                        new_status = st.selectbox(
                            "My Private Status",
                            ["Considering", "Reserved", "Purchased", "Ordered", "Delivered"],
                            index=["Considering", "Reserved", "Purchased", "Ordered", "Delivered"].index(cur_status) if cur_status in ["Considering", "Reserved", "Purchased", "Ordered", "Delivered"] else 0
                        )
                        new_notes = st.text_area("Private Notes (Tracking, order no, sizing)", value=cur_notes)
                        col_p1, col_p2 = st.columns(2)
                        with col_p1:
                            est_spend = st.number_input("Estimated Spend (£)", min_value=0.0, value=cur_est, step=5.0)
                        with col_p2:
                            act_spend = st.number_input("Actual Spend (£)", min_value=0.0, value=cur_act, step=5.0)

                        save_plan = st.form_submit_button("🔒 Save Private Intention", use_container_width=True)
                        if save_plan:
                            p_res = record_private_plan_item(
                                couple_id=couple_id,
                                buyer_id=user["id"],
                                partner_id=partner_id,
                                wishlist_item_id=item["id"],
                                status=new_status,
                                private_notes=new_notes,
                                estimated_spend=est_spend,
                                actual_spend=act_spend
                            )
                            if p_res.get("success"):
                                st.success("Private plan saved!")
                                st.rerun()
                            else:
                                st.error(p_res.get("error"))


render_page()
