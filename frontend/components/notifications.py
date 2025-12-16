import streamlit as st
from datetime import date

def render_notifications(api_client, user):
    st.header("Notifications")
    
    tenant = user.get('tenant')
    if not tenant:
        return

    st.subheader("Rent Status")
    # 1. Rent Reminder
    # Check if rent paid for this month
    this_month = date.today().replace(day=1)
    month_str = this_month.strftime('%Y-%m-%d')
    month_display = this_month.strftime('%B %Y')
    
    try:
        payments = api_client.get("payments/")
        paid = False
        status = "Unpaid"
        if payments:
            for p in payments:
                if p.get('payment_month') == month_str:
                    status = p.get('status')
                    if status in ['Verified', 'Pending']:
                        paid = True
                    break
        
        if paid:
            st.success(f"✅ Rent for {month_display} is {status}.")
        else:
            st.warning(f"⚠️ Rent for {month_display} is Pending/Unpaid!")
            if st.button("Pay Now"):
                st.info("Go to 'Pay Rent' tab to submit payment.")
            
    except Exception as e:
        st.error(f"Error checking rent status: {e}")

    st.divider()
    st.subheader("Recent Updates")
    # 2. Maintenance Updates
    try:
        reqs = api_client.get("maintenance/")
        if reqs:
            active_reqs = [r for r in reqs if r['status'] in ['In Progress', 'Resolved', 'Closed']]
            if active_reqs:
                for r in active_reqs:
                    icon = "🔧" if r['status'] == 'In Progress' else "✅"
                    st.info(f"{icon} Request #{r['id']} ({r['category']}) is **{r['status']}**")
            else:
                st.write("No recent updates.")
        else:
            st.write("No updates.")
    except:
        pass
