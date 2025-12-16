import streamlit as st
import pandas as pd
from datetime import date

def render_tenant_management(api_client):
    st.subheader("Tenant Management")

    tab1, tab2 = st.tabs(["View Tenants", "Register Tenant"])

    with tab1:
        # Fetch tenants
        try:
            tenants_data = api_client.get("tenants/")
            if tenants_data:
                df = pd.DataFrame(tenants_data)
                
                # Filters
                filter_active = st.radio("Status", ["All", "Active", "Inactive"], horizontal=True)
                
                filtered_df = df.copy()
                if not df.empty:
                    if filter_active == "Active":
                        filtered_df = filtered_df[filtered_df['is_active'] == True]
                    elif filter_active == "Inactive":
                        filtered_df = filtered_df[filtered_df['is_active'] == False]
                    
                    # Display DataFrame
                    # Prepare display columns
                    if 'user' in filtered_df.columns:
                        filtered_df['email'] = filtered_df['user'].apply(lambda x: x.get('email') if isinstance(x, dict) else '')
                    else:
                        filtered_df['email'] = ''

                    display_cols = ['id', 'full_name', 'email', 'phone', 'room_id', 'is_active']
                    # Ensure columns exist
                    display_cols = [c for c in display_cols if c in filtered_df.columns]
                    
                    st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)
                    
                    # Manage Tenant
                    st.divider()
                    st.write("### Manage Tenant")
                    tenant_ids = filtered_df['id'].unique()
                    t_options = [(t_id, f"{filtered_df[filtered_df['id']==t_id]['full_name'].iloc[0]} (ID: {t_id})") for t_id in tenant_ids]
                    
                    selected_t_id = st.selectbox("Select Tenant", [t[0] for t in t_options], format_func=lambda x: next((t[1] for t in t_options if t[0] == x), str(x)))
                    
                    if selected_t_id:
                        selected_t = filtered_df[filtered_df['id'] == selected_t_id].iloc[0]
                        
                        with st.expander("Tenant Details & Actions", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Name:** {selected_t.get('full_name')}")
                                st.write(f"**Phone:** {selected_t.get('phone')}")
                                st.write(f"**Emergency Contact:** {selected_t.get('emergency_contact')}")
                                st.write(f"**Email:** {selected_t.get('email')}")
                            with col2:
                                st.write(f"**Room ID:** {selected_t.get('room_id')}")
                                st.write(f"**Check-In:** {selected_t.get('check_in_date')}")
                                st.write(f"**Deposit:** {selected_t.get('deposit_amount')}")
                                status_text = "Active" if selected_t.get('is_active') else "Inactive"
                                st.write(f"**Status:** {status_text}")

                            st.divider()
                            
                            # Actions
                            if selected_t.get('is_active'):
                                st.write("#### Actions")
                                if st.button("Process Checkout", type="primary"):
                                    try:
                                        res = api_client.post(f"tenants/{selected_t_id}/checkout")
                                        st.success("Checkout processed successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Checkout failed: {e}")
            else:
                st.info("No tenants found.")
        except Exception as e:
            st.error(f"Error fetching tenants: {e}")

    with tab2:
        st.write("### Register New Tenant")
        
        # Fetch available rooms
        try:
            rooms_data = api_client.get("rooms/")
            # Filter available rooms
            available_rooms = []
            if rooms_data:
                for r in rooms_data:
                    current_len = len(r.get('tenants', [])) if isinstance(r.get('tenants'), list) else 0
                    if current_len < r.get('capacity', 0) and r.get('is_active'):
                        available_rooms.append(r)
        except:
            available_rooms = []
            st.warning("Could not fetch rooms.")

        with st.form("register_tenant"):
            col1, col2 = st.columns(2)
            with col1:
                t_name = st.text_input("Full Name")
                t_email = st.text_input("Email (for login)")
                t_password = st.text_input("Initial Password", value="welcome123", type="password")
            with col2:
                t_phone = st.text_input("Phone")
                t_emergency = st.text_input("Emergency Contact")
            
            col3, col4 = st.columns(2)
            with col3:
                t_checkin = st.date_input("Check-In Date", value=date.today())
            with col4:
                t_deposit = st.number_input("Deposit Amount", min_value=0.0, step=100.0)
            
            room_opts = [(r['id'], f"Room {r['room_number']} ({r['room_type']}) - Rent: {r['monthly_rent']}") for r in available_rooms]
            
            if not room_opts:
                st.warning("No available rooms found. Please create rooms first.")
                selected_room = None
            else:
                selected_room = st.selectbox("Assign Room", [r[0] for r in room_opts], format_func=lambda x: next((r[1] for r in room_opts if r[0] == x), "Select Room"))
            
            if st.form_submit_button("Register Tenant"):
                if not t_name or not t_email:
                    st.error("Name and Email are required.")
                elif not selected_room:
                    st.error("Please select a room.")
                else:
                    data = {
                        "full_name": t_name,
                        "email": t_email,
                        "password": t_password,
                        "phone": t_phone,
                        "emergency_contact": t_emergency,
                        "check_in_date": str(t_checkin),
                        "deposit_amount": float(t_deposit),
                        "room_id": selected_room
                    }
                    
                    try:
                        res = api_client.post("tenants/", data)
                        st.success(f"Tenant registered successfully! Login email: {t_email}")
                        st.info(f"Initial Password: {t_password}")
                    except Exception as e:
                        st.error(f"Registration failed: {e}")
