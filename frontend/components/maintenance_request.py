import streamlit as st
import pandas as pd

def render_maintenance_request(api_client, user):
    st.header("Maintenance Requests")
    
    tenant = user.get('tenant')
    if not tenant:
        st.error("Tenant profile not found.")
        return

    tab1, tab2 = st.tabs(["New Request", "My Requests"])
    
    with tab1:
        with st.form("maint_form"):
            category = st.selectbox("Category", ["Plumbing", "Electrical", "Furniture", "Other"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            description = st.text_area("Description")
            image_file = st.file_uploader("Upload Image (Optional)", type=['png', 'jpg', 'jpeg'])
            
            submit = st.form_submit_button("Submit Request")
            
            if submit:
                if not description:
                    st.error("Description is required.")
                else:
                    image_path = None
                    if image_file:
                        try:
                            resp = api_client.upload_file("maintenance/upload-image", image_file)
                            if resp and 'path' in resp:
                                image_path = resp['path']
                            else:
                                st.warning("Image upload failed, proceeding without image.")
                        except Exception as e:
                            st.error(f"Error uploading image: {e}")
                            st.stop()
                    
                    data = {
                        "category": category,
                        "priority": priority,
                        "description": description,
                        "image_path": image_path
                    }
                    try:
                        api_client.post("maintenance/", data)
                        st.success("Request submitted successfully!")
                    except Exception as e:
                        st.error(f"Error submitting request: {e}")

    with tab2:
        # List requests
        try:
            reqs = api_client.get("maintenance/")
            if reqs:
                df = pd.DataFrame(reqs)
                # Ensure columns exist
                display_cols = ['id', 'category', 'priority', 'status', 'request_date', 'description']
                st.dataframe(df[display_cols], use_container_width=True)
            else:
                st.info("No maintenance requests found.")
        except Exception as e:
            st.error(f"Error fetching requests: {e}")
