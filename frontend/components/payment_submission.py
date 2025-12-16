import streamlit as st
import pandas as pd
from datetime import date

def render_payment_submission(api_client, user):
    st.header("Rent Payment")
    
    tenant = user.get('tenant')
    if not tenant:
        st.error("Tenant profile not found.")
        return

    # Tabs
    tab1, tab2 = st.tabs(["Submit Payment", "Payment History"])
    
    with tab1:
        st.subheader("Submit New Payment")
        
        with st.form("payment_form"):
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Amount", min_value=1.0, step=100.0)
                payment_date = st.date_input("Payment Date", value=date.today())
            with col2:
                payment_month = st.date_input("Rent Month (Select any day in the month)", value=date.today())
                method = st.selectbox("Payment Method", ["Bank Transfer", "UPI", "Cash", "Cheque"])
            
            transaction_id = st.text_input("Transaction ID / Reference Number")
            proof_file = st.file_uploader("Upload Payment Proof (Image)", type=['png', 'jpg', 'jpeg'])
            
            submitted = st.form_submit_button("Submit Payment")
            
            if submitted:
                if not transaction_id:
                    st.error("Transaction ID is required.")
                elif amount <= 0:
                    st.error("Invalid amount.")
                else:
                    # Upload File first if exists
                    proof_path = None
                    if proof_file:
                        try:
                            # Use API Client to upload
                            resp = api_client.upload_file("payments/upload-proof", proof_file)
                            if resp and 'path' in resp:
                                proof_path = resp['path']
                            else:
                                st.error("File upload failed.")
                                st.stop()
                        except Exception as e:
                            st.error(f"Error uploading file: {e}")
                            st.stop()
                            
                    # Submit Payment Data
                    # PaymentBase expects payment_month as date
                    # We should normalize payment_month to 1st of month
                    normalized_month = payment_month.replace(day=1)
                    
                    data = {
                        "amount": amount,
                        "payment_date": str(payment_date),
                        "payment_method": method,
                        "transaction_id": transaction_id,
                        "payment_month": str(normalized_month),
                        "proof_image_path": proof_path
                    }
                    
                    try:
                        api_client.post("payments/", data)
                        st.success("Payment submitted successfully!")
                    except Exception as e:
                        st.error(f"Submission failed: {e}")

    with tab2:
        st.subheader("History")
        try:
            # Fetch my payments. The endpoint "payments/" filters by current user if tenant.
            payments = api_client.get("payments/")
            if payments:
                df = pd.DataFrame(payments)
                display_cols = ['payment_month', 'amount', 'status', 'payment_date', 'transaction_id']
                st.dataframe(df[display_cols], use_container_width=True)
            else:
                st.info("No payment history found.")
        except Exception as e:
            st.error(f"Error fetching history: {e}")
