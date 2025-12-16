import streamlit as st
from utils.session import logout_user, init_session, is_authenticated

def show_dashboard():
    init_session()
    if not is_authenticated():
        st.switch_page("pages/login.py")
        return

    st.title("Tenant Dashboard")
    st.write("Welcome, Tenant!")
    
    if st.button("Logout"):
        logout_user()
        st.switch_page("pages/login.py")

if __name__ == "__main__":
    show_dashboard()
