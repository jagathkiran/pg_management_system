import streamlit as st
import pandas as pd
import os

def render_rent_collection(api_client):
    st.subheader("Rent Collection & Payments")

    tab1, tab2 = st.tabs(["Pending Verifications", "Payment History"])

    with tab1:
        st.write("### Pending Payments")
        try:
            # Fetch pending payments
            pending_payments = api_client.get("payments/", params={"status": "Pending"})
            
            if pending_payments:
                for payment in pending_payments:
                    tenant_name = payment.get('tenant', {}).get('full_name', 'Unknown')
                    with st.expander(f"Payment ID: {payment['id']} - ${payment['amount']} (Tenant: {tenant_name})", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Amount:** ${payment['amount']}")
                            st.write(f"**Date:** {payment['payment_date']}")
                            st.write(f"**Month:** {payment['payment_month']}")
                            st.write(f"**Transaction ID:** {payment['transaction_id']}")
                        with col2:
                            proof_path = payment.get('proof_image_path')
                            if proof_path:
                                # Construct image URL. Assuming backend serves static files at root
                                # If proof_path is "uploads/payments/..."
                                # Base URL: http://localhost:8000
                                root_url = api_client.base_url.replace("/api", "")
                                image_url = f"{root_url}/{proof_path}"
                                try:
                                    st.image(image_url, caption="Payment Proof", width=300)
                                except:
                                    st.error("Could not load image.")
                            else:
                                st.warning("No proof image uploaded.")

                        # Action Form
                        st.write("**Verify Payment**")
                        # Use a unique key for each form
                        with st.form(key=f"verify_form_{payment['id']}"):
                            remarks = st.text_input("Remarks (Optional)", key=f"rem_{payment['id']}")
                            
                            col_approve, col_reject = st.columns(2)
                            with col_approve:
                                approve_btn = st.form_submit_button("Approve Payment", type="primary", use_container_width=True)
                            with col_reject:
                                reject_btn = st.form_submit_button("Reject Payment", use_container_width=True)

                            if approve_btn:
                                data = {"status": "Verified", "remarks": remarks}
                                try:
                                    api_client.put(f"payments/{payment['id']}/verify", data)
                                    st.success("Payment verified!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            
                            if reject_btn:
                                data = {"status": "Rejected", "remarks": remarks}
                                try:
                                    api_client.put(f"payments/{payment['id']}/verify", data)
                                    st.warning("Payment rejected.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
            else:
                st.info("No pending payments to verify.")
        except Exception as e:
            st.error(f"Error fetching pending payments: {e}")

    with tab2:
        st.write("### Payment History")
        try:
            # Fetch all payments
            all_payments = api_client.get("payments/")
            if all_payments:
                df = pd.DataFrame(all_payments)
                
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    status_options = ["All"] + list(df['status'].unique()) if 'status' in df.columns else ["All"]
                    status_filter = st.selectbox("Filter by Status", status_options)
                
                filtered_df = df.copy()
                if not df.empty:
                    if status_filter != "All":
                        filtered_df = filtered_df[filtered_df['status'] == status_filter]
                    
                    # Enrich with tenant name
                    if 'tenant' in filtered_df.columns:
                        filtered_df['Tenant Name'] = filtered_df['tenant'].apply(lambda x: x.get('full_name') if isinstance(x, dict) else 'Unknown')
                    else:
                        filtered_df['Tenant Name'] = 'Unknown'
                    
                    display_cols = ['id', 'Tenant Name', 'amount', 'payment_date', 'payment_month', 'status', 'remarks']
                    display_cols = [c for c in display_cols if c in filtered_df.columns]
                    
                    st.dataframe(
                        filtered_df[display_cols],
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.info("No payment history found.")
        except Exception as e:
            st.error(f"Error fetching history: {e}")
