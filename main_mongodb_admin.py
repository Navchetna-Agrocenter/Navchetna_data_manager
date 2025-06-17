# -*- coding: utf-8 -*-
"""
Admin functions for MongoDB-powered Streamlit Application
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib

def show_user_management():
    """Display user management page (Admin only)"""
    st.markdown("""
    <div class="main-header">
        <h1>👥 User Management</h1>
        <p>Manage users and their access permissions</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["👤 Create User", "📋 User List", "🔧 Edit User"])
    
    with tab1:
        st.subheader("Create New User")
        
        with st.form("create_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username", placeholder="Enter username")
                new_password = st.text_input("Password", type="password", placeholder="Enter password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            
            with col2:
                new_role = st.selectbox("Role", ["viewer", "project_manager", "admin"])
                
                # Get all projects
                projects_df = db_manager.read_dataframe(None, 'projects')
                all_projects = projects_df['Project_Name'].tolist() if not projects_df.empty else []
                
                if new_role == "project_manager" or new_role == "viewer":
                    accessible_projects = st.multiselect("Accessible Projects", all_projects)
                else:
                    accessible_projects = all_projects if new_role == "admin" else []
            
            full_name = st.text_input("Full Name", placeholder="Enter full name")
            email = st.text_input("Email", placeholder="Enter email address")
            
            create_user_btn = st.form_submit_button("👤 Create User", use_container_width=True)
            
            if create_user_btn:
                if not all([new_username, new_password, confirm_password, full_name]):
                    st.error("❌ Please fill in all required fields.")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters long.")
                elif create_user(new_username, new_password, new_role, accessible_projects, full_name, email):
                    st.success(f"✅ User '{new_username}' created successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create user. Username might already exist.")
    
    with tab2:
        st.subheader("Current Users")
        
        # Add refresh button
        if st.button("🔄 Refresh User List"):
            st.rerun()
        
        users_df = db_manager.read_dataframe(None, 'users')
        if not users_df.empty:
            # Show relevant columns for display
            display_columns = ['Username', 'Full_Name', 'Role', 'Assigned_Projects', 'Email', 'Status']
            available_columns = [col for col in display_columns if col in users_df.columns]
            display_df = users_df[available_columns].copy()
            
            # Convert all columns to string to avoid PyArrow type errors
            for col in display_df.columns:
                display_df[col] = display_df[col].astype(str)
            
            # Clean up NaN values
            display_df = display_df.fillna('')
            
            st.dataframe(display_df, use_container_width=True)
            
            # Delete user functionality
            st.subheader("Delete User")
            user_to_delete = st.selectbox("Select user to delete", users_df['Username'].tolist())
            if st.button("🗑️ Delete User", type="secondary"):
                if user_to_delete != st.session_state.get('username', ''):
                    if delete_user(user_to_delete):
                        st.success(f"✅ User '{user_to_delete}' deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete user.")
                else:
                    st.error("❌ You cannot delete your own account.")
        else:
            st.info("No users found.")
    
    with tab3:
        st.subheader("Edit User")
        users_df = db_manager.read_dataframe(None, 'users')
        if not users_df.empty:
            user_to_edit = st.selectbox("Select user to edit", users_df['Username'].tolist())
            
            if user_to_edit:
                user_data = get_user_data(user_to_edit)
                
                if user_data:
                    st.markdown(f"**Editing User: {user_to_edit}**")
                    
                    with st.form("edit_user_form", clear_on_submit=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_full_name = st.text_input("Full Name", value=user_data.get('Full_Name', ''))
                            edit_email = st.text_input("Email", value=user_data.get('Email', ''))
                            current_role = user_data.get('Role', 'viewer')
                            role_options = ["viewer", "project_manager", "admin"]
                            role_index = role_options.index(current_role) if current_role in role_options else 0
                            edit_role = st.selectbox("Role", role_options, index=role_index)
                        
                        with col2:
                            # Get all projects
                            projects_df = db_manager.read_dataframe(None, 'projects')
                            all_projects = projects_df['Project_Name'].tolist() if not projects_df.empty else []
                            
                            if edit_role == "project_manager" or edit_role == "viewer":
                                # Get current projects properly
                                current_assigned = user_data.get('Assigned_Projects', '')
                                if current_assigned == 'All':
                                    current_projects = all_projects
                                elif current_assigned:
                                    try:
                                        if isinstance(current_assigned, str):
                                            current_projects = [p.strip() for p in current_assigned.split(',')]
                                        else:
                                            current_projects = [str(current_assigned)]
                                        
                                        # Filter out any invalid projects
                                        current_projects = [p for p in current_projects if p in all_projects]
                                    except:
                                        current_projects = []
                                else:
                                    current_projects = []
                                
                                edit_accessible_projects = st.multiselect(
                                    "Accessible Projects", 
                                    all_projects, 
                                    default=current_projects
                                )
                            else:
                                edit_accessible_projects = all_projects if edit_role == "admin" else []
                                st.info(f"Projects: {'All projects' if edit_role == 'admin' else 'No projects'}")
                            
                            reset_password = st.checkbox("Reset Password")
                            if reset_password:
                                new_password = st.text_input("New Password", type="password")
                                confirm_new_password = st.text_input("Confirm New Password", type="password")
                        
                        submitted = st.form_submit_button("💾 Update User")
                        
                        if submitted:
                            update_data = {
                                'full_name': edit_full_name,
                                'email': edit_email,
                                'role': edit_role,
                                'accessible_projects': edit_accessible_projects
                            }
                            
                            if reset_password:
                                if not new_password or not confirm_new_password:
                                    st.error("❌ Please enter both password fields.")
                                elif new_password != confirm_new_password:
                                    st.error("❌ Passwords do not match.")
                                elif len(new_password) < 6:
                                    st.error("❌ Password must be at least 6 characters long.")
                                else:
                                    update_data['password'] = new_password
                                    if update_user(user_to_edit, update_data):
                                        st.success(f"✅ User '{user_to_edit}' updated successfully with new password!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to update user.")
                            else:
                                if update_user(user_to_edit, update_data):
                                    st.success(f"✅ User '{user_to_edit}' updated successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update user.")
                else:
                    st.error("❌ User data not found.")
        else:
            st.info("No users available for editing.")

def create_user(username: str, password: str, role: str, accessible_projects: list, full_name: str, email: str) -> bool:
    """Create a new user"""
    try:
        users_df = db_manager.read_dataframe(None, 'users')
        
        # Check if username already exists
        if not users_df.empty and username in users_df['Username'].values:
            return False
        
        # Generate user ID
        user_count = len(users_df) if not users_df.empty else 0
        user_id = f"USR{str(user_count + 1).zfill(3)}"
        
        # Create new user data
        new_user = {
            'User_ID': user_id,
            'Username': username,
            'Full_Name': full_name,
            'Password_Hash': db_manager.hash_password(password),
            'Role': role,
            'Assigned_Projects': ','.join(accessible_projects) if accessible_projects else 'All' if role == 'admin' else '',
            'Email': email,
            'Status': 'Active',
            'Created_Date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Add to dataframe
        if users_df.empty:
            users_df = pd.DataFrame([new_user])
        else:
            users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
        
        # Save to database
        db_manager.write_dataframe(None, 'users', users_df)
        return True
        
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return False

def get_user_data(username: str) -> dict:
    """Get user data for editing"""
    try:
        users_df = db_manager.read_dataframe(None, 'users')
        if not users_df.empty:
            user_row = users_df[users_df['Username'] == username]
            if not user_row.empty:
                return user_row.iloc[0].to_dict()
        return {}
    except Exception as e:
        st.error(f"Error getting user data: {str(e)}")
        return {}

def update_user(username: str, update_data: dict) -> bool:
    """Update user data"""
    try:
        users_df = db_manager.read_dataframe(None, 'users')
        
        if not users_df.empty:
            user_index = users_df[users_df['Username'] == username].index
            
            if len(user_index) > 0:
                idx = user_index[0]
                
                # Update fields
                if 'full_name' in update_data:
                    users_df.at[idx, 'Full_Name'] = update_data['full_name']
                if 'email' in update_data:
                    users_df.at[idx, 'Email'] = update_data['email']
                if 'role' in update_data:
                    users_df.at[idx, 'Role'] = update_data['role']
                if 'accessible_projects' in update_data:
                    projects = update_data['accessible_projects']
                    users_df.at[idx, 'Assigned_Projects'] = ','.join(projects) if projects else 'All' if update_data.get('role') == 'admin' else ''
                if 'password' in update_data:
                    users_df.at[idx, 'Password_Hash'] = db_manager.hash_password(update_data['password'])
                
                # Save updated data
                db_manager.write_dataframe(None, 'users', users_df)
                return True
        return False
    except Exception as e:
        st.error(f"Error updating user: {str(e)}")
        return False

def delete_user(username: str) -> bool:
    """Delete a user"""
    try:
        users_df = db_manager.read_dataframe(None, 'users')
        
        if not users_df.empty:
            users_df = users_df[users_df['Username'] != username]
            db_manager.write_dataframe(None, 'users', users_df)
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting user: {str(e)}")
        return False

def show_project_management():
    """Display project management interface (admin only)"""
    st.markdown("""
    <div class="main-header">
        <h1>🏗️ Project Management</h1>
        <p>Create and manage plantation projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display current projects
    projects_df = db_manager.read_dataframe(None, 'projects')
    
    st.subheader("📋 Current Projects")
    if not projects_df.empty:
        st.dataframe(projects_df, use_container_width=True)
    else:
        st.info("No projects found.")
    
    st.markdown("---")
    
    # Add new project form
    st.subheader("➕ Create New Project")
    
    with st.form("add_project_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            project_id = st.text_input("Project ID*", placeholder="e.g., PRJ003")
            project_name = st.text_input("Project Name*", placeholder="e.g., Amazon Sustainability")
            description = st.text_area("Description*", placeholder="Brief description of the project")
        
        with col2:
            start_date = st.date_input("Start Date*", datetime.now().date())
            target_area = st.number_input("Target Area (Hectares)*", min_value=1.0, max_value=10000.0, value=100.0)
            status = st.selectbox("Status*", ["Active", "Planning", "Completed", "On Hold"])
        
        # Get users for manager selection
        users_df = db_manager.read_dataframe(None, 'users')
        manager_options = users_df['Username'].tolist() if not users_df.empty else []
        manager = st.selectbox("Project Manager", manager_options)
        
        submitted = st.form_submit_button("🏗️ Create Project")
        
        if submitted:
            if all([project_id, project_name, description, target_area]):
                project_data = {
                    'Project_ID': project_id,
                    'Project_Name': project_name,
                    'Description': description,
                    'Start_Date': start_date.strftime('%Y-%m-%d'),
                    'Target_Area': target_area,
                    'Assigned_Users': manager,
                    'Status': status,
                    'Manager': manager,
                    'Created_Date': datetime.now().strftime('%Y-%m-%d')
                }
                
                if create_project(project_data):
                    st.success("✅ Project created successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create project.")
            else:
                st.error("❌ Please fill in all required fields.")

def create_project(project_data: dict) -> bool:
    """Create a new project"""
    try:
        projects_df = db_manager.read_dataframe(None, 'projects')
        
        # Check if project already exists
        if not projects_df.empty and project_data['Project_Name'] in projects_df['Project_Name'].values:
            return False
        
        # Add to dataframe
        if projects_df.empty:
            projects_df = pd.DataFrame([project_data])
        else:
            projects_df = pd.concat([projects_df, pd.DataFrame([project_data])], ignore_index=True)
        
        # Save to database
        db_manager.write_dataframe(None, 'projects', projects_df)
        
        # Initialize default tables for the project
        table_manager.initialize_project_tables(project_data['Project_Name'])
        
        return True
        
    except Exception as e:
        st.error(f"Error creating project: {str(e)}")
        return False

def show_schema_management():
    """Display schema management page (Admin only)"""
    st.markdown("""
    <div class="main-header">
        <h1>🔧 Schema Management</h1>
        <p>Manage database tables and fields</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 View Schema", "➕ Add Field", "✏️ Edit Field", "🗑️ Delete Field", "🆕 Manage Tables"])
    
    with tab1:
        st.subheader("Current Database Schema")
        
        # Get all tables
        all_tables = table_manager.get_all_table_definitions()
        
        if not all_tables:
            st.info("No tables defined yet.")
            return
        
        # Display table schemas
        for table_name, schema in all_tables.items():
            st.markdown(f"**{table_name} Table**")
            
            schema_df = pd.DataFrame(schema)
            if not schema_df.empty:
                st.dataframe(schema_df, use_container_width=True)
            else:
                st.info(f"No schema defined for {table_name}")
            
            st.markdown("---")
    
    with tab2:
        st.subheader("➕ Add Field to Existing Table")
        
        # Get available tables
        table_names = list(table_manager.get_all_table_definitions().keys())
        
        if not table_names:
            st.warning("No tables found to add fields to.")
        else:
            with st.form("add_field_form"):
                selected_table = st.selectbox("Select Table to Add Field to:", table_names)
                field_name = st.text_input("Field Name:")
                field_type = st.selectbox("Field Type:", ["Text", "Number", "Date", "True/False", "Dropdown"])
                default_value = st.text_input("Default Value (optional):")
                is_required = st.checkbox("Required Field")
                
                dropdown_options = ""
                if field_type == "Dropdown":
                    dropdown_options = st.text_area("Dropdown Options (comma-separated):")
                
                description = st.text_area("Field Description (optional):")
                
                submitted = st.form_submit_button("Add Field")
                
                if submitted and selected_table and field_name:
                    field_config = {
                        'name': field_name,
                        'type': field_type,
                        'required': is_required,
                        'default': default_value,
                        'description': description
                    }
                    
                    if field_type == "Dropdown":
                        field_config['options'] = [opt.strip() for opt in dropdown_options.split(',') if opt.strip()]
                    
                    if table_manager.add_field_to_table(selected_table, field_config):
                        st.success(f"✅ Field '{field_name}' added to {selected_table} successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add field. Field may already exist.")
    
    with tab3:
        st.subheader("✏️ Edit Existing Field")
        st.info("Field editing functionality will be implemented based on specific requirements.")
    
    with tab4:
        st.subheader("🗑️ Delete Field")
        st.info("Field deletion functionality will be implemented based on specific requirements.")
    
    with tab5:
        st.subheader("🆕 Manage Tables")
        
        # Create new table section
        st.markdown("**Create New Table**")
        with st.form("create_table_form"):
            table_name = st.text_input("Table Name:")
            table_description = st.text_area("Table Description:")
            
            st.markdown("**Define Table Fields:**")
            num_fields = st.number_input("Number of Fields:", min_value=1, max_value=20, value=3)
            
            fields = []
            for i in range(num_fields):
                col1, col2, col3 = st.columns(3)
                with col1:
                    field_name = st.text_input(f"Field {i+1} Name:", key=f"field_name_{i}")
                with col2:
                    field_type = st.selectbox(f"Field {i+1} Type:", ["Text", "Number", "Date", "True/False", "Dropdown"], key=f"field_type_{i}")
                with col3:
                    field_required = st.checkbox(f"Required", key=f"field_required_{i}")
                
                if field_name:
                    field_config = {
                        'name': field_name,
                        'type': field_type,
                        'required': field_required,
                        'default': ''
                    }
                    
                    if field_type == "Dropdown":
                        options = st.text_input(f"Options for {field_name} (comma-separated):", key=f"field_options_{i}")
                        field_config['options'] = [opt.strip() for opt in options.split(',') if opt.strip()]
                    
                    fields.append(field_config)
            
            submitted = st.form_submit_button("Create Table")
            
            if submitted and table_name and fields:
                if table_manager.create_table(table_name, table_description, fields):
                    st.success(f"✅ Table '{table_name}' created successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create table. Table may already exist.")
        
        # Show existing tables
        st.markdown("---")
        st.markdown("**Existing Tables**")
        all_tables = table_manager.get_all_table_definitions()
        if all_tables:
            for table_name in all_tables.keys():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📊 {table_name}")
                with col2:
                    if st.button(f"🗑️ Delete", key=f"delete_table_{table_name}"):
                        if table_manager.delete_table(table_name):
                            st.success(f"✅ Table '{table_name}' deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete table.")
        else:
            st.info("No tables created yet.")

def show_my_projects():
    """Display detailed view of manager's assigned projects"""
    st.markdown("""
    <div class="main-header">
        <h1>🏢 My Projects</h1>
        <p>Detailed view of all your assigned projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get user's accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects assigned to your account. Please contact an administrator.")
        return
    
    # Project selection
    selected_project = st.selectbox("Select Project:", accessible_projects)
    
    if not selected_project:
        return
    
    # Display project details
    st.subheader(f"📊 Project: {selected_project}")
    
    # Create tabs for different data views
    tab1, tab2, tab3 = st.tabs(["📈 Overview", "📊 All Tables", "📋 Recent Activity"])
    
    with tab1:
        # Show project overview/summary
        st.subheader("Project Summary")
        
        # Load KML and plantation data
        kml_data = table_manager.get_table_data(selected_project, "KML Tracking")
        plantation_data = table_manager.get_table_data(selected_project, "Plantation Records")
        
        # Calculate summary metrics
        total_area = kml_data['Total_Area'].sum() if not kml_data.empty and 'Total_Area' in kml_data.columns else 0
        area_approved = kml_data['Area_Approved'].sum() if not kml_data.empty and 'Area_Approved' in kml_data.columns else 0
        area_planted = plantation_data['Area_Planted'].sum() if not plantation_data.empty and 'Area_Planted' in plantation_data.columns else 0
        trees_planted = plantation_data['Trees_Planted'].sum() if not plantation_data.empty and 'Trees_Planted' in plantation_data.columns else 0
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Area Submitted", f"{total_area:.2f} Ha")
        
        with col2:
            st.metric("Area Approved", f"{area_approved:.2f} Ha", f"{(area_approved/total_area*100) if total_area > 0 else 0:.1f}%")
        
        with col3:
            st.metric("Area Planted", f"{area_planted:.2f} Ha", f"{(area_planted/total_area*100) if total_area > 0 else 0:.1f}%")
        
        with col4:
            st.metric("Trees Planted", f"{trees_planted:,}")
    
    with tab2:
        st.subheader("All Project Tables")
        
        # Get all available tables for this project
        available_tables = table_manager.get_project_tables(selected_project)
        
        if not available_tables:
            st.info(f"No tables found for project '{selected_project}'.")
            return
        
        # Create selectbox for table selection
        selected_table = st.selectbox("Select table to view:", available_tables)
        
        if selected_table:
            # Load and display the table data
            table_data = table_manager.get_table_data(selected_project, selected_table)
            if table_data.empty:
                st.info(f"No records in {selected_table}.")
            else:
                st.markdown(f"**Total Records:** {len(table_data)}")
                st.dataframe(table_data, use_container_width=True)
    
    with tab3:
        st.subheader("Recent Activity")
        
        # Show recent records from all tables
        recent_activity = []
        
        for table_name in table_manager.get_project_tables(selected_project):
            table_data = table_manager.get_table_data(selected_project, table_name)
            if not table_data.empty and 'Date' in table_data.columns:
                # Get last 5 records
                recent_records = table_data.tail(5)
                for _, record in recent_records.iterrows():
                    recent_activity.append({
                        'Date': record.get('Date', ''),
                        'Table': table_name,
                        'Summary': str(record.iloc[1]) if len(record) > 1 else 'N/A'
                    })
        
        if recent_activity:
            # Sort by date
            activity_df = pd.DataFrame(recent_activity)
            activity_df = activity_df.sort_values('Date', ascending=False)
            st.dataframe(activity_df, use_container_width=True)
        else:
            st.info("No recent activity found.")

def show_all_projects():
    """Display all projects for viewers with read-only access"""
    st.markdown("""
    <div class="main-header">
        <h1>🔍 All Projects</h1>
        <p>Browse all projects data (read-only)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all projects
    projects_df = db_manager.read_dataframe(None, 'projects')
    
    if projects_df.empty:
        st.warning("No projects available in the system.")
        return
    
    all_projects = projects_df['Project_Name'].tolist()
    
    # Project selection
    selected_project = st.selectbox("Select Project:", all_projects)
    
    if not selected_project:
        return
    
    # Display project details (similar to show_my_projects but read-only)
    st.subheader(f"📊 Project: {selected_project}")
    
    # Create tabs for different data views
    tab1, tab2 = st.tabs(["📈 Overview", "📊 All Tables"])
    
    with tab1:
        # Show project overview/summary
        st.subheader("Project Summary")
        
        # Load KML and plantation data
        kml_data = table_manager.get_table_data(selected_project, "KML Tracking")
        plantation_data = table_manager.get_table_data(selected_project, "Plantation Records")
        
        # Calculate summary metrics
        total_area = kml_data['Total_Area'].sum() if not kml_data.empty and 'Total_Area' in kml_data.columns else 0
        area_approved = kml_data['Area_Approved'].sum() if not kml_data.empty and 'Area_Approved' in kml_data.columns else 0
        area_planted = plantation_data['Area_Planted'].sum() if not plantation_data.empty and 'Area_Planted' in plantation_data.columns else 0
        trees_planted = plantation_data['Trees_Planted'].sum() if not plantation_data.empty and 'Trees_Planted' in plantation_data.columns else 0
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Area Submitted", f"{total_area:.2f} Ha")
        
        with col2:
            st.metric("Area Approved", f"{area_approved:.2f} Ha", f"{(area_approved/total_area*100) if total_area > 0 else 0:.1f}%")
        
        with col3:
            st.metric("Area Planted", f"{area_planted:.2f} Ha", f"{(area_planted/total_area*100) if total_area > 0 else 0:.1f}%")
        
        with col4:
            st.metric("Trees Planted", f"{trees_planted:,}")
    
    with tab2:
        st.subheader("All Project Tables")
        
        # Get all available tables for this project
        available_tables = table_manager.get_project_tables(selected_project)
        
        if not available_tables:
            st.info(f"No tables found for project '{selected_project}'.")
            return
        
        # Create selectbox for table selection
        selected_table = st.selectbox("Select table to view:", available_tables)
        
        if selected_table:
            # Load and display the table data
            table_data = table_manager.get_table_data(selected_project, selected_table)
            if table_data.empty:
                st.info(f"No records in {selected_table}.")
            else:
                st.markdown(f"**Total Records:** {len(table_data)}")
                st.dataframe(table_data, use_container_width=True) 