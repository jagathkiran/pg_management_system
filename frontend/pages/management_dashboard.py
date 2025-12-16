import streamlit as st
import sys
import os

# Add parent directory to path to allow imports from components and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamlit_option_menu import option_menu
from utils.session import logout_user, init_session, is_authenticated, get_token
from utils.api_client import APIClient
from utils.ui import hide_sidebar_nav
from components.room_management import render_room_management
from components.tenant_management import render_tenant_management
from components.rent_collection import render_rent_collection
from components.maintenance_mgmt import render_maintenance_mgmt
from components.financial_dashboard import render_financial_dashboard
import os

# Page config must be the first Streamlit command
st.set_page_config(page_title="Admin Dashboard", layout="wide", page_icon="🏢")

def show_dashboard():
    init_session()
    hide_sidebar_nav()
    
    # Security check
    if not is_authenticated():
        st.switch_page("pages/login.py")
        return
        
    # Double check role (optional but good)
    if st.session_state.get('role') != 'admin':
        st.error("Unauthorized access.")
        if st.button("Go to Login"):
             st.switch_page("pages/login.py")
        return

    # Initialize API Client
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api")
    client = APIClient(base_url=api_base_url)
    token = get_token()
    if token:
        client.set_token(token)

    # Sidebar Navigation
    with st.sidebar:
        st.title("PG Management")
        user = st.session_state.get('user', {})
        st.write(f"Admin: **{user.get('email', 'Unknown')}**")
        
        selected = option_menu(
            "Menu",
            ["Overview", "Rooms", "Tenants", "Payments", "Maintenance"],
            icons=["house", "door-open", "people", "cash", "tools"],
            menu_icon="cast",
            default_index=0,
            styles={
                "nav-link-selected": {"background-color": "#ff4b4b"},
            }
        )
        
        st.divider()
        if st.button("Logout", type="primary", use_container_width=True):
            logout_user()
            st.switch_page("pages/login.py")

    # Main Content Routing
    if selected == "Overview":
        render_financial_dashboard(client)
        
    elif selected == "Rooms":
        render_room_management(client)
        
    elif selected == "Tenants":
        render_tenant_management(client)
        
    elif selected == "Payments":
        render_rent_collection(client)
        
    elif selected == "Maintenance":
        render_maintenance_mgmt(client)

if __name__ == "__main__":
    show_dashboard()