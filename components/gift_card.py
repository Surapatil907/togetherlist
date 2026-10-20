"""
Gift Card UI Component for TogetherList.
Renders romantic, rounded cards with product image, price tag, priority badge,
retailer link, and context-aware action buttons for owner vs partner.
"""

import html
import streamlit as st
from typing import Dict, Any, Callable, Optional

# Color mapping for priority badges
PRIORITY_COLORS = {
    "Must-have": {"bg": "#FFE4E6", "text": "#BE123C", "border": "#FDA4AF"},
    "Really want": {"bg": "#FCE7F3", "text": "#9D174D", "border": "#FBCFE8"},
    "Nice to have": {"bg": "#EDE9FE", "text": "#6D28D9", "border": "#DDD6FE"}
}


def render_gift_card_html(item: Dict[str, Any], is_owner: bool = True) -> str:
    """Generate modern, romantic CSS card HTML for a wishlist item."""
    title = html.escape(item.get("title", "Untitled Gift"))
    description = html.escape(item.get("description", ""))
    price = item.get("price", 0.0)
    currency_symbol = "£" if item.get("currency") == "GBP" else ("$" if item.get("currency") == "USD" else "€")
    retailer = html.escape(item.get("retailer") or "")
    url = item.get("url") or ""
    image_url = item.get("image_url") or "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500&auto=format&fit=crop&q=80"
    priority = item.get("priority", "Really want")
    category = html.escape(item.get("category", "General"))
    size = html.escape(item.get("preferred_size") or "")
    color = html.escape(item.get("preferred_color") or "")
    brand = html.escape(item.get("brand_or_model") or "")
    status = item.get("status", "active")
    date_str = (item.get("created_at") or "")[:10]

    # Occasion tag if linked
    occasion_tag = ""
    if "occasions" in item and item["occasions"]:
        occ_title = html.escape(item["occasions"].get("title", ""))
        occasion_tag = f'<span class="tl-badge tl-badge-occasion">🎉 {occ_title}</span>'

    badge_style = PRIORITY_COLORS.get(priority, PRIORITY_COLORS["Really want"])

    details_parts = []
    if brand:
        details_parts.append(f"<b>Brand:</b> {brand}")
    if size:
        details_parts.append(f"<b>Size:</b> {size}")
    if color:
        details_parts.append(f"<b>Color:</b> {color}")
    details_html = " • ".join(details_parts)

    url_link_html = ""
    if url:
        url_link_html = f'<a href="{url}" target="_blank" class="tl-product-link">🔗 View at {retailer or "Shop"}</a>'
    elif retailer:
        url_link_html = f'<span class="tl-retailer-name">🛍️ {retailer}</span>'

    status_tag = ""
    if status == "archived":
        status_tag = '<span class="tl-badge tl-badge-archived">Archived</span>'
    elif status == "no_longer_wanted":
        status_tag = '<span class="tl-badge tl-badge-archived">No Longer Wanted</span>'

    card_html = f"""
    <div class="tl-gift-card">
        <div class="tl-card-image-wrap">
            <img src="{image_url}" alt="{title}" class="tl-card-image" onerror="this.src='https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500&auto=format&fit=crop&q=80';" />
            <div class="tl-price-tag">{currency_symbol}{price:,.2f}</div>
        </div>
        <div class="tl-card-body">
            <div class="tl-badges-row">
                <span class="tl-badge" style="background-color: {badge_style['bg']}; color: {badge_style['text']}; border: 1px solid {badge_style['border']};">
                    ★ {priority}
                </span>
                <span class="tl-badge tl-badge-category">{category}</span>
                {occasion_tag}
                {status_tag}
            </div>
            <h3 class="tl-card-title">{title}</h3>
            {f'<p class="tl-card-description">{description}</p>' if description else ''}
            {f'<p class="tl-card-details">{details_html}</p>' if details_html else ''}
            <div class="tl-card-footer">
                {url_link_html}
                <span class="tl-date-added">Added {date_str}</span>
            </div>
        </div>
    </div>
    """
    return card_html


def render_card_styles():
    """Inject custom CSS for TogetherList gift cards and layout."""
    st.markdown("""
    <style>
    .tl-gift-card {
        background: #FFFFFF;
        border-radius: 18px;
        border: 1px solid #F1E5E7;
        box-shadow: 0 4px 14px rgba(217, 107, 130, 0.08);
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .tl-gift-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(217, 107, 130, 0.15);
    }
    .tl-card-image-wrap {
        position: relative;
        width: 100%;
        height: 200px;
        background-color: #FAF4F2;
        overflow: hidden;
    }
    .tl-card-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .tl-price-tag {
        position: absolute;
        bottom: 12px;
        right: 12px;
        background: rgba(255, 255, 255, 0.95);
        color: #B83253;
        font-weight: 700;
        font-size: 1.05rem;
        padding: 4px 12px;
        border-radius: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(4px);
    }
    .tl-card-body {
        padding: 1rem 1.2rem;
        flex: 1;
        display: flex;
        flex-direction: column;
    }
    .tl-badges-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 0.6rem;
    }
    .tl-badge {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 12px;
        display: inline-block;
    }
    .tl-badge-category {
        background-color: #F3F4F6;
        color: #4B5563;
        border: 1px solid #E5E7EB;
    }
    .tl-badge-occasion {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .tl-badge-archived {
        background-color: #F1F5F9;
        color: #64748B;
        border: 1px solid #CBD5E1;
    }
    .tl-card-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #2D2628;
        margin: 0 0 0.4rem 0;
        line-height: 1.3;
    }
    .tl-card-description {
        font-size: 0.88rem;
        color: #5C5255;
        line-height: 1.4;
        margin-bottom: 0.5rem;
    }
    .tl-card-details {
        font-size: 0.8rem;
        color: #7B6E72;
        margin-bottom: 0.5rem;
    }
    .tl-card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: auto;
        padding-top: 0.6rem;
        border-top: 1px solid #F7ECEE;
    }
    .tl-product-link {
        font-size: 0.82rem;
        color: #D96B82;
        font-weight: 600;
        text-decoration: none;
    }
    .tl-product-link:hover {
        text-decoration: underline;
    }
    .tl-retailer-name {
        font-size: 0.82rem;
        color: #7B6E72;
        font-weight: 500;
    }
    .tl-date-added {
        font-size: 0.75rem;
        color: #A09497;
    }
    </style>
    """, unsafe_allow_html=True)
