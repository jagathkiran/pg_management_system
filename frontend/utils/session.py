import streamlit as st
from typing import Optional, Dict, Any

def init_session():
    """Initializes session state variables if they don't exist."""
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = None
    if 'token' not in st.session_state:
        st.session_state['token'] = None
    if 'user' not in st.session_state:
        st.session_state['user'] = {}
    if 'role' not in st.session_state:
        st.session_state['role'] = None

def login_user(token: str, user_data: Dict[str, Any]):
    """Sets the session state for a logged-in user."""
    st.session_state['authentication_status'] = True
    st.session_state['token'] = token
    st.session_state['user'] = user_data
    # Assuming user_data has 'role' field.
    st.session_state['role'] = user_data.get('role')

def logout_user():
    """Clears the session state to log out the user."""
    st.session_state['authentication_status'] = None
    st.session_state['token'] = None
    st.session_state['user'] = {}
    st.session_state['role'] = None
    
    # Rerun to update UI immediately
    st.rerun()

def get_token() -> Optional[str]:
    """Returns the current access token."""
    return st.session_state.get('token')

def get_user_role() -> Optional[str]:
    """Returns the current user's role."""
    return st.session_state.get('role')

def is_authenticated() -> bool:
    """Checks if the user is authenticated."""
    return st.session_state.get('authentication_status') is True
