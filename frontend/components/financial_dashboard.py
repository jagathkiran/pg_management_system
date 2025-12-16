import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def render_financial_dashboard(api_client):
    st.subheader("Financial Overview")

    # Fetch Data
    try:
        with st.spinner("Loading financial data..."):
            payments_data = api_client.get("payments/?limit=1000") 
            rooms_data = api_client.get("rooms/?limit=1000")
            tenants_data = api_client.get("tenants/?active_only=true&limit=1000")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return

    if not payments_data:
        payments_data = []
    if not rooms_data:
        rooms_data = []
    if not tenants_data:
        tenants_data = []

    # Convert to DataFrames
    df_payments = pd.DataFrame(payments_data)
    df_rooms = pd.DataFrame(rooms_data)
    df_tenants = pd.DataFrame(tenants_data)

    # --- Metrics ---
    
    # 1. Total Revenue (Verified Payments)
    total_revenue = 0.0
    pending_amount = 0.0
    
    if not df_payments.empty:
        # Ensure correct types
        df_payments['amount'] = pd.to_numeric(df_payments['amount'], errors='coerce').fillna(0)
        
        verified_payments = df_payments[df_payments['status'] == 'Verified']
        total_revenue = verified_payments['amount'].sum()
        
        pending_payments = df_payments[df_payments['status'] == 'Pending']
        pending_amount = pending_payments['amount'].sum()

    # 2. Deposit Summary (Active Tenants)
    total_deposit = 0.0
    if not df_tenants.empty:
        df_tenants['deposit_amount'] = pd.to_numeric(df_tenants['deposit_amount'], errors='coerce').fillna(0)
        total_deposit = df_tenants['deposit_amount'].sum()

    # 3. Occupancy Rate
    total_capacity = 0
    total_occupied = 0
    occupancy_rate = 0.0
    
    if not df_rooms.empty:
        df_rooms['capacity'] = pd.to_numeric(df_rooms['capacity'], errors='coerce').fillna(0)
        total_capacity = df_rooms['capacity'].sum()
        
    if not df_tenants.empty:
        total_occupied = len(df_tenants) # Assuming 1 tenant = 1 bed/capacity unit
        
    if total_capacity > 0:
        occupancy_rate = (total_occupied / total_capacity) * 100

    # Display Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${total_revenue:,.2f}")
    col2.metric("Pending Payments", f"${pending_amount:,.2f}")
    col3.metric("Total Deposits", f"${total_deposit:,.2f}")
    col4.metric("Occupancy Rate", f"{occupancy_rate:.1f}%")

    st.divider()

    # --- Charts ---
    c1, c2 = st.columns(2)

    with c1:
        st.write("#### Revenue Trend (Monthly)")
        if not df_payments.empty and 'payment_month' in df_payments.columns:
            # Group by month
            df_verified = df_payments[df_payments['status'] == 'Verified'].copy()
            if not df_verified.empty:
                df_verified['payment_month'] = pd.to_datetime(df_verified['payment_month'])
                df_verified['Month'] = df_verified['payment_month'].dt.strftime('%Y-%m')
                monthly_revenue = df_verified.groupby('Month')['amount'].sum().reset_index()
                
                fig_rev = px.bar(monthly_revenue, x='Month', y='amount', title="Monthly Revenue", labels={'amount': 'Revenue ($)'})
                st.plotly_chart(fig_rev, use_container_width=True)
            else:
                st.info("No verified payments to show revenue trend.")
        else:
            st.info("No payment data available.")

    with c2:
        st.write("#### Occupancy Status")
        if total_capacity > 0:
            vacant = total_capacity - total_occupied
            labels = ['Occupied', 'Vacant']
            values = [total_occupied, vacant]
            fig_occ = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
            fig_occ.update_layout(title_text="Overall Occupancy")
            st.plotly_chart(fig_occ, use_container_width=True)
        else:
            st.info("No room capacity data defined.")

    # --- Pending Payments Table ---
    st.write("#### Pending Payments")
    if not df_payments.empty:
        pending_df = df_payments[df_payments['status'] == 'Pending'].copy()
        if not pending_df.empty:
            # Enrich with Tenant Name
            if 'tenant' in pending_df.columns:
                 pending_df['Tenant Name'] = pending_df['tenant'].apply(lambda x: x.get('full_name') if isinstance(x, dict) else 'Unknown')
            else:
                 pending_df['Tenant Name'] = 'Unknown'

            display_cols = ['id', 'Tenant Name', 'amount', 'payment_month', 'payment_date']
            st.dataframe(pending_df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.success("No pending payments.")
    else:
        st.info("No payments recorded.")
