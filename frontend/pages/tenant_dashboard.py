import streamlit as st
from streamlit_option_menu import option_menu
from utils.session import logout_user, init_session, is_authenticated, get_token
from utils.api_client import APIClient
import os

# Components
from components.tenant_profile import render_tenant_profile
from components.payment_submission import render_payment_submission
from components.maintenance_request import render_maintenance_request
from components.notifications import render_notifications

st.set_page_config(page_title="Tenant Dashboard", layout="wide", page_icon="🏠")

def show_dashboard():
    init_session()
    
    if not is_authenticated():
        st.switch_page("pages/login.py")
        return

    # Check Role
    if st.session_state.get('role') != 'tenant':
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

    # Refresh User Data to get Tenant Info if missing
    user = st.session_state.get('user', {})
    # Always try to fetch fresh user data to get latest tenant info
    try:
        user_data = client.get("auth/me")
        if user_data:
            st.session_state['user'] = user_data
            user = user_data
    except:
        pass
            
    # Sidebar
    with st.sidebar:
        st.title("My Home")
        tenant_name = user.get('tenant', {}).get('full_name') if user.get('tenant') else user.get('email')
        st.write(f"Welcome, **{tenant_name}**")
        
        selected = option_menu(
            "Menu",
            ["Profile", "Pay Rent", "Maintenance", "Notifications"],
            icons=["person", "credit-card", "tools", "bell"],
            menu_icon="cast",
            default_index=0,
             styles={
                "nav-link-selected": {"background-color": "#4b7bff"},
            }
        )
        
        st.divider()
        if st.button("Logout", type="primary", use_container_width=True):
            logout_user()
            st.switch_page("pages/login.py")

    # Routing
    if selected == "Profile":
        render_tenant_profile(client, user)
        
    elif selected == "Pay Rent":
        render_payment_submission(client, user)
        
    elif selected == "Maintenance":
        render_maintenance_request(client, user)
        
    elif selected == "Notifications":
        render_notifications(client, user)

if __name__ == "__main__":
    show_dashboard()