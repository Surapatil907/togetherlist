"""
TogetherList — A Free Personal Gift Wishlist App for Couples
Main application entry point, authentication flow, couple connection,
and couple dashboard.
"""

import streamlit as st
from services.auth_service import (
    sign_in, sign_up, reset_password, get_current_user, sign_out
)
from services.couple_service import (
    create_couple_space, join_couple_with_code, get_user_couple_status
)
from services.wishlist_service import get_wishlist_items
from services.occasion_service import get_next_upcoming_occasion, get_couple_occasions
from components.gift_card import render_card_styles, render_gift_card_html
from components.navigation import render_top_header, render_couple_banner, render_sidebar

# Configure page
st.set_page_config(
    page_title="TogetherList — Couples Gift Wishlist",
    page_icon="💕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styling
render_card_styles()
render_sidebar()

# Check authentication
user = get_current_user()


def render_unauthenticated():
    """Render landing page with login and registration forms."""
    render_top_header()

    col_hero, col_auth = st.columns([1.1, 1], gap="large")

    with col_hero:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #F7ECEE; border-radius: 20px; padding: 2rem; box-shadow: 0 4px 20px rgba(217, 107, 130, 0.08);">
            <h2 style="color: #2D2628; font-weight: 800; font-size: 1.8rem; margin-top: 0;">
                Share Wishlists, Create Beautiful Surprises
            </h2>
            <p style="color: #5C5255; font-size: 1.05rem; line-height: 1.6;">
                TogetherList is a private, ad-free wishlist space designed exclusively for couples.
                Say goodbye to awkward guessing and duplicate gifts:
            </p>
            <ul style="color: #5C5255; font-size: 0.98rem; line-height: 1.8; padding-left: 1.2rem;">
                <li>🎁 <b>Personal Wishlists:</b> Curate items with photos, sizes, links, and priorities.</li>
                <li>🤫 <b>Secret Gift Planner:</b> Reserve and track gifts privately without spoiling the surprise.</li>
                <li>📅 <b>Special Dates:</b> Milestone countdowns for birthdays and anniversaries.</li>
                <li>🔒 <b>100% Private & Free:</b> Powered securely by Supabase PostgreSQL and Storage.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_auth:
        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Sign In", "✨ Create Account", "🔄 Forgot Password"])

        # TAB 1: SIGN IN
        with auth_tab1:
            with st.form("signin_form"):
                st.subheader("Welcome Back")
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if submit:
                    res = sign_in(email, password)
                    if res.get("success"):
                        st.success("Signed in successfully!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Sign in failed."))

        # TAB 2: REGISTER
        with auth_tab2:
            with st.form("signup_form"):
                st.subheader("Join TogetherList")
                reg_name = st.text_input("Your Display Name *", placeholder="e.g. Suraj, Emma")
                reg_email = st.text_input("Email Address *", placeholder="you@example.com")
                reg_pass = st.text_input("Choose Password (min 6 characters) *", type="password")
                reg_avatar = st.text_input("Avatar Photo URL (Optional)", placeholder="https://...")
                submit_reg = st.form_submit_button("Create Free Account", use_container_width=True, type="primary")

                if submit_reg:
                    res = sign_up(reg_email, reg_pass, reg_name, reg_avatar)
                    if res.get("success"):
                        st.success("Account created successfully! Welcome to TogetherList 💕")
                        st.rerun()
                    else:
                        st.error(res.get("error"))

        # TAB 3: RESET PASSWORD
        with auth_tab3:
            with st.form("reset_form"):
                st.subheader("Reset Your Password")
                rst_email = st.text_input("Enter your account email", placeholder="you@example.com")
                submit_rst = st.form_submit_button("Send Reset Link", use_container_width=True)

                if submit_rst:
                    res = reset_password(rst_email)
                    if res.get("success"):
                        st.success(res.get("message"))
                    else:
                        st.error(res.get("error"))


def render_couple_creation(current_user):
    """Render options to create a couple space or join using an invitation code."""
    render_top_header()
    st.markdown(f"### Welcome, **{current_user.get('display_name')}**! 💕")
    st.markdown("To start sharing wishlists, connect with your partner by creating a new couple space or joining an existing one.")

    col_create, col_join = st.columns(2, gap="large")

    with col_create:
        with st.container(border=True):
            st.subheader("Create a New Couple Space")
            st.write("Start a fresh private space and generate an invitation code to share with your partner.")
            c_name = st.text_input("Couple Space Name", value="Our Couple Space")
            if st.button("✨ Create Space & Invite Partner", type="primary", use_container_width=True):
                res = create_couple_space(current_user["id"], c_name)
                if res.get("success"):
                    st.success("Couple space created!")
                    st.rerun()
                else:
                    st.error(res.get("error"))

    with col_join:
        with st.container(border=True):
            st.subheader("Join Partner's Space")
            st.write("If your partner already created a couple space and gave you an invitation code, enter it below:")
            code_input = st.text_input("Invitation Code", placeholder="TOGETHER-XXXXXX")
            if st.button("🤝 Connect with Partner", use_container_width=True):
                res = join_couple_with_code(current_user["id"], code_input)
                if res.get("success"):
                    st.success("Connected with your partner!")
                    st.rerun()
                else:
                    st.error(res.get("error"))


def render_waiting_room(current_user, couple_status):
    """Render waiting room while partner has not yet joined."""
    render_top_header()
    render_couple_banner(current_user, couple_status)

    inv_code = couple_status.get("invitation_code")
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 2px dashed #FBCFE8; border-radius: 18px; padding: 2.2rem; text-align: center; margin: 1.5rem auto; max-width: 650px;">
        <span style="font-size: 3rem;">💌</span>
        <h2 style="color: #2D2628; margin: 0.5rem 0;">Waiting for your partner to connect</h2>
        <p style="color: #5C5255; font-size: 1rem; line-height: 1.5;">
            Send this invitation code to your partner. When they log in and enter this code,
            your spaces will be permanently paired!
        </p>
        <div style="background: #FFF5F7; border: 1px solid #FDA4AF; border-radius: 12px; padding: 12px 20px; display: inline-block; margin: 1rem 0;">
            <code style="font-size: 1.6rem; font-weight: 800; color: #BE123C; letter-spacing: 2px;">{inv_code}</code>
        </div>
        <p style="font-size: 0.85rem; color: #7B6E72;">
            Valid for 7 days. Only 1 partner can join using this code.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_btn, _ = st.columns([1, 2])
    with col_btn:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()

    st.markdown("---")
    st.info("💡 **Tip:** While waiting, you can already start curating items on **🎁 My Wishlist** via the sidebar!")


def render_dashboard(current_user, couple_status):
    """Render the full couple dashboard when paired."""
    render_top_header()
    render_couple_banner(current_user, couple_status)

    partner = couple_status["partner"]
    partner_name = partner.get("display_name", "Partner")
    couple_id = couple_status["couple_id"]

    # Fetch Dashboard Data
    my_items = get_wishlist_items(couple_id, current_user["id"], status="active")
    partner_items = get_wishlist_items(couple_id, partner["id"], status="active")
    next_occ = get_next_upcoming_occasion(couple_id)

    my_total_value = sum(float(i.get("price") or 0.0) for i in my_items)
    partner_total_value = sum(float(i.get("price") or 0.0) for i in partner_items)

    # Top Metrics Row
    st.subheader("Overview")
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric(label="My Wishlist Items", value=len(my_items))
    with col_stat2:
        st.metric(label=f"{partner_name}'s Wishlist Items", value=len(partner_items))
    with col_stat3:
        st.metric(label="My Wishlist Total Value", value=f"£{my_total_value:,.2f}")
    with col_stat4:
        st.metric(label=f"{partner_name}'s Total Value", value=f"£{partner_total_value:,.2f}")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Next Upcoming Occasion Banner
    if next_occ:
        occ_days = next_occ.get("days_remaining", 0)
        occ_title = next_occ.get("title", "")
        occ_date = next_occ.get("next_occurrence")
        occ_budget = next_occ.get("budget")

        if occ_days == 0:
            day_str = "TODAY! 🎉"
            bg_color = "#FEF3C7"
            text_color = "#92400E"
        elif occ_days > 0:
            day_str = f"in {occ_days} day{'s' if occ_days != 1 else ''} ({occ_date})"
            bg_color = "#FFF5F7"
            text_color = "#BE123C"
        else:
            day_str = f"{abs(occ_days)} days ago"
            bg_color = "#F3F4F6"
            text_color = "#4B5563"

        st.markdown(f"""
        <div style="background: {bg_color}; border: 1px solid #FBCFE8; border-radius: 14px; padding: 1.1rem 1.4rem; margin-bottom: 1.8rem; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span style="font-size: 0.85rem; font-weight: 700; color: {text_color}; text-transform: uppercase; letter-spacing: 0.5px;">Upcoming Celebration</span>
                <h3 style="margin: 0.2rem 0; color: #2D2628;">🎉 {occ_title}</h3>
                <span style="font-size: 0.95rem; color: #5C5255; font-weight: 600;">Countdown: {day_str}</span>
                {f'<span style="margin-left: 12px; font-size: 0.88rem; color: #7B6E72;">Target Budget: £{occ_budget:,.2f}</span>' if occ_budget else ''}
            </div>
            <div>
                <a href="/Special_Dates" target="_self" style="background: #FFFFFF; color: #D96B82; font-weight: 700; font-size: 0.88rem; padding: 8px 16px; border-radius: 12px; border: 1px solid #FBCFE8; text-decoration: none;">
                    View All Dates →
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Quick Navigation / Action Row
    st.subheader("Quick Actions")
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("➕ Add Gift to My List", use_container_width=True, type="primary"):
            st.switch_page("pages/1_My_Wishlist.py")
    with qa2:
        if st.button(f"👀 Browse {partner_name}'s List", use_container_width=True):
            st.switch_page("pages/2_Partner_Wishlist.py")
    with qa3:
        if st.button("🤫 Secret Gift Planner", use_container_width=True):
            st.switch_page("pages/4_Secret_Gift_Planner.py")
    with qa4:
        if st.button("📅 Add Special Occasion", use_container_width=True):
            st.switch_page("pages/3_Special_Dates.py")

    st.markdown("---")

    # Recently Added Gifts (Split View)
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.subheader(f"✨ {partner_name}'s Recent Wishes")
        if not partner_items:
            st.info(f"{partner_name} hasn't added any gifts yet.")
        else:
            for it in partner_items[:2]:
                st.markdown(render_gift_card_html(it, is_owner=False), unsafe_allow_html=True)
            if len(partner_items) > 2:
                if st.button(f"View all {len(partner_items)} gifts from {partner_name} →", key="view_all_partner"):
                    st.switch_page("pages/2_Partner_Wishlist.py")

    with col_right:
        st.subheader("✨ My Recent Wishes")
        if not my_items:
            st.info("You haven't added any gifts yet. Add your favourite products!")
        else:
            for it in my_items[:2]:
                st.markdown(render_gift_card_html(it, is_owner=True), unsafe_allow_html=True)
            if len(my_items) > 2:
                if st.button(f"View all {len(my_items)} gifts in my list →", key="view_all_my"):
                    st.switch_page("pages/1_My_Wishlist.py")


# Routing logic
if not user:
    render_unauthenticated()
else:
    couple_status = get_user_couple_status(user["id"])
    if not couple_status.get("has_couple"):
        render_couple_creation(user)
    elif not couple_status.get("is_paired"):
        render_waiting_room(user, couple_status)
    else:
        render_dashboard(user, couple_status)
