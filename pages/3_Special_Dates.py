"""
Special Dates Page — TogetherList
Manage birthdays, anniversaries, holiday countdowns, and celebration budgets.
"""

import datetime
import streamlit as st
from services.auth_service import get_current_user
from services.couple_service import get_user_couple_status
from services.occasion_service import (
    get_couple_occasions, add_occasion, delete_occasion
)
from services.wishlist_service import get_wishlist_items
from components.navigation import render_sidebar


def render_page():
    st.set_page_config(page_title="Special Dates — TogetherList", page_icon="📅", layout="wide")
    render_sidebar()

    user = get_current_user()
    if not user:
        st.warning("Please log in on the Home page first.")
        st.stop()
        return

    couple_status = get_user_couple_status(user["id"])
    if not couple_status.get("has_couple"):
        st.warning("Please connect to a couple space on the Home page first.")
        st.stop()
        return

    couple_id = couple_status["couple_id"]

    st.title("📅 Special Dates & Celebrations")
    st.markdown("Track your relationship milestones, birthdays, holidays, and countdowns together.")

    # --- ADD OCCASION FORM ---
    with st.expander("➕ Add an Occasion or Celebration", expanded=False):
        with st.form("add_occasion_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Occasion Title *", placeholder="e.g. Our 3rd Anniversary, Sarah's Birthday")
                occ_type = st.selectbox("Type", ["anniversary", "birthday", "valentines", "christmas", "custom"], format_func=lambda x: {
                    "anniversary": "💍 Relationship Anniversary",
                    "birthday": "🎂 Birthday",
                    "valentines": "💖 Valentine's Day",
                    "christmas": "🎄 Christmas",
                    "custom": "✨ Custom Special Occasion"
                }.get(x, x))
                event_date = st.date_input("Date *", value=datetime.date.today())
            with col2:
                is_recurring = st.checkbox("Repeat Annually (Every Year)", value=True)
                budget = st.number_input("Target Celebration Budget (£ GBP, Optional)", min_value=0.0, value=0.0, step=25.0)
                desc = st.text_area("Notes / Traditions", placeholder="e.g. Book our favourite restaurant, gift exchange at sunset")

            submitted = st.form_submit_button("✨ Save Special Date", use_container_width=True)
            if submitted:
                if not title.strip():
                    st.error("Occasion Title is required.")
                else:
                    res = add_occasion(
                        couple_id=couple_id,
                        created_by=user["id"],
                        title=title,
                        event_date=event_date,
                        is_recurring=is_recurring,
                        occasion_type=occ_type,
                        description=desc,
                        budget=budget if budget > 0 else None
                    )
                    if res.get("success"):
                        st.success("🎉 Added special date!")
                        st.rerun()
                    else:
                        st.error(res.get("error"))

    st.markdown("---")

    occasions = get_couple_occasions(couple_id)

    if not occasions:
        st.info("No special dates added yet. Add your birthday or anniversary above!")
    else:
        st.subheader(f"Upcoming Celebrations ({len(occasions)})")

        for occ in occasions:
            days = occ.get("days_remaining", 0)
            next_date = occ.get("next_occurrence")
            budget_val = occ.get("budget")

            if days == 0:
                badge_text = "🎉 TODAY! Happy Celebration! 🎉"
                badge_bg = "#FEF3C7"
                badge_color = "#92400E"
            elif days > 0 and days <= 14:
                badge_text = f"⏳ In {days} day{'s' if days != 1 else ''}! Coming up soon!"
                badge_bg = "#FFE4E6"
                badge_color = "#BE123C"
            elif days > 0:
                badge_text = f"🗓️ In {days} days ({next_date})"
                badge_bg = "#F3F4F6"
                badge_color = "#374151"
            else:
                badge_text = f"Passed {abs(days)} days ago"
                badge_bg = "#F1F5F9"
                badge_color = "#64748B"

            occ_type_icons = {
                "anniversary": "💍",
                "birthday": "🎂",
                "valentines": "💖",
                "christmas": "🎄",
                "custom": "✨"
            }
            icon = occ_type_icons.get(occ.get("occasion_type"), "🎉")

            col_left, col_right = st.columns([4, 1])
            with col_left:
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #F1E5E7; border-radius: 14px; padding: 1.1rem 1.3rem; margin-bottom: 0.8rem; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h4 style="margin: 0 0 0.3rem 0; color: #2D2628;">{icon} {occ['title']}</h4>
                            <span style="background: {badge_bg}; color: {badge_color}; font-size: 0.85rem; font-weight: 700; padding: 4px 10px; border-radius: 12px; display: inline-block;">
                                {badge_text}
                            </span>
                            {f'<span style="margin-left: 8px; font-size: 0.82rem; color: #7B6E72;">💰 Budget: £{budget_val:,.2f}</span>' if budget_val else ''}
                            {f'<span style="margin-left: 8px; font-size: 0.82rem; color: #059669;">🔁 Annual Recurrence</span>' if occ.get("is_recurring") else ''}
                        </div>
                    </div>
                    {f'<p style="margin: 0.6rem 0 0 0; font-size: 0.9rem; color: #5C5255;">{occ.get("description", "")}</p>' if occ.get("description") else ''}
                </div>
                """, unsafe_allow_html=True)

            with col_right:
                with st.popover("⚙️ Options"):
                    if st.button("Delete Occasion", key=f"del_occ_{occ['id']}", type="primary", use_container_width=True):
                        delete_occasion(occ["id"], couple_id)
                        st.rerun()


render_page()
