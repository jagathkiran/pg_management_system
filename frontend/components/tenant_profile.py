import streamlit as st

def render_tenant_profile(api_client, user):
    st.header("My Profile")
    
    tenant = user.get('tenant')
    if not tenant:
        st.warning("Tenant profile not found. Please contact admin.")
        return

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        st.write(f"**Name:** {tenant.get('full_name')}")
        st.write(f"**Email:** {user.get('email')}")
        st.write(f"**Phone:** {tenant.get('phone')}")
        st.write(f"**Emergency Contact:** {tenant.get('emergency_contact')}")
        
    with col2:
        st.subheader("Stay Details")
        st.write(f"**Check-in Date:** {tenant.get('check_in_date')}")
        st.write(f"**Deposit Amount:** ${tenant.get('deposit_amount', 0)}")
        
        # Fetch Room Details
        room_id = tenant.get('room_id')
        if room_id:
            try:
                room = api_client.get(f"rooms/{room_id}")
                if room:
                    st.write(f"**Room Number:** {room.get('room_number')}")
                    st.write(f"**Floor:** {room.get('floor')}")
                    st.write(f"**Type:** {room.get('room_type')}")
                    st.write(f"**Monthly Rent:** ${room.get('monthly_rent')}")
            except:
                st.write("**Room:** Error fetching room details")
        else:
            st.write("**Room:** Not Assigned")
            
    st.divider()
    # Edit Contact Info (Placeholder/Mockup)
    with st.expander("Edit Contact Information"):
        st.info("To update your contact details, please contact the administration.")
