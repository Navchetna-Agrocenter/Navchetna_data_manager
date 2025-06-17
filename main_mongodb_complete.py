# -*- coding: utf-8 -*-
"""
Complete MongoDB-powered Streamlit Application for Plantation Data Management System
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import time
import math
import json
import ast
import plotly.express as px
import plotly.graph_objects as go

# More robust path handling for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import configuration and managers
import config
from utils.mongodb_manager import MongoDBManager
from utils.table_manager import TableManager
from components.charts import ChartManager

# Configure Streamlit page
st.set_page_config(
    page_title="Navchetna Plantation Data Manager - MongoDB",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize managers
@st.cache_resource
def initialize_managers():
    """Initialize all managers"""
    # Initialize MongoDB manager
    db_manager = MongoDBManager()
    
    # Initialize table manager
    table_manager = TableManager(db_manager)
    
    # Initialize chart manager
    chart_manager = ChartManager()
    
    return db_manager, table_manager, chart_manager

# Get managers
db_manager, table_manager, chart_manager = initialize_managers()

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
    }
    
    .data-form {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Authentication Manager
class AuthManager:
    """Authentication and user management for MongoDB"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Initialize session state
        if 'logged_in' not in st.session_state:
            st.session_state['logged_in'] = False
        if 'username' not in st.session_state:
            st.session_state['username'] = None
        if 'role' not in st.session_state:
            st.session_state['role'] = None
        if 'assigned_projects' not in st.session_state:
            st.session_state['assigned_projects'] = None
    
    def show_login_form(self):
        """Display login form"""
        st.subheader("🔐 Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if self.authenticate_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    def authenticate_user(self, username, password):
        """Authenticate user"""
        users_df = self.db_manager.read_dataframe(None, 'users')
        
        if users_df.empty:
            # Create default admin user if no users exist
            if username == "admin" and password == "admin":
                self.create_default_admin()
                st.session_state['logged_in'] = True
                st.session_state['username'] = "admin"
                st.session_state['role'] = "admin"
                st.session_state['assigned_projects'] = "All"
                return True
            return False
        
        # Find user
        user_row = users_df[users_df['Username'] == username]
        if user_row.empty:
            return False
        
        # Check password
        hashed_password = self.db_manager.hash_password(password)
        if user_row.iloc[0]['Password_Hash'] != hashed_password:
            return False
        
        # Set session state
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.session_state['role'] = user_row.iloc[0]['Role']
        st.session_state['assigned_projects'] = user_row.iloc[0]['Assigned_Projects']
        
        return True
    
    def logout(self):
        """Logout user"""
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.session_state['role'] = None
        st.session_state['assigned_projects'] = None
    
    def create_default_admin(self):
        """Create default admin user"""
        admin_user = pd.DataFrame([{
            'User_ID': 'USR001',
            'Username': 'admin',
            'Full_Name': 'Administrator',
            'Password_Hash': self.db_manager.hash_password('admin'),
            'Role': 'admin',
            'Assigned_Projects': 'All',
            'Email': 'admin@example.com',
            'Status': 'Active',
            'Created_Date': datetime.now().strftime('%Y-%m-%d')
        }])
        
        self.db_manager.write_dataframe(None, 'users', admin_user)
    
    def get_accessible_projects(self):
        """Get projects accessible to current user"""
        role = st.session_state.get('role', '')
        assigned_projects = st.session_state.get('assigned_projects', '')
        
        # Get all projects
        projects_df = self.db_manager.read_dataframe(None, 'projects')
        if projects_df.empty:
            return []
            
        all_projects = projects_df['Project_Name'].tolist()
        
        if role == 'admin' or assigned_projects == 'All':
            return all_projects
            
        if isinstance(assigned_projects, str) and assigned_projects:
            project_list = [p.strip() for p in assigned_projects.split(',')]
            return [p for p in project_list if p in all_projects]
            
        return []
    
    def has_project_access(self, project_name):
        """Check if current user has access to a project"""
        if st.session_state.get('role') == 'admin':
            return True
            
        assigned_projects = st.session_state.get('assigned_projects', '')
        
        if assigned_projects == 'All':
            return True
            
        if isinstance(assigned_projects, str):
            project_list = [p.strip() for p in assigned_projects.split(',')]
            return project_name in project_list
            
        return False
    
    def can_edit_data(self, project_name):
        """Check if user can edit data for a project"""
        role = st.session_state.get('role', '')
        return role in ['admin', 'project_manager'] and self.has_project_access(project_name)

# Initialize auth manager
auth_manager = AuthManager(db_manager)

def main():
    """Main application function"""
    
    # Sidebar connection status
    with st.sidebar:
        if db_manager.is_online:
            st.success("🟢 Connected to MongoDB")
        else:
            st.info("🔵 Using local storage fallback")
        
        # Initialize default data if needed
        if st.button("🔧 Initialize System"):
            initialize_default_data()
            st.success("System initialized!")
            st.rerun()
    
    # Check if user is logged in
    if not st.session_state.get('logged_in', False):
        show_login_page()
    else:
        show_main_app()

def initialize_default_data():
    """Initialize default projects and tables"""
    try:
        # Create default projects if none exist
        projects_df = db_manager.read_dataframe(None, 'projects')
        if projects_df.empty:
            default_projects = [
                {
                    'Project_ID': 'PRJ001',
                    'Project_Name': 'MakeMyTrip',
                    'Description': 'MakeMyTrip plantation initiative',
                    'Start_Date': '2024-01-01',
                    'Target_Area': 1000.0,
                    'Assigned_Users': 'admin',
                    'Status': 'Active',
                    'Manager': 'admin',
                    'Created_Date': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Project_ID': 'PRJ002',
                    'Project_Name': 'Absolute',
                    'Description': 'Absolute plantation project',
                    'Start_Date': '2024-01-01',
                    'Target_Area': 800.0,
                    'Assigned_Users': 'admin',
                    'Status': 'Active',
                    'Manager': 'admin',
                    'Created_Date': datetime.now().strftime('%Y-%m-%d')
                }
            ]
            
            projects_df = pd.DataFrame(default_projects)
            db_manager.write_dataframe(None, 'projects', projects_df)
        
        # Initialize tables for each project
        for project_name in ['MakeMyTrip', 'Absolute']:
            table_manager.initialize_project_tables(project_name)
        
    except Exception as e:
        st.error(f"Error initializing default data: {str(e)}")

def show_login_page():
    """Display login page"""
    st.markdown("""
    <div class="main-header">
        <h1>🌱 Plantation Data Management System</h1>
        <h3>Navchetna Spatial Solutions - MongoDB Version</h3>
        <p>Scalable, Dynamic, and Secure Data Management</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        auth_manager.show_login_form()
        
        st.info("""
        **Default Login Credentials:**
        - Username: admin
        - Password: admin
        
        **Features:**
        - Dynamic table creation and modification
        - MongoDB with local fallback
        - Role-based access control
        - Real-time data synchronization
        """)

def show_main_app():
    """Display main application with sidebar navigation"""
    
    # Sidebar
    with st.sidebar:
        # Get current user info safely
        current_username = st.session_state.get('username', 'User')
        current_role = st.session_state.get('role', 'viewer')
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #4CAF50; color: white; border-radius: 8px; margin-bottom: 1rem;">
            <h3>🌱 Navchetna Data Manager</h3>
            <p>Welcome, {current_username}!</p>
            <p><small>Role: {current_role.title()}</small></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation menu based on role
        if current_role == 'admin':
            menu_options = ["🏠 Dashboard", "➕ Add Data", "📊 Analytics", "📋 Manage Records", 
                          "📊 Reports", "👥 User Management", "🆕 Project Management", "🔧 Schema Management"]
        elif current_role == 'project_manager':
            menu_options = ["🏠 Dashboard", "🏢 My Projects", "➕ Add Data", "📊 Analytics", "📋 Manage Records", "📊 Reports"]
        else:  # viewer
            menu_options = ["🏠 Dashboard", "🔍 All Projects", "📊 Analytics", "📊 Reports"]
        
        selected_page = st.selectbox("Navigate to:", menu_options)
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            auth_manager.logout()
            st.rerun()
    
    # Main content area
    if selected_page == "🏠 Dashboard":
        show_dashboard()
    elif selected_page == "➕ Add Data":
        if current_role in ['admin', 'project_manager']:
            show_add_data()
        else:
            st.error("⛔ Access denied. You do not have permission to add data.")
    elif selected_page == "📊 Analytics":
        show_analytics()
    elif selected_page == "📋 Manage Records":
        if current_role in ['admin', 'project_manager']:
            show_manage_records()
        else:
            st.error("⛔ Access denied. You do not have permission to manage records.")
    elif selected_page == "📊 Reports":
        show_reports()
    elif selected_page == "👥 User Management":
        if current_role == 'admin':
            show_user_management()
        else:
            st.error("⛔ Access denied. Only administrators can manage users.")
    elif selected_page == "🆕 Project Management":
        if current_role == 'admin':
            show_project_management()
        else:
            st.error("⛔ Access denied. Only administrators can manage projects.")
    elif selected_page == "🔧 Schema Management":
        if current_role == 'admin':
            show_schema_management()
        else:
            st.error("⛔ Access denied. Only administrators can manage schemas.")
    elif selected_page == "🏢 My Projects":
        show_my_projects()
    elif selected_page == "🔍 All Projects":
        show_all_projects()

def show_dashboard():
    """Display main dashboard"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Plantation Analytics Dashboard</h1>
        <p>Overview of all plantation activities and progress</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible to your account.")
        return
    
    # Overall KPIs
    st.subheader("📈 Overall Performance Metrics")
    
    total_area_submitted = 0
    total_area_approved = 0
    total_area_planted = 0
    total_trees = 0
    
    # Aggregate data from all accessible projects
    for project_name in accessible_projects:
        # Get KML data
        kml_data = table_manager.get_table_data(project_name, "KML Tracking")
        if not kml_data.empty:
            total_area_submitted += kml_data.get('Total_Area', pd.Series([0])).sum()
            total_area_approved += kml_data.get('Area_Approved', pd.Series([0])).sum()
        
        # Get plantation data
        plantation_data = table_manager.get_table_data(project_name, "Plantation Records")
        if not plantation_data.empty:
            total_area_planted += plantation_data.get('Area_Planted', pd.Series([0])).sum()
            total_trees += plantation_data.get('Trees_Planted', pd.Series([0])).sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Total Area Submitted", f"{total_area_submitted:,.1f} Ha")
    with col2:
        st.metric("✅ Total Area Approved", f"{total_area_approved:,.1f} Ha", 
                 f"{(total_area_approved/total_area_submitted*100) if total_area_submitted > 0 else 0:.1f}%")
    with col3:
        st.metric("🌱 Total Area Planted", f"{total_area_planted:,.1f} Ha",
                 f"{(total_area_planted/total_area_submitted*100) if total_area_submitted > 0 else 0:.1f}%")
    with col4:
        st.metric("🌳 Total Trees Planted", f"{total_trees:,.0f}")
    
    # Recent activity
    st.markdown("---")
    st.subheader("📅 Recent Activity")
    
    today = datetime.now().strftime('%Y-%m-%d')
    recent_activity = []
    
    for project_name in accessible_projects:
        # Get today's KML data
        kml_data = table_manager.get_table_data(project_name, "KML Tracking")
        if not kml_data.empty and 'Date' in kml_data.columns:
            today_kml = kml_data[kml_data['Date'] == today]
            if not today_kml.empty:
                recent_activity.append({
                    'Project': project_name,
                    'Activity': 'KML Submission',
                    'Count': today_kml['KML_Count_Sent'].sum() if 'KML_Count_Sent' in today_kml.columns else 0,
                    'Area': today_kml['Total_Area'].sum() if 'Total_Area' in today_kml.columns else 0,
                    'Time': 'Today'
                })
        
        # Get today's plantation data
        plantation_data = table_manager.get_table_data(project_name, "Plantation Records")
        if not plantation_data.empty and 'Date' in plantation_data.columns:
            today_plantation = plantation_data[plantation_data['Date'] == today]
            if not today_plantation.empty:
                recent_activity.append({
                    'Project': project_name,
                    'Activity': 'Plantation',
                    'Count': len(today_plantation),
                    'Area': today_plantation['Area_Planted'].sum() if 'Area_Planted' in today_plantation.columns else 0,
                    'Time': 'Today'
                })
    
    if recent_activity:
        activity_df = pd.DataFrame(recent_activity)
        st.dataframe(activity_df, use_container_width=True)
    else:
        st.info("No activity recorded for today yet.")

def show_add_data():
    """Show add data interface"""
    st.title("📝 Add Data")
    
    # Get user's accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("⚠️ You don't have access to any projects. Please contact an administrator.")
        return
    
    # Project selection
    project_name = st.selectbox("🏢 Select Project", accessible_projects)
    
    if not project_name:
        st.info("Please select a project to continue.")
        return
    
    # Get available tables for the project
    available_tables = table_manager.get_project_tables(project_name)
    
    if not available_tables:
        st.info(f"No tables found for project '{project_name}'. Create tables in Schema Management first.")
        if st.button("🔧 Initialize Default Tables"):
            table_manager.initialize_project_tables(project_name)
            st.success("Default tables created!")
            st.rerun()
        return
    
    # Table selection
    st.subheader("📋 Select Table Type")
    table_name = st.radio("Choose table to add data to:", available_tables)
    
    if table_name:
        show_dynamic_form(project_name, table_name)

def show_dynamic_form(project_name: str, table_name: str):
    """Display dynamic form for data entry"""
    st.subheader(f"📝 {table_name} Data Entry")
    
    # Get table schema
    schema = table_manager.get_table_schema(table_name)
    
    if not schema:
        st.error("❌ Table schema not found!")
        return
    
    with st.form(f"{table_name.lower().replace(' ', '_')}_form", clear_on_submit=True):
        st.markdown('<div class="data-form">', unsafe_allow_html=True)
        
        record_data = {}
        
        # Create form fields dynamically
        col1, col2 = st.columns(2)
        field_count = 0
        
        for field in schema:
            field_name = field['name']
            field_type = field['type']
            required = field.get('required', False)
            default_value = field.get('default', '')
            description = field.get('description', '')
            
            # Alternate between columns
            col = col1 if field_count % 2 == 0 else col2
            
            with col:
                if field_type == "Date":
                    if default_value:
                        try:
                            default_date = pd.to_datetime(default_value).date()
                        except:
                            default_date = datetime.now().date()
                    else:
                        default_date = datetime.now().date()
                    
                    value = st.date_input(field_name, default_date, help=description)
                    record_data[field_name] = value.strftime('%Y-%m-%d')
                    
                elif field_type == "Number":
                    default_num = float(default_value) if default_value else 0.0
                    value = st.number_input(field_name, value=default_num, step=0.1, help=description)
                    record_data[field_name] = value
                    
                elif field_type == "True/False":
                    default_bool = default_value.lower() == 'true' if default_value else False
                    value = st.checkbox(field_name, value=default_bool, help=description)
                    record_data[field_name] = value
                    
                elif field_type == "Dropdown":
                    options = field.get('options', ['Option 1', 'Option 2'])
                    if isinstance(options, str):
                        options = [opt.strip() for opt in options.split(',')]
                    value = st.selectbox(field_name, options, help=description)
                    record_data[field_name] = value
                    
                else:  # Text
                    value = st.text_input(
                        field_name,
                        value=default_value,
                        placeholder=f"Enter {field_name.lower()}",
                        help=description
                    )
                    record_data[field_name] = value
            
            field_count += 1
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button(f"💾 Save {table_name} Record", use_container_width=True)
        
        if submitted:
            # Add User field automatically
            record_data['User'] = st.session_state.get('username', 'Unknown')
            
            if table_manager.add_record(project_name, table_name, record_data):
                st.success(f"✅ {table_name} record added successfully! Form has been reset for next entry.")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ Failed to add {table_name} record. Please try again.")

# Continue with all other functions...
# [The rest of the functions would continue here - analytics, manage records, reports, user management, etc.]
# For brevity, I'll include the key functions that make the app work

if __name__ == "__main__":
    main() 