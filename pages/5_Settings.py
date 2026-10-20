"""
Settings Page — TogetherList
User profile management, couple space information, invitation sharing, and couple disconnection.
"""

import streamlit as st
from services.auth_service import get_current_user, update_profile, sign_out
from services.couple_service import get_user_couple_status, disconnect_couple
from components.navigation import render_sidebar


def render_page():
    st.set_page_config(page_title="Settings — TogetherList", page_icon="⚙️", layout="wide")
    render_sidebar()

    user = get_current_user()
    if not user:
        st.warning("Please log in on the Home page first.")
        st.stop()
        return

    couple_status = get_user_couple_status(user["id"])

    st.title("⚙️ Account & Space Settings")

    tab_profile, tab_couple, tab_info = st.tabs(["👤 Profile", "💕 Couple Space", "ℹ️ Database & Privacy"])

    with tab_profile:
        st.subheader("Your Profile")
        with st.form("profile_form"):
            disp_name = st.text_input("Display Name", value=user.get("display_name", ""))
            avatar_url = st.text_input("Avatar Image URL", value=user.get("avatar_url", ""), placeholder="https://example.com/avatar.jpg")
            col_sub, _ = st.columns([1, 3])
            with col_sub:
                save_btn = st.form_submit_button("Save Profile Changes", use_container_width=True)
            if save_btn:
                res = update_profile(disp_name, avatar_url)
                if res.get("success"):
                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    st.error(res.get("error"))

        if user.get("avatar_url"):
            st.markdown(f"""
            <div style="margin-top: 1rem;">
                <b>Avatar Preview:</b><br/>
                <img src="{user['avatar_url']}" style="width: 72px; height: 72px; border-radius: 50%; border: 2px solid #D96B82; object-fit: cover; margin-top: 6px;" />
            </div>
            """, unsafe_allow_html=True)

    with tab_couple:
        st.subheader("Couple Space Settings")
        if not couple_status.get("has_couple"):
            st.info("You are not currently connected to any couple space. Go to the Home page to create or join one!")
        else:
            couple = couple_status.get("couple") or {}
            partner = couple_status.get("partner")
            inv_code = couple_status.get("invitation_code")
            couple_id = couple_status["couple_id"]

            st.markdown(f"**Space Name:** {couple.get('name', 'Our Couple Space')}")
            st.markdown(f"**Status:** {'Connected with Partner ❤️' if partner else 'Waiting for Partner ⏳'}")

            if partner:
                st.markdown(f"**Connected Partner:** {partner.get('display_name', 'Partner')}")
            elif inv_code:
                st.markdown(f"**Pending Invitation Code:** `{inv_code}`")
                st.caption("Share this code with your partner so they can join your space.")

            st.markdown("---")
            st.subheader("⚠️ Disconnect Couple Space")
            st.write("Disconnecting will remove your shared access to this space and archive your pairing.")

            with st.popover("💔 Disconnect from Couple Space"):
                st.error("Are you completely sure you want to disconnect?")
                confirm = st.checkbox("Yes, I understand and want to disconnect.")
                if st.button("Confirm Disconnect", type="primary", disabled=not confirm):
                    d_res = disconnect_couple(user["id"], couple_id)
                    if d_res.get("success"):
                        st.success("Disconnected. Redirecting...")
                        st.session_state.pop("couple_info", None)
                        st.rerun()
                    else:
                        st.error(d_res.get("error"))

    with tab_info:
        st.subheader("Free Infrastructure & Privacy Guarantees")
        st.markdown("""
        - **PostgreSQL Database:** Supabase Free Tier with Row Level Security (RLS).
        - **Authentication:** Supabase Auth (or isolated local session).
        - **Product Images:** Supabase Storage bucket (`wishlist-images`).
        - **Secret Purchase Isolation:** Recipient has zero access to buyer notes, budgets, or purchase status until deliberately revealed by the buyer.
        - **Privacy:** Invitations cannot be reused, self-joined, or claimed by unauthorized third parties.
        """)


render_page()
