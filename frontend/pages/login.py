import streamlit as st
import sys
import os

# Add parent directory to path to allow imports from components and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.api_client import APIClient
from utils.session import login_user, init_session, is_authenticated, get_user_role
import os

# Initialize API Client
api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api")
api_client = APIClient(base_url=api_base_url)

def show_login_page():
    st.title("Login to PG Management System")
    
    # Check if already authenticated
    if is_authenticated():
        role = get_user_role()
        if role == "admin":
            st.switch_page("pages/management_dashboard.py")
        elif role == "tenant":
            st.switch_page("pages/tenant_dashboard.py")
        return

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.subheader("Please enter your credentials")
            email = st.text_input("Email", placeholder="admin@pg.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    with st.spinner("Logging in..."):
                        token_data = api_client.login(email, password)
                        if token_data:
                            api_client.set_token(token_data['access_token'])
                            try:
                                user_info = api_client.get("auth/me")
                                if user_info:
                                    login_user(token_data['access_token'], user_info)
                                    st.success("Login successful!")
                                    
                                    # Redirect based on role
                                    role = user_info.get('role')
                                    if role == "admin":
                                        st.switch_page("pages/management_dashboard.py")
                                    elif role == "tenant":
                                        st.switch_page("pages/tenant_dashboard.py")
                                    else:
                                        st.error(f"Unknown role: {role}")
                                else:
                                    st.error("Login failed: Could not retrieve user details.")
                            except Exception as e:
                                st.error(f"Login failed: {str(e)}")
                        else:
                            st.error("Invalid email or password.")

if __name__ == "__main__":
    st.set_page_config(page_title="Login - PG Management", page_icon="🔐")
    init_session()
    show_login_page()