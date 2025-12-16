import streamlit as st
import pandas as pd

def render_room_management(api_client):
    st.subheader("Room Management")

    tab1, tab2 = st.tabs(["View Rooms", "Add Room"])

    with tab1:
        # Fetch rooms
        try:
            rooms_data = api_client.get("rooms/")
            if rooms_data:
                df = pd.DataFrame(rooms_data)
                
                # Pre-process data
                if 'tenants' in df.columns:
                    df['current_occupants'] = df['tenants'].apply(lambda x: len(x) if isinstance(x, list) else 0)
                    df['availability'] = df.apply(lambda row: "Available" if row['current_occupants'] < row['capacity'] else "Full", axis=1)
                else:
                    df['current_occupants'] = 0
                    df['availability'] = "Available"

                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    type_options = ["All"] + list(df['room_type'].unique()) if not df.empty else ["All"]
                    filter_type = st.selectbox("Filter by Type", type_options)
                with col2:
                     filter_status = st.selectbox("Filter by Status", ["All", "Available", "Full"])

                # Apply filters
                filtered_df = df.copy()
                if not df.empty:
                    if filter_type != "All":
                        filtered_df = filtered_df[filtered_df['room_type'] == filter_type]
                    if filter_status == "Available":
                        filtered_df = filtered_df[filtered_df['availability'] == "Available"]
                    elif filter_status == "Full":
                        filtered_df = filtered_df[filtered_df['availability'] == "Full"]

                    # Display Dataframe
                    display_cols = ['id', 'room_number', 'room_type', 'floor', 'monthly_rent', 'capacity', 'current_occupants', 'availability', 'is_active']
                    # Filter out columns that don't exist
                    display_cols = [c for c in display_cols if c in filtered_df.columns]
                    
                    st.dataframe(
                        filtered_df[display_cols], 
                        use_container_width=True,
                        hide_index=True
                    )

                    # Action Section: Edit/Delete
                    st.divider()
                    st.write("### Manage Selected Room")
                    
                    room_ids = filtered_df['id'].unique()
                    room_options = [(r_id, f"Room {filtered_df[filtered_df['id']==r_id]['room_number'].iloc[0]}") for r_id in room_ids]
                    
                    selected_room_id = st.selectbox(
                        "Select Room", 
                        options=[r[0] for r in room_options],
                        format_func=lambda x: next((r[1] for r in room_options if r[0] == x), str(x))
                    )
                    
                    if selected_room_id:
                        selected_room = filtered_df[filtered_df['id'] == selected_room_id].iloc[0]
                        
                        col_edit, col_delete = st.columns(2)
                        
                        with col_edit:
                            with st.expander("Edit Room Details"):
                                with st.form("edit_room_form"):
                                    new_number = st.text_input("Room Number", value=selected_room['room_number'])
                                    new_floor = st.number_input("Floor", value=int(selected_room['floor']))
                                    
                                    # Handle Type Selection
                                    current_type = selected_room['room_type']
                                    type_opts = ["Single", "Double", "Triple"]
                                    if current_type not in type_opts:
                                        type_opts.append(current_type)
                                    new_type = st.selectbox("Type", type_opts, index=type_opts.index(current_type))
                                    
                                    new_rent = st.number_input("Monthly Rent", value=float(selected_room['monthly_rent']))
                                    new_capacity = st.number_input("Capacity", value=int(selected_room['capacity']))
                                    
                                    # Is Active (handle boolean)
                                    is_active_val = bool(selected_room['is_active'])
                                    new_active = st.checkbox("Is Active", value=is_active_val)
                                    
                                    if st.form_submit_button("Update Room"):
                                        data = {
                                            "room_number": new_number,
                                            "floor": int(new_floor),
                                            "room_type": new_type,
                                            "monthly_rent": float(new_rent),
                                            "capacity": int(new_capacity),
                                            "is_active": new_active
                                        }
                                        try:
                                            res = api_client.put(f"rooms/{selected_room_id}", data)
                                            st.success("Room updated successfully!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Failed to update room: {e}")

                        with col_delete:
                            st.write("Delete Room")
                            confirm_delete = st.checkbox("I confirm deletion of this room", key="confirm_del")
                            if st.button("Delete Room", type="primary", disabled=not confirm_delete):
                                try:
                                    api_client.delete(f"rooms/{selected_room_id}")
                                    st.success("Room deleted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to delete room: {e}")

            else:
                st.info("No rooms found. Add a room to get started.")
        except Exception as e:
            st.error(f"Error fetching rooms: {str(e)}")

    with tab2:
        st.write("### Add New Room")
        with st.form("add_room_form"):
            r_number = st.text_input("Room Number")
            r_floor = st.number_input("Floor", min_value=0, step=1)
            r_type = st.selectbox("Room Type", ["Single", "Double", "Triple"])
            r_rent = st.number_input("Monthly Rent", min_value=0.0, step=100.0)
            r_capacity = st.number_input("Capacity", min_value=1, step=1)
            
            if st.form_submit_button("Create Room"):
                if not r_number:
                    st.error("Room Number is required.")
                else:
                    data = {
                        "room_number": r_number,
                        "floor": int(r_floor),
                        "room_type": r_type,
                        "monthly_rent": float(r_rent),
                        "capacity": int(r_capacity)
                    }
                    try:
                        res = api_client.post("rooms/", data)
                        st.success("Room created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create room: {str(e)}")
