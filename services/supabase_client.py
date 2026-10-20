"""
Supabase Client Management for TogetherList.
Handles client initialization, session-scoped client instances for Streamlit,
and local fallback store for seamless demonstration and testing without API credentials.
"""

import os
from typing import Optional, Tuple
import streamlit as st
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()


def get_supabase_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Retrieve Supabase URL and Anon Key from Streamlit secrets or OS environment."""
    url = None
    key = None

    # Check Streamlit secrets first
    try:
        if hasattr(st, "secrets"):
            if "SUPABASE_URL" in st.secrets:
                url = st.secrets["SUPABASE_URL"]
            elif "supabase" in st.secrets and "url" in st.secrets["supabase"]:
                url = st.secrets["supabase"]["url"]

            if "SUPABASE_KEY" in st.secrets:
                key = st.secrets["SUPABASE_KEY"]
            elif "supabase" in st.secrets and "key" in st.secrets["supabase"]:
                key = st.secrets["supabase"]["key"]
    except Exception:
        pass

    # Fall back to environment variables
    if not url:
        url = os.getenv("SUPABASE_URL")
    if not key:
        key = os.getenv("SUPABASE_KEY")

    return url, key


def is_supabase_configured() -> bool:
    """Check if valid Supabase credentials are provided."""
    url, key = get_supabase_credentials()
    if not url or not key:
        return False
    # Check if placeholder from .env.example
    if "your-project-id" in url or "your_anon_key_here" in key:
        return False
    return True


def get_supabase_client():
    """
    Get or create a Supabase client instance scoped to the current user's session.
    Using session_state ensures that auth state and tokens are isolated per browser tab.
    """
    if not is_supabase_configured():
        return None

    if "supabase_client" not in st.session_state:
        from supabase import create_client

        url, key = get_supabase_credentials()
        st.session_state.supabase_client = create_client(url, key)

    return st.session_state.supabase_client


def reset_session_client():
    """Reset the Supabase client in session state on logout."""
    if "supabase_client" in st.session_state:
        del st.session_state.supabase_client
