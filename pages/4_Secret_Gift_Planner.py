"""
Secret Gift Planner Page — TogetherList
Private, confidential gift workspace for the buyer to track purchases,
budgets, and delivery statuses. The partner CANNOT see these items until revealed.
"""

import datetime
import streamlit as st
from services.auth_service import get_current_user
from services.couple_service import get_user_couple_status
from services.gift_planning_service import (
    get_buyer_private_plans, get_buyer_spending_summary,
    reveal_secret_gift, delete_secret_plan_item, record_private_plan_item
)
from components.navigation import render_sidebar


def render_page():
    st.set_page_config(page_title="Secret Gift Planner — TogetherList", page_icon="🤫", layout="wide")
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

    if not couple_status.get("is_paired"):
        st.info("⏳ Your partner hasn't connected yet. Once connected, you can plan secret surprises for them here!")
        st.stop()
        return

    partner = couple_status["partner"]
    partner_name = partner.get("display_name", "Partner")
    couple_id = couple_status["couple_id"]

    st.title(f"🤫 Secret Gift Planner for {partner_name}")
    st.markdown(f"""
    <div style="background: #FDF2F8; border-left: 4px solid #D96B82; padding: 12px 16px; border-radius: 8px; margin-bottom: 1.5rem;">
        <h4 style="margin: 0 0 4px 0; color: #9D174D;">🔒 Strictly Confidential to You</h4>
        <p style="margin: 0; color: #831843; font-size: 0.9rem;">
            Everything on this page is private. <b>{partner_name}</b> cannot see your purchase notes, statuses, or spending.
            When you are ready to give the gift, click <b>'Reveal to Partner'</b> to unveil it.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Spending Summary Dashboard
    summary = get_buyer_spending_summary(user["id"])
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Gifts Planned", summary["total_planned_gifts"])
    with col_m2:
        st.metric("Estimated Spend", f"£{summary['total_estimated']:,.2f}")
    with col_m3:
        st.metric("Actual Spend", f"£{summary['total_actual']:,.2f}")
    with col_m4:
        purchased_count = summary["status_counts"].get("Purchased", 0) + summary["status_counts"].get("Ordered", 0) + summary["status_counts"].get("Delivered", 0)
        st.metric("Secured / Ordered", purchased_count)

    st.markdown("---")

    plans = get_buyer_private_plans(user["id"])
    active_plans = [p for p in plans if not p.get("is_revealed")]
    revealed_plans = [p for p in plans if p.get("is_revealed")]

    tab_active, tab_revealed = st.tabs([f"🤫 Active Secret Plans ({len(active_plans)})", f"🎉 Revealed Gifts ({len(revealed_plans)})"])

    with tab_active:
        if not active_plans:
            st.info(f"No active secret plans yet! Go to **👀 {partner_name}'s Wishlist** to pick items and plan surprises.")
        else:
            for plan_item in active_plans:
                w_item = plan_item.get("wishlist_items") or {}
                title = w_item.get("title", "Unknown Gift")
                img = w_item.get("image_url") or "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500&auto=format&fit=crop&q=80"
                status = plan_item.get("status", "Considering")
                notes = plan_item.get("private_notes", "")
                est_val = float(plan_item.get("estimated_spend") or 0.0)
                act_val = float(plan_item.get("actual_spend") or 0.0)

                status_colors = {
                    "Considering": "#94A3B8",
                    "Reserved": "#F59E0B",
                    "Ordered": "#3B82F6",
                    "Purchased": "#8B5CF6",
                    "Delivered": "#10B981"
                }
                s_color = status_colors.get(status, "#D96B82")

                with st.container():
                    col_img, col_info, col_actions = st.columns([1, 3, 2])
                    with col_img:
                        st.image(img, use_container_width=True)
                    with col_info:
                        st.markdown(f"### {title}")
                        st.markdown(f"""
                        <span style="background-color: {s_color}22; color: {s_color}; border: 1px solid {s_color}; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 0.82rem;">
                            ● {status}
                        </span>
                        <span style="margin-left: 10px; font-size: 0.85rem; color: #4B5563;">
                            Est: <b>£{est_val:,.2f}</b> | Actual: <b>£{act_val:,.2f}</b>
                        </span>
                        """, unsafe_allow_html=True)
                        if notes:
                            st.markdown(f"📝 *Private Note:* {notes}")
                        if w_item.get("url"):
                            st.markdown(f"[🔗 Open Product Store Page]({w_item['url']})")

                    with col_actions:
                        with st.popover("✏️ Update Status / Notes", use_container_width=True):
                            with st.form(f"upd_plan_{plan_item['id']}"):
                                n_st = st.selectbox(
                                    "Status",
                                    ["Considering", "Reserved", "Purchased", "Ordered", "Delivered"],
                                    index=["Considering", "Reserved", "Purchased", "Ordered", "Delivered"].index(status) if status in ["Considering", "Reserved", "Purchased", "Ordered", "Delivered"] else 0
                                )
                                n_notes = st.text_area("Private Notes", value=notes)
                                n_est = st.number_input("Estimated Spend (£)", min_value=0.0, value=est_val, step=5.0)
                                n_act = st.number_input("Actual Spend (£)", min_value=0.0, value=act_val, step=5.0)
                                if st.form_submit_button("Save Update"):
                                    record_private_plan_item(
                                        couple_id=couple_id,
                                        buyer_id=user["id"],
                                        partner_id=partner["id"],
                                        wishlist_item_id=plan_item["wishlist_item_id"],
                                        status=n_st,
                                        private_notes=n_notes,
                                        estimated_spend=n_est,
                                        actual_spend=n_act
                                    )
                                    st.rerun()

                        with st.popover("🎉 Reveal to Partner", use_container_width=True):
                            st.write("Ready to unveil this surprise to your partner?")
                            if st.button("Yes, Reveal Gift!", key=f"rev_{plan_item['id']}", type="primary", use_container_width=True):
                                reveal_secret_gift(user["id"], plan_item["id"])
                                st.success("Surprise revealed! 🎉")
                                st.rerun()

                        with st.popover("🗑️ Remove Plan", use_container_width=True):
                            st.write("Delete this secret intention?")
                            if st.button("Confirm Delete", key=f"del_plan_{plan_item['id']}", type="secondary", use_container_width=True):
                                delete_secret_plan_item(user["id"], plan_item["id"])
                                st.rerun()

                    st.markdown("<hr style='margin: 0.8rem 0; border: none; border-top: 1px dashed #F1E5E7;' />", unsafe_allow_html=True)

    with tab_revealed:
        if not revealed_plans:
            st.info("No gifts revealed yet. When you give a gift in person, click 'Reveal to Partner'!")
        else:
            for plan_item in revealed_plans:
                w_item = plan_item.get("wishlist_items") or {}
                title = w_item.get("title", "Unknown Gift")
                img = w_item.get("image_url") or "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500&auto=format&fit=crop&q=80"
                act_val = float(plan_item.get("actual_spend") or 0.0)

                st.markdown(f"""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <img src="{img}" style="width: 50px; height: 50px; border-radius: 8px; object-fit: cover;" />
                        <div>
                            <h4 style="margin: 0; color: #166534;">🎉 {title}</h4>
                            <span style="font-size: 0.82rem; color: #15803D;">Status: Revealed | Spent: £{act_val:,.2f}</span>
                        </div>
                    </div>
                    <span style="background: #DCFCE7; color: #166534; font-weight: 700; font-size: 0.82rem; padding: 4px 10px; border-radius: 10px;">
                        Delivered & Celebrated
                    </span>
                </div>
                """, unsafe_allow_html=True)


render_page()
