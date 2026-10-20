"""
Navigation and Header UI Component for TogetherList.
Provides top banner with couple status, avatars, and sidebar profile card.
"""

import streamlit as st
from services.auth_service import get_current_user, sign_out
from services.couple_service import get_user_couple_status
from services.supabase_client import is_supabase_configured


def render_top_header():
    """Render top brand banner with tagline and connection status."""
    st.markdown("""
    <div style="text-align: center; padding: 1.2rem 0 1.6rem 0;">
        <h1 style="font-size: 2.3rem; font-weight: 800; color: #D96B82; margin: 0; letter-spacing: -0.5px;">
            TogetherList 💕
        </h1>
        <p style="font-size: 1.05rem; color: #7B6E72; margin: 0.3rem 0 0 0; font-style: italic;">
            "Your wishlist, their perfect surprise."
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_couple_banner(user: dict, couple_status: dict):
    """Render partner connection card at the top of the dashboard."""
    my_name = user.get("display_name", "You")
    my_avatar = user.get("avatar_url") or "https://api.dicebear.com/7.x/micah/svg?seed=" + user.get("id", "user1")

    partner = couple_status.get("partner")
    is_paired = couple_status.get("is_paired", False)

    if is_paired and partner:
        p_name = partner.get("display_name", "Partner")
        p_avatar = partner.get("avatar_url") or "https://api.dicebear.com/7.x/micah/svg?seed=" + partner.get("id", "user2")

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FFF5F7 0%, #FDF2F8 100%); border: 1px solid #FBCFE8; border-radius: 16px; padding: 1rem 1.4rem; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <img src="{my_avatar}" style="width: 44px; height: 44px; border-radius: 50%; border: 2px solid #D96B82; object-fit: cover;" />
                <span style="font-size: 1.3rem;">❤️</span>
                <img src="{p_avatar}" style="width: 44px; height: 44px; border-radius: 50%; border: 2px solid #D96B82; object-fit: cover;" />
                <div>
                    <h4 style="margin: 0; color: #2D2628; font-weight: 700;">{my_name} & {p_name}</h4>
                    <span style="font-size: 0.82rem; color: #059669; font-weight: 600;">● Connected Couple Space</span>
                </div>
            </div>
            <div>
                <span style="background: #FFFFFF; border: 1px solid #FBCFE8; padding: 4px 12px; border-radius: 12px; font-size: 0.82rem; color: #D96B82; font-weight: 600;">
                    Shared Wishlist Active
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif couple_status.get("has_couple"):
        inv_code = couple_status.get("invitation_code", "PENDING")
        st.markdown(f"""
        <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 16px; padding: 1rem 1.4rem; margin-bottom: 1.5rem;">
            <h4 style="margin: 0 0 0.3rem 0; color: #92400E;">⏳ Waiting for your partner to connect...</h4>
            <p style="margin: 0; font-size: 0.9rem; color: #B45309;">
                Share your invitation code: <b style="background: #FFFFFF; padding: 3px 8px; border-radius: 6px; font-family: monospace; font-size: 1rem; color: #D96B82;">{inv_code}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar user profile and sign out controls."""
    user = get_current_user()
    if not user:
        return

    st.sidebar.markdown("---")
    my_avatar = user.get("avatar_url") or "https://api.dicebear.com/7.x/micah/svg?seed=" + user.get("id", "user1")
    my_name = user.get("display_name", "User")
    my_email = user.get("email", "")

    st.sidebar.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.8rem;">
        <img src="{my_avatar}" style="width: 38px; height: 38px; border-radius: 50%; border: 1px solid #D96B82; object-fit: cover;" />
        <div style="overflow: hidden;">
            <div style="font-weight: 600; color: #2D2628; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{my_name}</div>
            <div style="font-size: 0.78rem; color: #7B6E72; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{my_email}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Database Status Indicator
    if is_supabase_configured():
        st.sidebar.caption("⚡ Connected: Supabase Free PostgreSQL")
    else:
        st.sidebar.caption("💡 Mode: Local Demonstration Store")

    if st.sidebar.button("🚪 Sign Out", key="sidebar_sign_out_btn", use_container_width=True):
        sign_out()
        st.rerun()
