import streamlit as st

def hide_sidebar_nav():
    """Hides the default Streamlit sidebar navigation."""
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

def render_auth_sidebar(current_page: str = None):
    """
    Renders the sidebar for authentication pages (Login/Signup) and Home.
    Hides default nav and provides Login/Signup buttons.
    """
    hide_sidebar_nav()
    st.sidebar.title("Navigation")
    
    # We use columns or just buttons.
    # To prevent 'switch_page' errors or loops, we can disable the current page button
    # but Streamlit buttons don't have 'disabled' state easily based on logic here?
    # Actually st.button has `disabled` arg.
    
    if st.sidebar.button("Login", key="auth_nav_login", disabled=(current_page == "login")):
        st.switch_page("pages/login.py")
        
    if st.sidebar.button("Sign Up", key="auth_nav_signup", disabled=(current_page == "signup")):
        st.switch_page("pages/signup.py")
