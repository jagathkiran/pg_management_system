import streamlit as st
import pandas as pd

def render_maintenance_mgmt(api_client):
    st.subheader("Maintenance Management")

    # Fetch all requests
    try:
        requests_data = api_client.get("maintenance/")
        if not requests_data:
            st.info("No maintenance requests found.")
            return

        df = pd.DataFrame(requests_data)
        
        # Enrich data
        if 'tenant' in df.columns:
            df['Tenant Name'] = df['tenant'].apply(lambda x: x.get('full_name') if isinstance(x, dict) else 'Unknown')
            df['Room ID'] = df['tenant'].apply(lambda x: str(x.get('room_id')) if isinstance(x, dict) else 'N/A')
        else:
            df['Tenant Name'] = 'Unknown'
            df['Room ID'] = 'N/A'

        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        total = len(df)
        open_reqs = len(df[df['status'] == 'Open'])
        in_progress = len(df[df['status'] == 'In Progress'])
        resolved = len(df[df['status'] == 'Resolved'])
        
        col1.metric("Total Requests", total)
        col2.metric("Open", open_reqs, delta_color="inverse")
        col3.metric("In Progress", in_progress)
        col4.metric("Resolved", resolved)

        st.divider()

        # Filters
        c1, c2 = st.columns(2)
        with c1:
            # Default to Open/In Progress if available, else all
            all_statuses = list(df['status'].unique())
            default_statuses = [s for s in ['Open', 'In Progress'] if s in all_statuses]
            if not default_statuses: 
                default_statuses = all_statuses
            
            status_filter = st.multiselect("Filter by Status", all_statuses, default=default_statuses)
        with c2:
            priority_filter = st.multiselect("Filter by Priority", list(df['priority'].unique()), default=list(df['priority'].unique()))

        filtered_df = df.copy()
        if status_filter:
            filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
        if priority_filter:
            filtered_df = filtered_df[filtered_df['priority'].isin(priority_filter)]

        # Display Dataframe
        if not filtered_df.empty:
            display_cols = ['id', 'category', 'priority', 'status', 'request_date', 'Tenant Name', 'Room ID']
            st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)

            # Manage Request
            st.write("### Manage Request")
            req_options = [(r_id, f"#{r_id} - {filtered_df[filtered_df['id']==r_id]['category'].iloc[0]} ({filtered_df[filtered_df['id']==r_id]['Tenant Name'].iloc[0]})") for r_id in filtered_df['id'].unique()]
            
            selected_req_id = st.selectbox("Select Request to Update", [r[0] for r in req_options], format_func=lambda x: next((r[1] for r in req_options if r[0] == x), str(x)))

            if selected_req_id:
                req = filtered_df[filtered_df['id'] == selected_req_id].iloc[0]
                
                with st.expander("Request Details & Update", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Category:** {req['category']}")
                        st.write(f"**Priority:** {req['priority']}")
                        st.write(f"**Status:** {req['status']}")
                        st.write(f"**Date:** {req['request_date']}")
                    with c2:
                        st.write(f"**Tenant:** {req['Tenant Name']}")
                        st.write(f"**Room ID:** {req['Room ID']}")
                        
                    st.write(f"**Description:** {req['description']}")
                    
                    if req.get('image_path'):
                        root_url = api_client.base_url.replace("/api", "")
                        try:
                            st.image(f"{root_url}/{req['image_path']}", caption="Request Image", width=300)
                        except:
                            st.error("Could not load image.")
                    
                    st.divider()
                    st.write("#### Update Status")
                    with st.form("update_req"):
                        status_opts = ["Open", "In Progress", "Resolved", "Closed"]
                        current_status_idx = status_opts.index(req['status']) if req['status'] in status_opts else 0
                        new_status = st.selectbox("Status", status_opts, index=current_status_idx)
                        
                        resolution = st.text_area("Resolution Notes", value=req['resolution_notes'] if req['resolution_notes'] else "")
                        
                        if st.form_submit_button("Update Request"):
                            data = {
                                "status": new_status,
                                "resolution_notes": resolution
                            }
                            try:
                                api_client.put(f"maintenance/{selected_req_id}", data)
                                st.success("Request updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to update request: {e}")
        else:
            st.info("No requests match the selected filters.")

    except Exception as e:
        st.error(f"Error fetching maintenance requests: {e}")
