import streamlit as st
import sys
import os

# Add current directory to path to allow imports from utils
sys.path.append(os.path.dirname(__file__))

from utils.session import init_session, is_authenticated, get_user_role
from utils.api_client import APIClient
import os

# Page Configuration
st.set_page_config(
    page_title="PG Management System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API Client
api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api")
api_client = APIClient(base_url=api_base_url)

def main():
    init_session()
    
    # Routing
    if not is_authenticated():
        st.switch_page("pages/login.py")
    else:
        role = get_user_role()
        if role == "admin":
            st.switch_page("pages/management_dashboard.py")
        elif role == "tenant":
            st.switch_page("pages/tenant_dashboard.py")
        else:
            st.error(f"Unknown user role: {role}")
            if st.button("Logout"):
                from utils.session import logout_user
                logout_user()
                st.rerun()

if __name__ == "__main__":
    main()