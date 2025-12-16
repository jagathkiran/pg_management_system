import streamlit as st
import sys
import os
from datetime import date

# Add parent directory to path to allow imports from utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.api_client import APIClient
from utils.session import init_session, is_authenticated, get_user_role
from utils.ui import render_auth_sidebar

# Initialize API Client
api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api")
api_client = APIClient(base_url=api_base_url)

def show_signup_page():
    st.title("Sign Up")
    
    if is_authenticated():
        role = get_user_role()
        if role == "admin":
            st.switch_page("pages/management_dashboard.py")
        elif role == "tenant":
            st.switch_page("pages/tenant_dashboard.py")
        return

    # Sidebar navigation for unauthenticated users
    render_auth_sidebar(current_page="signup")
    
    st.info("Create a new account to access the PG Management System.")

    role_choice = st.radio("I want to register as:", ["Tenant", "Admin"], horizontal=True)

    # Initialize variables to ensure scope safety
    full_name = None
    phone = None
    emergency_contact = None
    check_in_date = None

    with st.form("signup_form"):
        st.subheader("Account Credentials")
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
        with col2:
            confirm_password = st.text_input("Confirm Password", type="password")
        
        if role_choice == "Tenant":
            st.subheader("Personal Details")
            full_name = st.text_input("Full Name")
            phone = st.text_input("Phone Number")
            emergency_contact = st.text_input("Emergency Contact")
            check_in_date = st.date_input("Expected Check-in Date", value=date.today())
        
        submitted = st.form_submit_button("Sign Up", use_container_width=True)
    
    # Process form submission outside the form context to allow other widgets like st.button
    if submitted:
        if password != confirm_password:
            st.error("Passwords do not match.")
            return # Stop execution
            
        if not email or not password:
            st.error("Email and Password are required.")
            return # Stop execution
        
        try:
            with st.spinner("Creating account..."):
                if role_choice == "Admin":
                    data = {
                        "email": email,
                        "password": password,
                        "role": "admin"
                    }
                    api_client.post("auth/register-admin", data)
                    st.success("Admin account created successfully!")
                    st.balloons()
                    
                elif role_choice == "Tenant":
                    if not full_name or not phone:
                            st.error("Full Name and Phone are required for Tenants.")
                            return # Stop execution
                    
                    data = {
                        "email": email,
                        "password": password,
                        "full_name": full_name,
                        "phone": phone,
                        "emergency_contact": emergency_contact if emergency_contact else "N/A",
                        "check_in_date": str(check_in_date),
                        # room_id is optional
                        "deposit_amount": 0.0 # Default
                    }
                    api_client.post("tenants/register", data)
                    st.success("Tenant account created successfully!")
                    st.balloons()
            
            st.info("You can now Login.")
            if st.button("Go to Login"):
                st.switch_page("pages/login.py")
                
        except Exception as e:
            st.error(f"Registration failed: {str(e)}")

if __name__ == "__main__":
    st.set_page_config(page_title="Sign Up - PG Management", page_icon="📝")
    init_session()
    show_signup_page()