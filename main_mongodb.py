#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete MongoDB-powered Plantation Data Management System
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
import hashlib
import plotly.express as px

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import configuration and managers
import config
from utils.mongodb_manager import MongoDBManager
from utils.table_manager import TableManager

# Configure Streamlit
st.set_page_config(
    page_title="Navchetna Plantation Manager - MongoDB",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize managers
@st.cache_resource
def get_managers():
    """Initialize and return managers"""
    db_manager = MongoDBManager()
    table_manager = TableManager(db_manager)
    return db_manager, table_manager

db_manager, table_manager = get_managers()

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
    
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        background: #f0f8ff;
        border-radius: 10px;
        margin-bottom: 1rem;
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
        user_row = users_df[users_df['username'] == username]
        if user_row.empty:
            return False
        
        # Check password
        hashed_password = self.db_manager.hash_password(password)
        # Handle both column name formats for backward compatibility
        password_col = 'Password_Hash' if 'Password_Hash' in user_row.columns else 'password'
        role_col = 'Role' if 'Role' in user_row.columns else 'role'
        projects_col = 'Assigned_Projects' if 'Assigned_Projects' in user_row.columns else 'assigned_projects'
        
        if user_row.iloc[0][password_col] != hashed_password:
            return False
        
        # Set session state
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.session_state['role'] = user_row.iloc[0][role_col]
        st.session_state['assigned_projects'] = user_row.iloc[0].get(projects_col, 'All')
        
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
    """Main application"""
    
    # Sidebar connection status
    with st.sidebar:
        if db_manager.is_online:
            st.success("🟢 Connected to MongoDB")
        else:
            st.info("🔵 Using local storage fallback")
        
        if st.button("🔧 Initialize System"):
            initialize_default_data()
            st.success("System initialized!")
            st.rerun()
    
    # Check if user is logged in
    if not st.session_state.get('logged_in', False):
        show_login_page()
    else:
        show_main_app()

def show_login_page():
    """Display login page"""
    st.markdown("""
    <div class="main-header">
        <h1>🌱 Plantation Data Management System</h1>
        <h3>Navchetna Spatial Solutions - MongoDB Version</h3>
    </div>
    """, unsafe_allow_html=True)
    
    auth_manager.show_login_form()

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
            menu_options = ["🏠 Dashboard", "➕ Add Data", "✏️ Manage Data", "📊 Analytics", "📋 Manage Records", 
                          "📊 Reports", "👥 User Management", "🆕 Project Management", "🔧 Schema Management"]
        elif current_role == 'project_manager':
            menu_options = ["🏠 Dashboard", "🏢 My Projects", "➕ Add Data", "✏️ Manage Data", "📊 Analytics", "📋 Manage Records", "📊 Reports"]
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
    elif selected_page == "✏️ Manage Data":
        if current_role in ['admin', 'project_manager']:
            show_manage_data()
        else:
            st.error("⛔ Access denied. You do not have permission to manage data.")
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

# Continue with page implementations...
def show_dashboard():
    """Display comprehensive client-ready dashboard with rich visualizations"""
    st.markdown("""
    <div class="main-header">
        <h1>🌱 Plantation Management Dashboard</h1>
        <p>Comprehensive insights and analytics for sustainable plantation projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible to your account.")
        return
    
    # Collect comprehensive data for visualizations
    project_data = {}
    total_area_submitted = 0
    total_area_approved = 0
    total_area_planted = 0
    total_trees = 0
    monthly_data = []
    daily_activity = []
    
    # Get dates for analysis
    today = datetime.now()
    last_30_days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
    last_7_days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    for project_name in accessible_projects:
        project_info = {
            'name': project_name,
            'total_area_submitted': 0,
            'total_area_approved': 0,
            'total_area_planted': 0,
            'total_trees': 0,
            'kml_records': 0,
            'plantation_records': 0,
            'approval_rate': 0
        }
        
        # Get KML data
        kml_data = table_manager.get_table_data(project_name, "KML Tracking")
        if not kml_data.empty:
            try:
                # Convert to numeric and handle non-numeric values
                total_area_series = pd.to_numeric(kml_data.get('Total_Area', pd.Series([0])), errors='coerce').fillna(0)
                approved_area_series = pd.to_numeric(kml_data.get('Area_Approved', pd.Series([0])), errors='coerce').fillna(0)
                
                project_submitted = total_area_series.sum()
                project_approved = approved_area_series.sum()
                
                project_info['total_area_submitted'] = project_submitted
                project_info['total_area_approved'] = project_approved
                project_info['kml_records'] = len(kml_data)
                project_info['approval_rate'] = (project_approved / project_submitted * 100) if project_submitted > 0 else 0
                
                total_area_submitted += project_submitted
                total_area_approved += project_approved
                
                # Collect daily data for trends
                if 'Date' in kml_data.columns:
                    for date in last_30_days:
                        day_data = kml_data[kml_data['Date'] == date]
                        if not day_data.empty:
                            daily_area = pd.to_numeric(day_data['Total_Area'], errors='coerce').fillna(0).sum()
                            if daily_area > 0:
                                daily_activity.append({
                                    'Date': date,
                                    'Project': project_name,
                                    'Area_Submitted': daily_area,
                                    'Type': 'KML Submission'
                                })
            except Exception as e:
                print(f"Error processing KML data for {project_name}: {str(e)}")
        
        # Get plantation data
        plantation_data = table_manager.get_table_data(project_name, "Plantation Records")
        if not plantation_data.empty:
            try:
                # Convert to numeric and handle non-numeric values
                planted_area_series = pd.to_numeric(plantation_data.get('Area_Planted', pd.Series([0])), errors='coerce').fillna(0)
                trees_planted_series = pd.to_numeric(plantation_data.get('Trees_Planted', pd.Series([0])), errors='coerce').fillna(0)
                
                project_planted = planted_area_series.sum()
                project_trees = trees_planted_series.sum()
                
                project_info['total_area_planted'] = project_planted
                project_info['total_trees'] = project_trees
                project_info['plantation_records'] = len(plantation_data)
                
                total_area_planted += project_planted
                total_trees += project_trees
                
                # Collect daily plantation data
                if 'Date' in plantation_data.columns:
                    for date in last_30_days:
                        day_data = plantation_data[plantation_data['Date'] == date]
                        if not day_data.empty:
                            daily_planted = pd.to_numeric(day_data['Area_Planted'], errors='coerce').fillna(0).sum()
                            daily_trees = pd.to_numeric(day_data['Trees_Planted'], errors='coerce').fillna(0).sum()
                            if daily_planted > 0:
                                daily_activity.append({
                                    'Date': date,
                                    'Project': project_name,
                                    'Area_Planted': daily_planted,
                                    'Trees_Planted': daily_trees,
                                    'Type': 'Plantation'
                                })
            except Exception as e:
                print(f"Error processing plantation data for {project_name}: {str(e)}")
        
        project_data[project_name] = project_info
    
    # === KEY METRICS SECTION ===
    st.subheader("📊 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🎯 Total Area Submitted", 
            f"{total_area_submitted:,.1f} Ha",
            help="Total area submitted across all projects"
        )
    with col2:
        approval_rate = (total_area_approved/total_area_submitted*100) if total_area_submitted > 0 else 0
        st.metric(
            "✅ Total Area Approved", 
            f"{total_area_approved:,.1f} Ha", 
            f"{approval_rate:.1f}%",
            help="Total approved area with approval rate"
        )
    with col3:
        planting_rate = (total_area_planted/total_area_submitted*100) if total_area_submitted > 0 else 0
        st.metric(
            "🌱 Total Area Planted", 
            f"{total_area_planted:,.1f} Ha",
            f"{planting_rate:.1f}%",
            help="Total planted area with completion rate"
        )
    with col4:
        trees_per_ha = total_trees/total_area_planted if total_area_planted > 0 else 0
        st.metric(
            "🌳 Total Trees Planted", 
            f"{total_trees:,.0f}",
            f"{trees_per_ha:.0f}/Ha",
            help="Total trees planted with density per hectare"
        )
    
    # === PROJECT COMPARISON CHARTS ===
    st.markdown("---")
    st.subheader("📈 Project Performance Comparison")
    
    # Create project comparison data
    if project_data:
        comparison_data = []
        for project_name, info in project_data.items():
            comparison_data.append({
                'Project': project_name,
                'Area Submitted (Ha)': info['total_area_submitted'],
                'Area Approved (Ha)': info['total_area_approved'],
                'Area Planted (Ha)': info['total_area_planted'],
                'Trees Planted': info['total_trees'],
                'Approval Rate (%)': info['approval_rate'],
                'KML Records': info['kml_records'],
                'Plantation Records': info['plantation_records']
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        if not comparison_df.empty:
            # Row 1: Area Comparison Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart for area comparison
                fig_area = px.bar(
                    comparison_df, 
                    x='Project', 
                    y=['Area Submitted (Ha)', 'Area Approved (Ha)', 'Area Planted (Ha)'],
                    title="📊 Area Progress by Project",
                    barmode='group',
                    color_discrete_map={
                        'Area Submitted (Ha)': '#3498db',
                        'Area Approved (Ha)': '#2ecc71', 
                        'Area Planted (Ha)': '#27ae60'
                    }
                )
                fig_area.update_layout(height=400, showlegend=True)
                st.plotly_chart(fig_area, use_container_width=True)
            
            with col2:
                # Pie chart for trees distribution
                fig_trees = px.pie(
                    comparison_df, 
                    values='Trees Planted', 
                    names='Project',
                    title="🌳 Trees Distribution by Project",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_trees.update_layout(height=400)
                st.plotly_chart(fig_trees, use_container_width=True)
            
            # Row 2: Performance Metrics
            col1, col2 = st.columns(2)
            
            with col1:
                # Approval rate comparison
                fig_approval = px.bar(
                    comparison_df, 
                    x='Project', 
                    y='Approval Rate (%)',
                    title="✅ Approval Rate by Project",
                    color='Approval Rate (%)',
                    color_continuous_scale='Greens'
                )
                fig_approval.update_layout(height=350)
                st.plotly_chart(fig_approval, use_container_width=True)
            
            with col2:
                # Records count comparison
                fig_records = px.bar(
                    comparison_df, 
                    x='Project', 
                    y=['KML Records', 'Plantation Records'],
                    title="📋 Activity Records by Project",
                    barmode='group',
                    color_discrete_map={
                        'KML Records': '#e74c3c',
                        'Plantation Records': '#f39c12'
                    }
                )
                fig_records.update_layout(height=350)
                st.plotly_chart(fig_records, use_container_width=True)
    
    # === TIMELINE ANALYSIS ===
    st.markdown("---")
    st.subheader("📅 Activity Timeline & Trends")
    
    if daily_activity:
        activity_df = pd.DataFrame(daily_activity)
        activity_df['Date'] = pd.to_datetime(activity_df['Date'])
        
        # Group by date and type for timeline
        timeline_data = []
        for date in last_30_days:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            day_activities = activity_df[activity_df['Date'] == date_obj]
            
            if not day_activities.empty:
                kml_activities = day_activities[day_activities['Type'] == 'KML Submission']
                plantation_activities = day_activities[day_activities['Type'] == 'Plantation']
                
                timeline_data.append({
                    'Date': date_obj,
                    'KML Area Submitted': kml_activities['Area_Submitted'].sum() if not kml_activities.empty else 0,
                    'Plantation Area': plantation_activities['Area_Planted'].sum() if not plantation_activities.empty else 0,
                    'Trees Planted': plantation_activities['Trees_Planted'].sum() if not plantation_activities.empty else 0
                })
        
        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Area timeline
                fig_timeline = px.line(
                    timeline_df, 
                    x='Date', 
                    y=['KML Area Submitted', 'Plantation Area'],
                    title="📈 Daily Area Progress Timeline",
                    labels={'value': 'Area (Ha)', 'variable': 'Activity Type'}
                )
                fig_timeline.update_layout(height=350)
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            with col2:
                # Trees planted timeline
                fig_trees_time = px.bar(
                    timeline_df, 
                    x='Date', 
                    y='Trees Planted',
                    title="🌳 Daily Trees Planted",
                    color='Trees Planted',
                    color_continuous_scale='Greens'
                )
                fig_trees_time.update_layout(height=350)
                st.plotly_chart(fig_trees_time, use_container_width=True)
    
    # === RECENT ACTIVITY TABLE ===
    st.markdown("---")
    st.subheader("🕒 Recent Activity (Last 7 Days)")
    
    recent_activity = []
    for project_name in accessible_projects:
        # Get recent KML data
        kml_data = table_manager.get_table_data(project_name, "KML Tracking")
        if not kml_data.empty and 'Date' in kml_data.columns:
            recent_kml = kml_data[kml_data['Date'].isin(last_7_days)]
            if not recent_kml.empty:
                try:
                    for date in last_7_days:
                        day_kml = recent_kml[recent_kml['Date'] == date]
                        if not day_kml.empty:
                            kml_count = pd.to_numeric(day_kml['KML_Count_Sent'], errors='coerce').fillna(0).sum() if 'KML_Count_Sent' in day_kml.columns else 0
                            total_area = pd.to_numeric(day_kml['Total_Area'], errors='coerce').fillna(0).sum() if 'Total_Area' in day_kml.columns else 0
                            
                            if kml_count > 0 or total_area > 0:
                                date_obj = datetime.strptime(date, '%Y-%m-%d')
                                if date == today.strftime('%Y-%m-%d'):
                                    time_label = 'Today'
                                elif date == (today - timedelta(days=1)).strftime('%Y-%m-%d'):
                                    time_label = 'Yesterday'
                                else:
                                    time_label = date_obj.strftime('%b %d')
                                
                                recent_activity.append({
                                    'Date': time_label,
                                    'Project': project_name,
                                    'Activity': 'KML Submission',
                                    'Count': int(kml_count),
                                    'Area (Ha)': f"{total_area:.1f}",
                                    'Status': '📋 Submitted'
                                })
                except Exception as e:
                    print(f"Error processing recent KML data for {project_name}: {str(e)}")
        
        # Get recent plantation data
        plantation_data = table_manager.get_table_data(project_name, "Plantation Records")
        if not plantation_data.empty and 'Date' in plantation_data.columns:
            recent_plantation = plantation_data[plantation_data['Date'].isin(last_7_days)]
            if not recent_plantation.empty:
                try:
                    for date in last_7_days:
                        day_plantation = recent_plantation[recent_plantation['Date'] == date]
                        if not day_plantation.empty:
                            planted_area = pd.to_numeric(day_plantation['Area_Planted'], errors='coerce').fillna(0).sum() if 'Area_Planted' in day_plantation.columns else 0
                            trees_count = pd.to_numeric(day_plantation['Trees_Planted'], errors='coerce').fillna(0).sum() if 'Trees_Planted' in day_plantation.columns else 0
                            
                            if len(day_plantation) > 0:
                                date_obj = datetime.strptime(date, '%Y-%m-%d')
                                if date == today.strftime('%Y-%m-%d'):
                                    time_label = 'Today'
                                elif date == (today - timedelta(days=1)).strftime('%Y-%m-%d'):
                                    time_label = 'Yesterday'
                                else:
                                    time_label = date_obj.strftime('%b %d')
                                
                                recent_activity.append({
                                    'Date': time_label,
                                    'Project': project_name,
                                    'Activity': 'Plantation',
                                    'Count': f"{len(day_plantation)} plots",
                                    'Area (Ha)': f"{planted_area:.1f}",
                                    'Status': f'🌳 {int(trees_count)} trees'
                                })
                except Exception as e:
                    print(f"Error processing recent plantation data for {project_name}: {str(e)}")
    
    if recent_activity:
        # Sort by most recent first
        activity_df = pd.DataFrame(recent_activity)
        date_order = {'Today': 0, 'Yesterday': 1}
        activity_df['sort_key'] = activity_df['Date'].map(lambda x: date_order.get(x, 2))
        activity_df = activity_df.sort_values('sort_key').drop('sort_key', axis=1)
        
        st.dataframe(activity_df, use_container_width=True, hide_index=True)
    else:
        st.info("💡 No recent activity found. Start by adding some KML or plantation data!")
    
    # === SUMMARY INSIGHTS ===
    st.markdown("---")
    st.subheader("💡 Key Insights & Recommendations")
    
    insights_col1, insights_col2 = st.columns(2)
    
    with insights_col1:
        st.markdown("### 📈 Performance Highlights")
        if total_area_submitted > 0:
            efficiency = (total_area_planted / total_area_submitted * 100)
            if efficiency > 80:
                st.success(f"🎉 Excellent plantation efficiency: {efficiency:.1f}%")
            elif efficiency > 60:
                st.info(f"👍 Good plantation progress: {efficiency:.1f}%")
            else:
                st.warning(f"⚠️ Plantation efficiency needs improvement: {efficiency:.1f}%")
        
        if total_trees > 0 and total_area_planted > 0:
            tree_density = total_trees / total_area_planted
            st.metric("🌳 Average Tree Density", f"{tree_density:.0f} trees/Ha")
    
    with insights_col2:
        st.markdown("### 🎯 Recommendations")
        if project_data:
            best_project = max(project_data.items(), key=lambda x: x[1]['approval_rate'])
            if best_project[1]['approval_rate'] > 0:
                st.success(f"🏆 Best performing project: **{best_project[0]}** ({best_project[1]['approval_rate']:.1f}% approval rate)")
            
            total_projects = len([p for p in project_data.values() if p['total_area_submitted'] > 0])
            if total_projects > 1:
                st.info(f"📊 Monitoring {total_projects} active projects")
            
            if total_area_submitted > total_area_planted:
                pending_area = total_area_submitted - total_area_planted
                st.warning(f"⏳ {pending_area:.1f} Ha pending plantation")

def show_add_data():
    """Display add data page"""
    st.markdown("""
    <div class="main-header">
        <h1>➕ Add New Data</h1>
        <p>Add new records to your projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible to your account.")
        return
    
    # Project selection
    selected_project = st.selectbox("Select Project", accessible_projects)
    
    if selected_project:
        # Get available tables for the project
        tables = table_manager.get_project_tables(selected_project)
        
        if not tables:
            st.warning(f"No tables found for project '{selected_project}'. Create tables in Schema Management first.")
            return
        
        # Table selection
        selected_table = st.selectbox("Select Table", tables)
        
        if selected_table:
            # Get table schema
            schema = table_manager.get_table_schema(selected_table)
            
            if schema:
                st.subheader(f"Add data to {selected_table}")
                
                # Show existing data first
                existing_data = table_manager.get_table_data(selected_project, selected_table)
                if not existing_data.empty:
                    with st.expander(f"📊 Current data in {selected_table} ({len(existing_data)} records)"):
                        st.dataframe(existing_data, use_container_width=True)
                
                # Create form for data entry
                with st.form(f"add_data_{selected_table}"):
                    new_record = {}
                    
                    # Create two columns for better layout
                    col1, col2 = st.columns(2)
                    
                    for i, field in enumerate(schema):
                        field_name = field.get('name', '')
                        field_type = field.get('type', 'text')
                        required = field.get('required', False)
                        default_value = field.get('default', '')
                        
                        # Alternate between columns
                        current_col = col1 if i % 2 == 0 else col2
                        
                        with current_col:
                            # Handle date fields (case-insensitive)
                            if field_type.lower() in ['date', 'datetime']:
                                try:
                                    default_date = datetime.strptime(default_value, '%Y-%m-%d').date() if default_value else datetime.now().date()
                                except:
                                    default_date = datetime.now().date()
                                
                                new_record[field_name] = st.date_input(
                                    f"📅 {field_name} {'*' if required else ''}",
                                    value=default_date,
                                    key=f"add_data_{field_name}",
                                    help="Select date from calendar"
                                )
                            elif field_type.lower() in ['number', 'numeric', 'integer', 'float']:
                                try:
                                    default_num = float(default_value) if default_value else 0.0
                                except:
                                    default_num = 0.0
                                
                                new_record[field_name] = st.number_input(
                                    f"🔢 {field_name} {'*' if required else ''}",
                                    value=default_num,
                                    key=f"add_data_{field_name}"
                                )
                            elif field_type.lower() in ['textarea', 'longtext']:
                                new_record[field_name] = st.text_area(
                                    f"📝 {field_name} {'*' if required else ''}",
                                    value=default_value,
                                    key=f"add_data_{field_name}"
                                )
                            elif field_type.lower() in ['select', 'choice', 'dropdown']:
                                # For select fields, you might want to define options
                                options = ['Option 1', 'Option 2', 'Option 3']  # This could be dynamic
                                new_record[field_name] = st.selectbox(
                                    f"📋 {field_name} {'*' if required else ''}",
                                    options,
                                    index=0 if default_value in options else 0,
                                    key=f"add_data_{field_name}"
                                )
                            else:  # text
                                # Auto-populate User field with logged-in user
                                if field_name.lower() in ['user', 'username', 'created_by', 'entered_by']:
                                    default_user_value = st.session_state.get('username', default_value)
                                else:
                                    default_user_value = default_value
                                
                                new_record[field_name] = st.text_input(
                                    f"✏️ {field_name} {'*' if required else ''}",
                                    value=default_user_value,
                                    key=f"add_data_{field_name}"
                                )
                    
                    submitted = st.form_submit_button("➕ Add Record", use_container_width=True)
                    
                    if submitted:
                        # Validate required fields
                        missing_fields = []
                        for field in schema:
                            field_name = field.get('name', '')
                            if field.get('required', False) and not str(new_record.get(field_name, '')).strip():
                                missing_fields.append(field_name)
                        
                        if missing_fields:
                            st.error(f"Please fill in required fields: {', '.join(missing_fields)}")
                        else:
                            # Convert date objects to strings
                            for key, value in new_record.items():
                                if hasattr(value, 'strftime'):
                                    new_record[key] = value.strftime('%Y-%m-%d')
                            
                            # Add timestamp
                            new_record['_created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            new_record['_created_by'] = st.session_state.get('username', 'Unknown')
                            
                            # Add record
                            if table_manager.add_record(selected_project, selected_table, new_record):
                                st.success("Record added successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to add record.")
            else:
                st.warning(f"No schema defined for table '{selected_table}'. Please define the table structure in Schema Management first.")

def show_manage_data():
    """Display data management page for editing and deleting records"""
    st.markdown("""
    <div class="main-header">
        <h1>✏️ Manage Data</h1>
        <p>Edit, update, and delete records in your projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible to your account.")
        return
    
    # Project and table selection
    col1, col2 = st.columns(2)
    
    with col1:
        selected_project = st.selectbox("Select Project", accessible_projects)
    
    with col2:
        if selected_project:
            tables = table_manager.get_project_tables(selected_project)
            selected_table = st.selectbox("Select Table", tables if tables else ["No tables found"])
        else:
            selected_table = None
    
    if selected_project and selected_table and selected_table != "No tables found":
        # Get table data
        data = table_manager.get_table_data(selected_project, selected_table)
        
        if not data.empty:
            st.subheader(f"📊 Data in {selected_table}")
            
            # Tab layout for different operations
            tab1, tab2, tab3 = st.tabs(["👀 View Data", "✏️ Edit Records", "🗑️ Delete Records"])
            
            with tab1:
                st.write(f"**Total Records:** {len(data)}")
                
                # Search and filter
                search_term = st.text_input("🔍 Search in data", placeholder="Type to search...")
                
                if search_term:
                    # Search across all text columns
                    mask = data.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                    filtered_data = data[mask]
                    st.write(f"**Filtered Results:** {len(filtered_data)} records")
                else:
                    filtered_data = data
                
                # Display data with pagination
                if len(filtered_data) > 50:
                    page_size = st.selectbox("Records per page", [10, 25, 50, 100], index=2)
                    total_pages = (len(filtered_data) - 1) // page_size + 1
                    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
                    
                    start_idx = (page - 1) * page_size
                    end_idx = start_idx + page_size
                    display_data = filtered_data.iloc[start_idx:end_idx]
                    
                    st.write(f"Showing records {start_idx + 1} to {min(end_idx, len(filtered_data))} of {len(filtered_data)}")
                else:
                    display_data = filtered_data
                
                st.dataframe(display_data, use_container_width=True)
                
                # Export option
                if not filtered_data.empty:
                    csv = filtered_data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"{selected_project}_{selected_table}_data.csv",
                        mime="text/csv"
                    )
            
            with tab2:
                st.subheader("✏️ Edit Record")
                
                if len(data) > 0:
                    # Select record to edit
                    record_options = [f"Record {i+1}: {' | '.join([str(data.iloc[i, j])[:30] + ('...' if len(str(data.iloc[i, j])) > 30 else '') for j in range(min(3, len(data.columns)))])}" 
                                    for i in range(len(data))]
                    
                    selected_record_idx = st.selectbox("Select Record to Edit", 
                                                     range(len(record_options)), 
                                                     format_func=lambda x: record_options[x])
                    
                    if selected_record_idx is not None:
                        record = data.iloc[selected_record_idx]
                        
                        st.write("**Current Record:**")
                        current_record_df = pd.DataFrame([record]).T
                        current_record_df.columns = ['Current Value']
                        st.dataframe(current_record_df, use_container_width=True)
                        
                        # Get table schema for proper input types
                        schema = table_manager.get_table_schema(selected_table)
                        
                        # Edit form
                        with st.form("edit_record"):
                            st.write("**Edit Values:**")
                            updated_data = {}
                            
                            # Create columns for better layout
                            col1, col2 = st.columns(2)
                            
                            for i, (field_name, current_value) in enumerate(record.items()):
                                # Skip system fields
                                if field_name.startswith('_'):
                                    continue
                                
                                # Find field schema
                                field_schema = None
                                if schema:
                                    field_schema = next((f for f in schema if f.get('name') == field_name), None)
                                
                                field_type = field_schema.get('type', 'text') if field_schema else 'text'
                                
                                # Alternate between columns
                                current_col = col1 if i % 2 == 0 else col2
                                
                                with current_col:
                                    if field_type == 'date':
                                        try:
                                            if pd.isna(current_value) or current_value == '':
                                                default_date = datetime.now().date()
                                            else:
                                                default_date = pd.to_datetime(current_value).date()
                                        except:
                                            default_date = datetime.now().date()
                                        
                                        updated_data[field_name] = st.date_input(
                                            f"📅 {field_name}", 
                                            value=default_date, 
                                            key=f"edit_{field_name}",
                                            help="Select date from calendar"
                                        )
                                    elif field_type == 'number':
                                        try:
                                            default_num = float(current_value) if not pd.isna(current_value) else 0.0
                                        except:
                                            default_num = 0.0
                                        
                                        updated_data[field_name] = st.number_input(f"🔢 {field_name}", value=default_num, key=f"edit_{field_name}")
                                    elif field_type == 'textarea':
                                        updated_data[field_name] = st.text_area(f"📝 {field_name}", value=str(current_value) if not pd.isna(current_value) else '', key=f"edit_{field_name}")
                                    else:  # text
                                        # For user fields, show current user as option but allow editing
                                        current_text_value = str(current_value) if not pd.isna(current_value) else ''
                                        if field_name.lower() in ['user', 'username', 'created_by', 'entered_by'] and not current_text_value:
                                            current_text_value = st.session_state.get('username', '')
                                        
                                        updated_data[field_name] = st.text_input(f"✏️ {field_name}", value=current_text_value, key=f"edit_{field_name}")
                            
                            # Add update timestamp
                            updated_data['_updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            updated_data['_updated_by'] = st.session_state.get('username', 'Unknown')
                            
                            submitted = st.form_submit_button("💾 Update Record", use_container_width=True)
                            
                            if submitted:
                                # Convert date objects to strings
                                for key, value in updated_data.items():
                                    if hasattr(value, 'strftime'):
                                        updated_data[key] = value.strftime('%Y-%m-%d')
                                
                                if table_manager.update_record(selected_project, selected_table, selected_record_idx, updated_data):
                                    st.success("Record updated successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to update record.")
                else:
                    st.info("No records available to edit.")
            
            with tab3:
                st.subheader("🗑️ Delete Records")
                st.warning("⚠️ **Warning:** Deleting records is permanent and cannot be undone!")
                
                if len(data) > 0:
                    # Select records to delete
                    record_options = [f"Record {i+1}: {' | '.join([str(data.iloc[i, j])[:30] + ('...' if len(str(data.iloc[i, j])) > 30 else '') for j in range(min(3, len(data.columns)))])}" 
                                    for i in range(len(data))]
                    
                    selected_records = st.multiselect("Select Records to Delete", 
                                                    range(len(record_options)), 
                                                    format_func=lambda x: record_options[x])
                    
                    if selected_records:
                        st.write("**Records to be deleted:**")
                        delete_preview = data.iloc[selected_records]
                        st.dataframe(delete_preview, use_container_width=True)
                        
                        # Confirmation
                        confirm_delete = st.checkbox("I understand that this action cannot be undone")
                        
                        if st.button("🗑️ Delete Selected Records", disabled=not confirm_delete, use_container_width=True):
                            # Delete records (in reverse order to maintain indices)
                            for idx in sorted(selected_records, reverse=True):
                                table_manager.delete_record(selected_project, selected_table, idx)
                            
                            st.success(f"Deleted {len(selected_records)} record(s) successfully!")
                            st.rerun()
                else:
                    st.info("No records available to delete.")
        else:
            st.info(f"No data found in {selected_table}")
    else:
        st.info("Please select a project and table to manage data.")

def show_analytics():
    """Display analytics page"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Analytics</h1>
        <p>Detailed analytics and visualizations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible to your account.")
        return
    
    # Project selection
    selected_project = st.selectbox("Select Project for Analytics", accessible_projects)
    
    if selected_project:
        # Get KML and Plantation data
        kml_data = table_manager.get_table_data(selected_project, "KML Tracking")
        plantation_data = table_manager.get_table_data(selected_project, "Plantation Records")
        
        # Display charts if data exists
        if not kml_data.empty or not plantation_data.empty:
            # Area Analysis
            if not kml_data.empty and 'Total_Area' in kml_data.columns:
                st.subheader("📏 Area Analysis")
                
                # Area over time
                if 'Date' in kml_data.columns:
                    area_by_date = kml_data.groupby('Date')['Total_Area'].sum().reset_index()
                    
                    fig = px.line(area_by_date, x='Date', y='Total_Area',
                                title='Area Submitted Over Time',
                                labels={'Total_Area': 'Area (Ha)', 'Date': 'Date'})
                    st.plotly_chart(fig, use_container_width=True)
            
            # Plantation Analysis
            if not plantation_data.empty:
                st.subheader("🌱 Plantation Analysis")
                
                if 'Trees_Planted' in plantation_data.columns:
                    total_trees = plantation_data['Trees_Planted'].sum()
                    st.metric("Total Trees Planted", f"{total_trees:,.0f}")
                
                if 'Date' in plantation_data.columns and 'Trees_Planted' in plantation_data.columns:
                    trees_by_date = plantation_data.groupby('Date')['Trees_Planted'].sum().reset_index()
                    
                    fig = px.bar(trees_by_date, x='Date', y='Trees_Planted',
                               title='Trees Planted Over Time',
                               labels={'Trees_Planted': 'Trees', 'Date': 'Date'})
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for analytics.")

def show_manage_records():
    """Display manage records page"""
    st.markdown("""
    <div class="main-header">
        <h1>📋 Manage Records</h1>
        <p>View, edit, and delete existing records</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible to your account.")
        return
    
    # Project selection
    selected_project = st.selectbox("Select Project", accessible_projects)
    
    if selected_project:
        # Get available tables
        tables = table_manager.get_project_tables(selected_project)
        
        if tables:
            selected_table = st.selectbox("Select Table", tables)
            
            if selected_table:
                # Get data
                data = table_manager.get_table_data(selected_project, selected_table)
                
                if not data.empty:
                    st.subheader(f"Records in {selected_table}")
                    
                    # Display data with edit/delete options
                    edited_data = st.data_editor(
                        data,
                        use_container_width=True,
                        num_rows="dynamic"
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Save Changes"):
                            if table_manager.update_table_data(selected_project, selected_table, edited_data):
                                st.success("Changes saved successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to save changes.")
                    
                    with col2:
                        if st.button("Export Data"):
                            csv = edited_data.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"{selected_project}_{selected_table}.csv",
                                mime="text/csv"
                            )
                else:
                    st.info("No records found in this table.")

def show_reports():
    """Display comprehensive dynamic reports with download functionality"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Comprehensive Reports</h1>
        <p>Generate dynamic reports with daily, weekly, and monthly analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible to your account.")
        return
    
    # Report configuration sidebar
    with st.sidebar:
        st.header("📋 Report Configuration")
        
        # Project selection
        selected_projects = st.multiselect(
            "Select Projects", 
            accessible_projects, 
            default=accessible_projects,
            help="Choose projects to include in the report"
        )
        
        # Date range selection
        st.subheader("📅 Date Range")
        today = datetime.now().date()
        
        date_range_option = st.radio("Select Date Range", [
            "Last 7 Days",
            "Last 30 Days", 
            "Last 90 Days",
            "Custom Range"
        ])
        
        if date_range_option == "Last 7 Days":
            start_date = today - timedelta(days=7)
            end_date = today
        elif date_range_option == "Last 30 Days":
            start_date = today - timedelta(days=30)
            end_date = today
        elif date_range_option == "Last 90 Days":
            start_date = today - timedelta(days=90)
            end_date = today
        else:  # Custom Range
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=today - timedelta(days=30))
            with col2:
                end_date = st.date_input("End Date", value=today)
        
        # Report format selection
        st.subheader("📄 Export Options")
        export_format = st.selectbox("Export Format", ["Excel (.xlsx)", "CSV (.csv)", "PDF Report"])
    
    if not selected_projects:
        st.warning("Please select at least one project to generate reports.")
        return
    
    # Main report tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Executive Summary", 
        "📅 Daily Reports", 
        "📈 Weekly Analysis", 
        "📆 Monthly Overview",
        "📤 Data Export"
    ])
    
    # Collect data for all selected projects
    all_kml_data = []
    all_plantation_data = []
    project_summaries = {}
    
    for project_name in selected_projects:
        kml_data = table_manager.get_table_data(project_name, "KML Tracking")
        plantation_data = table_manager.get_table_data(project_name, "Plantation Records")
        
        # Filter by date range
        if not kml_data.empty and 'Date' in kml_data.columns:
            kml_data['Date'] = pd.to_datetime(kml_data['Date']).dt.date
            kml_data = kml_data[(kml_data['Date'] >= start_date) & (kml_data['Date'] <= end_date)]
            kml_data['Project'] = project_name
            all_kml_data.append(kml_data)
        
        if not plantation_data.empty and 'Date' in plantation_data.columns:
            plantation_data['Date'] = pd.to_datetime(plantation_data['Date']).dt.date
            plantation_data = plantation_data[(plantation_data['Date'] >= start_date) & (plantation_data['Date'] <= end_date)]
            plantation_data['Project'] = project_name
            all_plantation_data.append(plantation_data)
        
        # Calculate project summary
        project_summaries[project_name] = calculate_project_summary(kml_data, plantation_data)
    
    # Combine all data
    combined_kml = pd.concat(all_kml_data, ignore_index=True) if all_kml_data else pd.DataFrame()
    combined_plantation = pd.concat(all_plantation_data, ignore_index=True) if all_plantation_data else pd.DataFrame()
    
    # === EXECUTIVE SUMMARY TAB ===
    with tab1:
        st.subheader("📊 Executive Summary")
        st.write(f"**Report Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
        
        # Overall KPIs
        total_area_submitted = sum([s['total_area_submitted'] for s in project_summaries.values()])
        total_area_approved = sum([s['total_area_approved'] for s in project_summaries.values()])
        total_area_planted = sum([s['total_area_planted'] for s in project_summaries.values()])
        total_trees = sum([s['total_trees'] for s in project_summaries.values()])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Area Submitted", f"{total_area_submitted:,.1f} Ha")
        with col2:
            approval_rate = (total_area_approved/total_area_submitted*100) if total_area_submitted > 0 else 0
            st.metric("✅ Area Approved", f"{total_area_approved:,.1f} Ha", f"{approval_rate:.1f}%")
        with col3:
            planting_rate = (total_area_planted/total_area_submitted*100) if total_area_submitted > 0 else 0
            st.metric("🌱 Area Planted", f"{total_area_planted:,.1f} Ha", f"{planting_rate:.1f}%")
        with col4:
            st.metric("🌳 Trees Planted", f"{total_trees:,.0f}")
        
        # Project comparison chart
        if project_summaries:
            st.subheader("📈 Project Performance Comparison")
            
            comparison_data = []
            for project, summary in project_summaries.items():
                comparison_data.append({
                    'Project': project,
                    'Area Submitted': summary['total_area_submitted'],
                    'Area Approved': summary['total_area_approved'],
                    'Area Planted': summary['total_area_planted'],
                    'Trees Planted': summary['total_trees'],
                    'Approval Rate (%)': (summary['total_area_approved']/summary['total_area_submitted']*100) if summary['total_area_submitted'] > 0 else 0
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(comparison_df, x='Project', y=['Area Submitted', 'Area Approved', 'Area Planted'],
                           title="Area Progress by Project", barmode='group')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(comparison_df, x='Project', y='Approval Rate (%)',
                           title="Approval Rate by Project", color='Approval Rate (%)', color_continuous_scale='Greens')
                st.plotly_chart(fig, use_container_width=True)
        
        # Generate executive summary report
        executive_summary = generate_executive_summary(project_summaries, start_date, end_date)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📋 Summary Report")
            st.markdown(executive_summary)
        
        with col2:
            st.subheader("📥 Download Summary")
            summary_data = create_summary_report_data(project_summaries, start_date, end_date)
            
            if export_format == "Excel (.xlsx)":
                excel_buffer = create_excel_report(summary_data, "Executive_Summary")
                st.download_button(
                    "📊 Download Excel Report",
                    excel_buffer,
                    file_name=f"Executive_Summary_{start_date}_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif export_format == "CSV (.csv)":
                csv_data = summary_data.to_csv(index=False)
                st.download_button(
                    "📊 Download CSV Report",
                    csv_data,
                    file_name=f"Executive_Summary_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
            elif export_format == "PDF Report":
                pdf_buffer = create_pdf_report(summary_data, executive_summary, "Executive Summary", start_date, end_date)
                st.download_button(
                    "📄 Download PDF Report",
                    pdf_buffer,
                    file_name=f"Executive_Summary_{start_date}_{end_date}.pdf",
                    mime="application/pdf"
                )
    
    # === DAILY REPORTS TAB ===
    with tab2:
        st.subheader("📅 Daily Activity Reports")
        
        if not combined_kml.empty or not combined_plantation.empty:
            # Daily summary
            daily_summary = create_daily_summary(combined_kml, combined_plantation, start_date, end_date)
            
            if not daily_summary.empty:
                st.subheader("📊 Daily Activity Overview")
                
                # Daily charts
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.line(daily_summary, x='Date', y=['KML_Area_Submitted', 'Plantation_Area'],
                                title="Daily Area Activity", labels={'value': 'Area (Ha)'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.bar(daily_summary, x='Date', y='Trees_Planted',
                               title="Daily Trees Planted", color='Trees_Planted', color_continuous_scale='Greens')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Daily data table
                st.subheader("📋 Daily Summary Table")
                st.dataframe(daily_summary, use_container_width=True)
                
                # Download daily report
                st.subheader("📥 Download Daily Report")
                if export_format == "Excel (.xlsx)":
                    excel_buffer = create_excel_report(daily_summary, "Daily_Report")
                    st.download_button(
                        "📊 Download Daily Excel Report",
                        excel_buffer,
                        file_name=f"Daily_Report_{start_date}_{end_date}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                elif export_format == "CSV (.csv)":
                    csv_data = daily_summary.to_csv(index=False)
                    st.download_button(
                        "📊 Download Daily CSV Report",
                        csv_data,
                        file_name=f"Daily_Report_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
                elif export_format == "PDF Report":
                    pdf_buffer = create_pdf_report(daily_summary, "Daily activity report with area and tree planting data", "Daily Report", start_date, end_date)
                    st.download_button(
                        "📄 Download Daily PDF Report",
                        pdf_buffer,
                        file_name=f"Daily_Report_{start_date}_{end_date}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("No daily activity data available for the selected period.")
    
    # === WEEKLY ANALYSIS TAB ===
    with tab3:
        st.subheader("📈 Weekly Analysis")
        
        if not combined_kml.empty or not combined_plantation.empty:
            # Weekly summary
            weekly_summary = create_weekly_summary(combined_kml, combined_plantation, start_date, end_date)
            
            if not weekly_summary.empty:
                st.subheader("📊 Weekly Performance Overview")
                
                # Weekly charts
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.bar(weekly_summary, x='Week', y=['KML_Area_Submitted', 'Plantation_Area'],
                               title="Weekly Area Progress", barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.line(weekly_summary, x='Week', y='Cumulative_Trees',
                                title="Cumulative Trees Planted", markers=True)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Weekly trends
                st.subheader("📈 Weekly Trends Analysis")
                weekly_trends = analyze_weekly_trends(weekly_summary)
                st.markdown(weekly_trends)
                
                # Weekly data table
                st.subheader("📋 Weekly Summary Table")
                st.dataframe(weekly_summary, use_container_width=True)
                
                # Download weekly report
                st.subheader("📥 Download Weekly Report")
                if export_format == "Excel (.xlsx)":
                    excel_buffer = create_excel_report(weekly_summary, "Weekly_Report")
                    st.download_button(
                        "📊 Download Weekly Excel Report",
                        excel_buffer,
                        file_name=f"Weekly_Report_{start_date}_{end_date}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                elif export_format == "CSV (.csv)":
                    csv_data = weekly_summary.to_csv(index=False)
                    st.download_button(
                        "📊 Download Weekly CSV Report",
                        csv_data,
                        file_name=f"Weekly_Report_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
                elif export_format == "PDF Report":
                    pdf_buffer = create_pdf_report(weekly_summary, weekly_trends, "Weekly Analysis", start_date, end_date)
                    st.download_button(
                        "📄 Download Weekly PDF Report",
                        pdf_buffer,
                        file_name=f"Weekly_Report_{start_date}_{end_date}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("No weekly analysis data available for the selected period.")
    
    # === MONTHLY OVERVIEW TAB ===
    with tab4:
        st.subheader("📆 Monthly Overview")
        
        if not combined_kml.empty or not combined_plantation.empty:
            # Monthly summary
            monthly_summary = create_monthly_summary(combined_kml, combined_plantation, start_date, end_date)
            
            if not monthly_summary.empty:
                st.subheader("📊 Monthly Performance Overview")
                
                # Monthly charts
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.bar(monthly_summary, x='Month', y=['KML_Area_Submitted', 'Plantation_Area'],
                               title="Monthly Area Progress", barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.pie(monthly_summary, values='Trees_Planted', names='Month',
                               title="Monthly Trees Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Monthly insights
                st.subheader("💡 Monthly Insights")
                monthly_insights = generate_monthly_insights(monthly_summary)
                st.markdown(monthly_insights)
                
                # Monthly data table
                st.subheader("📋 Monthly Summary Table")
                st.dataframe(monthly_summary, use_container_width=True)
                
                # Download monthly report
                st.subheader("📥 Download Monthly Report")
                if export_format == "Excel (.xlsx)":
                    excel_buffer = create_excel_report(monthly_summary, "Monthly_Report")
                    st.download_button(
                        "📊 Download Monthly Excel Report",
                        excel_buffer,
                        file_name=f"Monthly_Report_{start_date}_{end_date}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                elif export_format == "CSV (.csv)":
                    csv_data = monthly_summary.to_csv(index=False)
                    st.download_button(
                        "📊 Download Monthly CSV Report",
                        csv_data,
                        file_name=f"Monthly_Report_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
                elif export_format == "PDF Report":
                    pdf_buffer = create_pdf_report(monthly_summary, monthly_insights, "Monthly Overview", start_date, end_date)
                    st.download_button(
                        "📄 Download Monthly PDF Report",
                        pdf_buffer,
                        file_name=f"Monthly_Report_{start_date}_{end_date}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("No monthly overview data available for the selected period.")
    
    # === DATA EXPORT TAB ===
    with tab5:
        st.subheader("📤 Comprehensive Data Export")
        
        export_option = st.selectbox("Select Export Type", [
            "All Project Data",
            "Filtered Data by Project",
            "Custom Data Selection"
        ])
        
        if export_option == "All Project Data":
            st.write("**Export all data for selected projects and date range**")
            
            # Combine all data for export
            export_data = {}
            
            if not combined_kml.empty:
                export_data['KML_Tracking'] = combined_kml
            
            if not combined_plantation.empty:
                export_data['Plantation_Records'] = combined_plantation
            
            if export_data:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if export_format == "Excel (.xlsx)":
                        excel_buffer = create_multi_sheet_excel(export_data)
                        st.download_button(
                            "📊 Download Complete Excel Report",
                            excel_buffer,
                            file_name=f"Complete_Data_Export_{start_date}_{end_date}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                
                with col2:
                    # ZIP file with multiple CSVs
                    zip_buffer = create_csv_zip(export_data, start_date, end_date)
                    st.download_button(
                        "📦 Download CSV Package",
                        zip_buffer,
                        file_name=f"Complete_Data_Export_{start_date}_{end_date}.zip",
                        mime="application/zip"
                    )
                
                with col3:
                    # Summary statistics
                    st.metric("📊 KML Records", len(combined_kml) if not combined_kml.empty else 0)
                    st.metric("🌱 Plantation Records", len(combined_plantation) if not combined_plantation.empty else 0)
        
        elif export_option == "Filtered Data by Project":
            selected_export_project = st.selectbox("Select Project for Export", selected_projects)
            
            if selected_export_project:
                project_kml = combined_kml[combined_kml['Project'] == selected_export_project] if not combined_kml.empty else pd.DataFrame()
                project_plantation = combined_plantation[combined_plantation['Project'] == selected_export_project] if not combined_plantation.empty else pd.DataFrame()
                
                project_export_data = {}
                if not project_kml.empty:
                    project_export_data['KML_Tracking'] = project_kml
                if not project_plantation.empty:
                    project_export_data['Plantation_Records'] = project_plantation
                
                if project_export_data:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if export_format == "Excel (.xlsx)":
                            excel_buffer = create_multi_sheet_excel(project_export_data)
                            st.download_button(
                                f"📊 Download {selected_export_project} Excel Report",
                                excel_buffer,
                                file_name=f"{selected_export_project}_Export_{start_date}_{end_date}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    
                    with col2:
                        zip_buffer = create_csv_zip(project_export_data, start_date, end_date)
                        st.download_button(
                            f"📦 Download {selected_export_project} CSV Package",
                            zip_buffer,
                            file_name=f"{selected_export_project}_Export_{start_date}_{end_date}.zip",
                            mime="application/zip"
                        )


# Helper functions for report generation
def calculate_project_summary(kml_data, plantation_data):
    """Calculate summary statistics for a project"""
    summary = {
        'total_area_submitted': 0,
        'total_area_approved': 0,
        'total_area_planted': 0,
        'total_trees': 0,
        'kml_records': 0,
        'plantation_records': 0
    }
    
    if not kml_data.empty:
        try:
            summary['total_area_submitted'] = pd.to_numeric(kml_data.get('Total_Area', pd.Series([0])), errors='coerce').fillna(0).sum()
            summary['total_area_approved'] = pd.to_numeric(kml_data.get('Area_Approved', pd.Series([0])), errors='coerce').fillna(0).sum()
            summary['kml_records'] = len(kml_data)
        except:
            pass
    
    if not plantation_data.empty:
        try:
            summary['total_area_planted'] = pd.to_numeric(plantation_data.get('Area_Planted', pd.Series([0])), errors='coerce').fillna(0).sum()
            summary['total_trees'] = pd.to_numeric(plantation_data.get('Trees_Planted', pd.Series([0])), errors='coerce').fillna(0).sum()
            summary['plantation_records'] = len(plantation_data)
        except:
            pass
    
    return summary

def create_daily_summary(kml_data, plantation_data, start_date, end_date):
    """Create daily summary report"""
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    daily_summary = []
    
    for date in date_range:
        date_str = date.date()
        
        # KML data for the day
        kml_day = kml_data[kml_data['Date'] == date_str] if not kml_data.empty else pd.DataFrame()
        plantation_day = plantation_data[plantation_data['Date'] == date_str] if not plantation_data.empty else pd.DataFrame()
        
        kml_area = pd.to_numeric(kml_day.get('Total_Area', pd.Series([0])), errors='coerce').fillna(0).sum()
        plantation_area = pd.to_numeric(plantation_day.get('Area_Planted', pd.Series([0])), errors='coerce').fillna(0).sum()
        trees_planted = pd.to_numeric(plantation_day.get('Trees_Planted', pd.Series([0])), errors='coerce').fillna(0).sum()
        
        daily_summary.append({
            'Date': date_str,
            'KML_Area_Submitted': kml_area,
            'Plantation_Area': plantation_area,
            'Trees_Planted': trees_planted,
            'KML_Records': len(kml_day),
            'Plantation_Records': len(plantation_day)
        })
    
    return pd.DataFrame(daily_summary)

def create_weekly_summary(kml_data, plantation_data, start_date, end_date):
    """Create weekly summary report"""
    if kml_data.empty and plantation_data.empty:
        return pd.DataFrame()
    
    # Create weekly periods
    weekly_data = []
    current_date = start_date
    week_num = 1
    cumulative_trees = 0
    
    while current_date <= end_date:
        week_end = min(current_date + timedelta(days=6), end_date)
        
        # Filter data for this week
        week_kml = kml_data[(kml_data['Date'] >= current_date) & (kml_data['Date'] <= week_end)] if not kml_data.empty else pd.DataFrame()
        week_plantation = plantation_data[(plantation_data['Date'] >= current_date) & (plantation_data['Date'] <= week_end)] if not plantation_data.empty else pd.DataFrame()
        
        kml_area = pd.to_numeric(week_kml.get('Total_Area', pd.Series([0])), errors='coerce').fillna(0).sum()
        plantation_area = pd.to_numeric(week_plantation.get('Area_Planted', pd.Series([0])), errors='coerce').fillna(0).sum()
        trees_planted = pd.to_numeric(week_plantation.get('Trees_Planted', pd.Series([0])), errors='coerce').fillna(0).sum()
        
        cumulative_trees += trees_planted
        
        weekly_data.append({
            'Week': f"Week {week_num}\n({current_date.strftime('%m/%d')} - {week_end.strftime('%m/%d')})",
            'KML_Area_Submitted': kml_area,
            'Plantation_Area': plantation_area,
            'Trees_Planted': trees_planted,
            'Cumulative_Trees': cumulative_trees,
            'KML_Records': len(week_kml),
            'Plantation_Records': len(week_plantation)
        })
        
        current_date = week_end + timedelta(days=1)
        week_num += 1
    
    return pd.DataFrame(weekly_data)

def create_monthly_summary(kml_data, plantation_data, start_date, end_date):
    """Create monthly summary report"""
    if kml_data.empty and plantation_data.empty:
        return pd.DataFrame()
    
    # Group by month
    monthly_data = []
    
    # Get unique months in the date range
    months = set()
    if not kml_data.empty:
        months.update([date.replace(day=1) for date in kml_data['Date']])
    if not plantation_data.empty:
        months.update([date.replace(day=1) for date in plantation_data['Date']])
    
    for month_start in sorted(months):
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        # Filter data for this month
        month_kml = kml_data[(kml_data['Date'] >= month_start) & (kml_data['Date'] <= month_end)] if not kml_data.empty else pd.DataFrame()
        month_plantation = plantation_data[(plantation_data['Date'] >= month_start) & (plantation_data['Date'] <= month_end)] if not plantation_data.empty else pd.DataFrame()
        
        kml_area = pd.to_numeric(month_kml.get('Total_Area', pd.Series([0])), errors='coerce').fillna(0).sum()
        plantation_area = pd.to_numeric(month_plantation.get('Area_Planted', pd.Series([0])), errors='coerce').fillna(0).sum()
        trees_planted = pd.to_numeric(month_plantation.get('Trees_Planted', pd.Series([0])), errors='coerce').fillna(0).sum()
        
        monthly_data.append({
            'Month': month_start.strftime('%B %Y'),
            'KML_Area_Submitted': kml_area,
            'Plantation_Area': plantation_area,
            'Trees_Planted': trees_planted,
            'KML_Records': len(month_kml),
            'Plantation_Records': len(month_plantation)
        })
    
    return pd.DataFrame(monthly_data)

def generate_executive_summary(project_summaries, start_date, end_date):
    """Generate executive summary text"""
    total_projects = len(project_summaries)
    total_area = sum([s['total_area_submitted'] for s in project_summaries.values()])
    total_trees = sum([s['total_trees'] for s in project_summaries.values()])
    
    best_project = max(project_summaries.items(), key=lambda x: x[1]['total_area_submitted']) if project_summaries else None
    
    summary = f"""
    ### 📊 Executive Summary Report
    
    **Reporting Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}
    
    #### Key Highlights:
    - **Projects Monitored:** {total_projects}
    - **Total Area Managed:** {total_area:,.1f} hectares
    - **Total Trees Planted:** {total_trees:,.0f}
    
    #### Performance Analysis:
    """
    
    if best_project:
        summary += f"- **Top Performing Project:** {best_project[0]} with {best_project[1]['total_area_submitted']:,.1f} Ha submitted\n"
    
    if total_area > 0:
        avg_area_per_project = total_area / total_projects
        summary += f"- **Average Area per Project:** {avg_area_per_project:,.1f} Ha\n"
    
    if total_trees > 0 and total_area > 0:
        tree_density = total_trees / total_area
        summary += f"- **Average Tree Density:** {tree_density:.0f} trees per hectare\n"
    
    return summary

def analyze_weekly_trends(weekly_summary):
    """Analyze weekly trends and generate insights"""
    if weekly_summary.empty or len(weekly_summary) < 2:
        return "**Insufficient data for trend analysis.**"
    
    # Calculate trends
    area_trend = "increasing" if weekly_summary['KML_Area_Submitted'].iloc[-1] > weekly_summary['KML_Area_Submitted'].iloc[0] else "decreasing"
    trees_trend = "increasing" if weekly_summary['Trees_Planted'].iloc[-1] > weekly_summary['Trees_Planted'].iloc[0] else "decreasing"
    
    best_week = weekly_summary.loc[weekly_summary['Trees_Planted'].idxmax(), 'Week']
    best_week_trees = weekly_summary['Trees_Planted'].max()
    
    trends = f"""
    ### 📈 Weekly Trends Analysis
    
    - **Area Submission Trend:** {area_trend.title()} over the reporting period
    - **Tree Planting Trend:** {trees_trend.title()} over the reporting period
    - **Best Performing Week:** {best_week} with {best_week_trees:,.0f} trees planted
    - **Total Weeks Analyzed:** {len(weekly_summary)}
    """
    
    return trends

def generate_monthly_insights(monthly_summary):
    """Generate monthly insights"""
    if monthly_summary.empty:
        return "**No monthly data available for insights.**"
    
    best_month = monthly_summary.loc[monthly_summary['Trees_Planted'].idxmax(), 'Month']
    best_month_trees = monthly_summary['Trees_Planted'].max()
    
    total_months = len(monthly_summary)
    avg_trees_per_month = monthly_summary['Trees_Planted'].mean()
    
    insights = f"""
    ### 💡 Monthly Performance Insights
    
    - **Best Performing Month:** {best_month} with {best_month_trees:,.0f} trees planted
    - **Average Trees per Month:** {avg_trees_per_month:,.0f}
    - **Total Months Analyzed:** {total_months}
    - **Consistency Score:** {"High" if monthly_summary['Trees_Planted'].std() < avg_trees_per_month * 0.3 else "Moderate" if monthly_summary['Trees_Planted'].std() < avg_trees_per_month * 0.6 else "Variable"}
    """
    
    return insights

def create_summary_report_data(project_summaries, start_date, end_date):
    """Create summary report data for download"""
    summary_data = []
    for project, summary in project_summaries.items():
        summary_data.append({
            'Project': project,
            'Report_Period': f"{start_date} to {end_date}",
            'Area_Submitted_Ha': summary['total_area_submitted'],
            'Area_Approved_Ha': summary['total_area_approved'],
            'Area_Planted_Ha': summary['total_area_planted'],
            'Trees_Planted': summary['total_trees'],
            'KML_Records': summary['kml_records'],
            'Plantation_Records': summary['plantation_records'],
            'Approval_Rate_Percent': (summary['total_area_approved']/summary['total_area_submitted']*100) if summary['total_area_submitted'] > 0 else 0
        })
    
    return pd.DataFrame(summary_data)

def create_excel_report(data, sheet_name):
    """Create Excel report buffer"""
    from io import BytesIO
    
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        data.to_excel(writer, sheet_name=sheet_name, index=False)
    
    buffer.seek(0)
    return buffer.getvalue()

def create_multi_sheet_excel(data_dict):
    """Create multi-sheet Excel report"""
    from io import BytesIO
    
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for sheet_name, data in data_dict.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)
    
    buffer.seek(0)
    return buffer.getvalue()

def create_csv_zip(data_dict, start_date, end_date):
    """Create ZIP file with multiple CSV files"""
    import zipfile
    from io import BytesIO, StringIO
    
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for name, data in data_dict.items():
            csv_buffer = StringIO()
            data.to_csv(csv_buffer, index=False)
            zip_file.writestr(f"{name}_{start_date}_{end_date}.csv", csv_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def create_pdf_report(data, summary_text, report_title, start_date, end_date):
    """Create PDF report using reportlab"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
        
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkgreen,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Build the story (content)
        story = []
        
        # Title
        story.append(Paragraph(f"🌱 {report_title}", title_style))
        story.append(Paragraph(f"Plantation Management Report", styles['Normal']))
        story.append(Paragraph(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Summary section
        if summary_text:
            story.append(Paragraph("Executive Summary", heading_style))
            # Clean up the summary text for PDF
            clean_summary = summary_text.replace('###', '').replace('**', '').replace('####', '')
            story.append(Paragraph(clean_summary, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Data table
        if not data.empty:
            story.append(Paragraph("Detailed Data", heading_style))
            
            # Convert DataFrame to table data
            table_data = []
            
            # Add headers
            headers = list(data.columns)
            table_data.append(headers)
            
            # Add data rows (limit to first 50 rows for PDF)
            for idx, row in data.head(50).iterrows():
                row_data = []
                for col in headers:
                    value = row[col]
                    # Format the value
                    if pd.isna(value):
                        row_data.append("")
                    elif isinstance(value, (int, float)):
                        if col.lower().endswith('_percent') or 'rate' in col.lower():
                            row_data.append(f"{value:.1f}%")
                        elif 'area' in col.lower() or 'ha' in col.lower():
                            row_data.append(f"{value:,.1f}")
                        else:
                            row_data.append(f"{value:,.0f}")
                    else:
                        row_data.append(str(value)[:30])  # Truncate long strings
                table_data.append(row_data)
            
            # Create table
            table = Table(table_data)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(table)
            
            if len(data) > 50:
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Note: Showing first 50 records out of {len(data)} total records.", styles['Italic']))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Generated by Navchetna Plantation Management System", styles['Italic']))
        story.append(Paragraph(f"Report generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Italic']))
        
        # Build PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        # Fallback to simple text-based PDF if reportlab is not available
        return create_simple_pdf_report(data, summary_text, report_title, start_date, end_date)

def create_simple_pdf_report(data, summary_text, report_title, start_date, end_date):
    """Create a simple PDF report using fpdf as fallback"""
    try:
        from fpdf import FPDF
        from io import BytesIO
        
        buffer = BytesIO()
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        
        # Title
        pdf.cell(0, 10, f'{report_title}', ln=True, align='C')
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Period: {start_date.strftime("%B %d, %Y")} to {end_date.strftime("%B %d, %Y")}', ln=True, align='C')
        pdf.ln(10)
        
        # Summary
        if summary_text:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Summary', ln=True)
            pdf.set_font('Arial', '', 10)
            
            # Clean and add summary text
            clean_summary = summary_text.replace('###', '').replace('**', '').replace('####', '')
            lines = clean_summary.split('\n')
            for line in lines[:10]:  # Limit lines
                if line.strip():
                    pdf.cell(0, 6, line.strip()[:80], ln=True)
            pdf.ln(5)
        
        # Data summary
        if not data.empty:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Data Summary', ln=True)
            pdf.set_font('Arial', '', 10)
            
            pdf.cell(0, 6, f'Total Records: {len(data)}', ln=True)
            pdf.cell(0, 6, f'Columns: {", ".join(data.columns[:5])}{"..." if len(data.columns) > 5 else ""}', ln=True)
            
            # Add key statistics
            numeric_cols = data.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                pdf.ln(5)
                pdf.cell(0, 6, 'Key Statistics:', ln=True)
                for col in numeric_cols[:3]:  # Show first 3 numeric columns
                    total = data[col].sum()
                    pdf.cell(0, 6, f'{col}: {total:,.1f}', ln=True)
        
        # Footer
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 6, 'Generated by Navchetna Plantation Management System', ln=True)
        pdf.cell(0, 6, f'Report generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', ln=True)
        
        # Save to buffer
        pdf_output = pdf.output(dest='S').encode('latin-1')
        buffer.write(pdf_output)
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        # Final fallback - create a text file as PDF
        return create_text_as_pdf_fallback(data, summary_text, report_title, start_date, end_date)

def create_text_as_pdf_fallback(data, summary_text, report_title, start_date, end_date):
    """Create a text file as final fallback when no PDF libraries are available"""
    from io import BytesIO
    
    buffer = BytesIO()
    
    # Create text content
    content = f"""
{report_title}
Plantation Management Report
Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}

{'='*60}

SUMMARY:
{summary_text if summary_text else 'No summary available'}

{'='*60}

DATA OVERVIEW:
Total Records: {len(data) if not data.empty else 0}
Columns: {', '.join(data.columns) if not data.empty else 'No data'}

"""
    
    if not data.empty:
        content += "\nDATA PREVIEW (First 10 rows):\n"
        content += data.head(10).to_string()
    
    content += f"""

{'='*60}
Generated by Navchetna Plantation Management System
Report generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
"""
    
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)
    return buffer.getvalue()

def show_user_management():
    """Display user management page"""
    st.markdown("""
    <div class="main-header">
        <h1>👥 User Management</h1>
        <p>Manage system users and permissions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tab layout for user management
    tab1, tab2, tab3 = st.tabs(["👥 View Users", "➕ Add User", "✏️ Edit Users"])
    
    with tab1:
        st.subheader("👥 Current Users")
        
        # Get current users
        users_df = db_manager.read_dataframe(None, 'users')
        
        if not users_df.empty:
            # Display user information
            display_cols = ['username', 'role']
            if 'assigned_projects' in users_df.columns:
                display_cols.append('assigned_projects')
            if 'created_date' in users_df.columns:
                display_cols.append('created_date')
            
            # Filter columns that exist
            available_cols = [col for col in display_cols if col in users_df.columns]
            
            st.dataframe(users_df[available_cols], use_container_width=True)
            
            # User statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                admin_count = len(users_df[users_df['role'] == 'admin'])
                st.metric("👑 Admins", admin_count)
            
            with col2:
                pm_count = len(users_df[users_df['role'] == 'project_manager'])
                st.metric("👨‍💼 Project Managers", pm_count)
            
            with col3:
                viewer_count = len(users_df[users_df['role'] == 'viewer'])
                st.metric("👁️ Viewers", viewer_count)
        else:
            st.info("No users found in the system.")
    
    with tab2:
        st.subheader("➕ Add New User")
        
        # Get projects for assignment
        projects_df = db_manager.read_dataframe(None, 'projects')
        project_options = ['All'] + (projects_df['Project_Name'].tolist() if not projects_df.empty else [])
        
        with st.form("add_user"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username*")
                new_password = st.text_input("Password*", type="password")
                new_role = st.selectbox("Role*", ["viewer", "project_manager", "admin"])
            
            with col2:
                new_email = st.text_input("Email")
                new_full_name = st.text_input("Full Name")
                assigned_projects = st.multiselect("Assigned Projects", project_options, default=['All'])
            
            # Convert multiselect to string
            projects_str = 'All' if 'All' in assigned_projects else ','.join(assigned_projects)
            
            submitted = st.form_submit_button("➕ Add User", use_container_width=True)
            
            if submitted:
                if new_username and new_password:
                    # Get current users
                    users_df = db_manager.read_dataframe(None, 'users')
                    
                    # Check if user already exists
                    if not users_df.empty and new_username in users_df['username'].values:
                        st.error("Username already exists!")
                    else:
                        # Add new user
                        new_user = pd.DataFrame([{
                            'username': new_username,
                            'password': db_manager.hash_password(new_password),
                            'role': new_role,
                            'assigned_projects': projects_str,
                            'email': new_email,
                            'full_name': new_full_name,
                            'status': 'Active',
                            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }])
                        
                        if users_df.empty:
                            updated_users = new_user
                        else:
                            updated_users = pd.concat([users_df, new_user], ignore_index=True)
                        
                        if db_manager.write_dataframe(None, 'users', updated_users):
                            st.success("User added successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to add user.")
                else:
                    st.error("Please fill in username and password.")
    
    with tab3:
        st.subheader("✏️ Edit Users")
        
        # Get current users
        users_df = db_manager.read_dataframe(None, 'users')
        
        if not users_df.empty:
            # Select user to edit
            usernames = users_df['username'].tolist()
            selected_username = st.selectbox("Select User to Edit", usernames)
            
            if selected_username:
                user_row = users_df[users_df['username'] == selected_username].iloc[0]
                
                # Get projects for assignment
                projects_df = db_manager.read_dataframe(None, 'projects')
                project_options = ['All'] + (projects_df['Project_Name'].tolist() if not projects_df.empty else [])
                
                with st.form("edit_user"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.text_input("Username", value=selected_username, disabled=True)
                        new_role = st.selectbox("Role", ["viewer", "project_manager", "admin"], 
                                              index=["viewer", "project_manager", "admin"].index(user_row.get('role', 'viewer')))
                        new_status = st.selectbox("Status", ["Active", "Inactive"], 
                                                index=0 if user_row.get('status', 'Active') == 'Active' else 1)
                    
                    with col2:
                        new_email = st.text_input("Email", value=user_row.get('email', ''))
                        new_full_name = st.text_input("Full Name", value=user_row.get('full_name', ''))
                        
                        # Handle assigned projects
                        current_projects = user_row.get('assigned_projects', 'All')
                        if current_projects == 'All':
                            default_projects = ['All']
                        else:
                            default_projects = [p.strip() for p in current_projects.split(',') if p.strip()]
                        
                        assigned_projects = st.multiselect("Assigned Projects", project_options, default=default_projects)
                    
                    # Password reset option
                    reset_password = st.checkbox("Reset Password")
                    new_password = ""
                    if reset_password:
                        new_password = st.text_input("New Password", type="password")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        update_submitted = st.form_submit_button("💾 Update User", use_container_width=True)
                    
                    with col2:
                        delete_submitted = st.form_submit_button("🗑️ Delete User", use_container_width=True, type="secondary")
                    
                    if update_submitted:
                        # Convert multiselect to string
                        projects_str = 'All' if 'All' in assigned_projects else ','.join(assigned_projects)
                        
                        # Update user data
                        users_df.loc[users_df['username'] == selected_username, 'role'] = new_role
                        users_df.loc[users_df['username'] == selected_username, 'assigned_projects'] = projects_str
                        users_df.loc[users_df['username'] == selected_username, 'email'] = new_email
                        users_df.loc[users_df['username'] == selected_username, 'full_name'] = new_full_name
                        users_df.loc[users_df['username'] == selected_username, 'status'] = new_status
                        
                        # Update password if requested
                        if reset_password and new_password:
                            users_df.loc[users_df['username'] == selected_username, 'password'] = db_manager.hash_password(new_password)
                        
                        if db_manager.write_dataframe(None, 'users', users_df):
                            st.success("User updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update user.")
                    
                    if delete_submitted:
                        if selected_username == 'admin':
                            st.error("Cannot delete the admin user!")
                        else:
                            # Delete user
                            updated_users = users_df[users_df['username'] != selected_username]
                            
                            if db_manager.write_dataframe(None, 'users', updated_users):
                                st.success("User deleted successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to delete user.")
        else:
            st.info("No users found to edit.")

def show_project_management():
    """Display project management page"""
    st.markdown("""
    <div class="main-header">
        <h1>🆕 Project Management</h1>
        <p>Create and manage projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get current projects
    projects_df = db_manager.read_dataframe(None, 'projects')
    
    if not projects_df.empty:
        st.subheader("Current Projects")
        st.dataframe(projects_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Add New Project")
    
    with st.form("add_project"):
        project_id = st.text_input("Project ID")
        project_name = st.text_input("Project Name")
        description = st.text_area("Description")
        start_date = st.date_input("Start Date", value=datetime.now().date())
        target_area = st.number_input("Target Area (Ha)", value=0.0)
        
        submitted = st.form_submit_button("Create Project")
        
        if submitted:
            if project_id and project_name:
                # Check if project already exists
                if not projects_df.empty and project_id in projects_df['Project_ID'].values:
                    st.error("Project ID already exists!")
                else:
                    # Add new project
                    new_project = pd.DataFrame([{
                        'Project_ID': project_id,
                        'Project_Name': project_name,
                        'Description': description,
                        'Start_Date': start_date.strftime('%Y-%m-%d'),
                        'Target_Area': target_area,
                        'Status': 'Active',
                        'Created_Date': datetime.now().strftime('%Y-%m-%d')
                    }])
                    
                    if projects_df.empty:
                        updated_projects = new_project
                    else:
                        updated_projects = pd.concat([projects_df, new_project], ignore_index=True)
                    
                    if db_manager.write_dataframe(None, 'projects', updated_projects):
                        # Initialize tables for the new project
                        table_manager.initialize_project_tables(project_name)
                        st.success("Project created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create project.")
            else:
                st.error("Please fill in required fields.")

def show_schema_management():
    """Display schema management page"""
    st.markdown("""
    <div class="main-header">
        <h1>🔧 Schema Management</h1>
        <p>Create tables, manage schemas and add new fields</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tab layout for different schema operations
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View Tables", "➕ Create Table", "🔧 Manage Fields", "📊 Table Data"])
    
    with tab1:
        st.subheader("📋 All Tables")
        tables_df = table_manager.get_all_tables()
        
        if not tables_df.empty:
            # Display tables with their schemas
            for _, table_row in tables_df.iterrows():
                table_name = table_row['table_name']
                description = table_row.get('description', 'No description')
                
                with st.expander(f"📊 {table_name}"):
                    st.write(f"**Description:** {description}")
                    
                    # Show schema
                    schema = table_manager.get_table_schema(table_name)
                    if schema:
                        schema_df = pd.DataFrame([
                            {
                                'Field Name': field.get('name', ''),
                                'Type': field.get('type', 'text'),
                                'Required': field.get('required', False),
                                'Default': field.get('default', '')
                            }
                            for field in schema
                        ])
                        st.dataframe(schema_df, use_container_width=True)
                    else:
                        st.info("No fields defined for this table")
        else:
            st.info("No tables found. Create your first table in the 'Create Table' tab.")
    
    with tab2:
        st.subheader("➕ Create New Table")
        
        # Dynamic field definition - OUTSIDE the form
        if 'new_table_fields' not in st.session_state:
            st.session_state.new_table_fields = [{'name': '', 'type': 'text', 'required': False, 'default': ''}]
        
        # Add/Remove field buttons - OUTSIDE the form
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("➕ Add Field"):
                st.session_state.new_table_fields.append({'name': '', 'type': 'text', 'required': False, 'default': ''})
                st.rerun()
        with col2:
            if len(st.session_state.new_table_fields) > 1 and st.button("❌ Remove Last Field"):
                st.session_state.new_table_fields.pop()
                st.rerun()
        
        with st.form("create_table"):
            table_name = st.text_input("Table Name", help="Enter a descriptive name for your table")
            description = st.text_area("Description", help="Describe what this table will store")
            table_type = st.selectbox("Table Type", ["data", "lookup", "configuration"], help="Select the type of table")
            
            st.write("**Define Fields:**")
            
            fields = []
            for i, field in enumerate(st.session_state.new_table_fields):
                col1, col2, col3, col4 = st.columns([3, 2, 1, 2])
                
                with col1:
                    field_name = st.text_input(f"Field Name {i+1}", value=field['name'], key=f"field_name_{i}")
                with col2:
                    field_type = st.selectbox("Type", ["text", "number", "date", "textarea", "select"], 
                                            index=["text", "number", "date", "textarea", "select"].index(field['type']), 
                                            key=f"field_type_{i}")
                with col3:
                    required = st.checkbox("Required", value=field['required'], key=f"field_required_{i}")
                with col4:
                    default = st.text_input("Default", value=field['default'], key=f"field_default_{i}")
                
                fields.append({
                    'name': field_name,
                    'type': field_type,
                    'required': required,
                    'default': default
                })
            
            submitted = st.form_submit_button("🔧 Create Table")
            
            if submitted:
                if table_name and description:
                    # Filter out empty fields
                    valid_fields = [f for f in fields if f['name'].strip()]
                    
                    if valid_fields:
                        if table_manager.create_table(table_name, description, valid_fields):
                            st.success(f"Table '{table_name}' created successfully!")
                            st.session_state.new_table_fields = [{'name': '', 'type': 'text', 'required': False, 'default': ''}]
                            st.rerun()
                        else:
                            st.error("Failed to create table. Table might already exist.")
                    else:
                        st.error("Please define at least one field.")
                else:
                    st.error("Please provide table name and description.")
    
    with tab3:
        st.subheader("🔧 Manage Table Fields")
        
        tables = table_manager.get_project_tables(None)  # Get all tables
        
        if tables:
            selected_table = st.selectbox("Select Table to Modify", tables)
            
            if selected_table:
                # Display current schema
                schema = table_manager.get_table_schema(selected_table)
                
                if schema:
                    st.write("**Current Fields:**")
                    schema_df = pd.DataFrame([
                        {
                            'Field Name': field.get('name', ''),
                            'Type': field.get('type', 'text'),
                            'Required': field.get('required', False),
                            'Default': field.get('default', '')
                        }
                        for field in schema
                    ])
                    st.dataframe(schema_df, use_container_width=True)
                
                st.markdown("---")
                
                # Create sub-tabs for field operations
                field_tab1, field_tab2, field_tab3 = st.tabs(["➕ Add Field", "✏️ Edit Field", "🗑️ Delete Field"])
                
                with field_tab1:
                    st.subheader("➕ Add New Field")
                    
                    with st.form("add_field"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_field_name = st.text_input("Field Name")
                            new_field_type = st.selectbox("Field Type", ["text", "number", "date", "textarea", "select"])
                        
                        with col2:
                            new_field_required = st.checkbox("Required Field")
                            new_field_default = st.text_input("Default Value")
                        
                        submitted = st.form_submit_button("➕ Add Field")
                        
                        if submitted:
                            if new_field_name:
                                field_config = {
                                    'name': new_field_name,
                                    'type': new_field_type,
                                    'required': new_field_required,
                                    'default': new_field_default
                                }
                                
                                if table_manager.add_field_to_table(selected_table, field_config):
                                    st.success("Field added successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to add field. Field might already exist.")
                            else:
                                st.error("Please enter a field name.")
                
                with field_tab2:
                    st.subheader("✏️ Edit Existing Field")
                    
                    if schema:
                        field_names = [field.get('name', '') for field in schema if field.get('name')]
                        
                        if field_names:
                            selected_field = st.selectbox("Select Field to Edit", field_names)
                            
                            if selected_field:
                                # Get current field configuration
                                current_field = next((f for f in schema if f.get('name') == selected_field), {})
                                
                                with st.form("edit_field"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        edit_field_name = st.text_input("Field Name", value=current_field.get('name', ''))
                                        
                                        # Normalize field type and handle case mismatches
                                        current_type = current_field.get('type', 'text').lower()
                                        type_options = ["text", "number", "date", "textarea", "select"]
                                        
                                        # Map common variations to standard types
                                        type_mapping = {
                                            'text': 'text',
                                            'string': 'text',
                                            'number': 'number',
                                            'numeric': 'number',
                                            'integer': 'number',
                                            'float': 'number',
                                            'date': 'date',
                                            'datetime': 'date',
                                            'textarea': 'textarea',
                                            'longtext': 'textarea',
                                            'select': 'select',
                                            'choice': 'select',
                                            'dropdown': 'select'
                                        }
                                        
                                        # Get the normalized type or default to 'text'
                                        normalized_type = type_mapping.get(current_type, 'text')
                                        
                                        # Find the index safely
                                        try:
                                            type_index = type_options.index(normalized_type)
                                        except ValueError:
                                            type_index = 0  # Default to 'text' if not found
                                        
                                        edit_field_type = st.selectbox("Field Type", 
                                                                     type_options,
                                                                     index=type_index)
                                    
                                    with col2:
                                        edit_field_required = st.checkbox("Required Field", value=current_field.get('required', False))
                                        edit_field_default = st.text_input("Default Value", value=current_field.get('default', ''))
                                    
                                    submitted = st.form_submit_button("✏️ Update Field")
                                    
                                    if submitted:
                                        if edit_field_name:
                                            new_field_config = {
                                                'name': edit_field_name,
                                                'type': edit_field_type,
                                                'required': edit_field_required,
                                                'default': edit_field_default
                                            }
                                            
                                            if table_manager.edit_field_in_table(selected_table, selected_field, new_field_config):
                                                st.success("Field updated successfully!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to update field.")
                                        else:
                                            st.error("Please enter a field name.")
                        else:
                            st.info("No fields available to edit.")
                    else:
                        st.info("No fields available to edit.")
                
                with field_tab3:
                    st.subheader("🗑️ Delete Field")
                    
                    if schema:
                        field_names = [field.get('name', '') for field in schema if field.get('name')]
                        
                        if field_names:
                            st.warning("⚠️ **Warning**: Deleting a field will permanently remove it from the table and all existing data in that field will be lost!")
                            
                            selected_field_to_delete = st.selectbox("Select Field to Delete", field_names, key="delete_field_select")
                            
                            if selected_field_to_delete:
                                # Show field details
                                field_to_delete = next((f for f in schema if f.get('name') == selected_field_to_delete), {})
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**Field Name:** {field_to_delete.get('name', '')}")
                                    st.write(f"**Type:** {field_to_delete.get('type', 'text')}")
                                with col2:
                                    st.write(f"**Required:** {field_to_delete.get('required', False)}")
                                    st.write(f"**Default:** {field_to_delete.get('default', '')}")
                                
                                # Confirmation checkbox
                                confirm_delete = st.checkbox("I understand that this action cannot be undone")
                                
                                if st.button("🗑️ Delete Field", type="primary", disabled=not confirm_delete):
                                    if table_manager.delete_field_from_table(selected_table, selected_field_to_delete):
                                        st.success("Field deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete field.")
                        else:
                            st.info("No fields available to delete.")
                    else:
                        st.info("No fields available to delete.")
        else:
            st.info("No tables available. Create a table first.")
    
    with tab4:
        st.subheader("📊 View Table Data")
        
        # Get accessible projects
        accessible_projects = auth_manager.get_accessible_projects()
        
        if accessible_projects:
            selected_project = st.selectbox("Select Project", accessible_projects, key="data_project")
            tables = table_manager.get_project_tables(selected_project)
            
            if tables:
                selected_table = st.selectbox("Select Table", tables, key="data_table")
                
                if selected_table:
                    data = table_manager.get_table_data(selected_project, selected_table)
                    
                    if not data.empty:
                        st.write(f"**Data in {selected_table}:**")
                        st.dataframe(data, use_container_width=True)
                        
                        # Export option
                        csv = data.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"{selected_project}_{selected_table}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info(f"No data found in {selected_table}")
            else:
                st.info("No tables found for this project.")
        else:
            st.warning("No projects accessible to your account.")

def show_my_projects():
    """Display user's accessible projects"""
    st.markdown("""
    <div class="main-header">
        <h1>🏢 My Projects</h1>
        <p>Projects you have access to</p>
    </div>
    """, unsafe_allow_html=True)
    
    accessible_projects = auth_manager.get_accessible_projects()
    
    if accessible_projects:
        for project_name in accessible_projects:
            with st.expander(f"📁 {project_name}"):
                # Get project data
                kml_data = table_manager.get_table_data(project_name, "KML Tracking")
                plantation_data = table_manager.get_table_data(project_name, "Plantation Records")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**KML Tracking:**")
                    if not kml_data.empty:
                        st.write(f"Records: {len(kml_data)}")
                        try:
                            total_area_series = pd.to_numeric(kml_data.get('Total_Area', pd.Series([0])), errors='coerce').fillna(0)
                            total_area = total_area_series.sum()
                            st.write(f"Total Area: {total_area:,.1f} Ha")
                        except Exception as e:
                            st.write("Total Area: Error calculating")
                    else:
                        st.write("No data available")
                
                with col2:
                    st.write("**Plantation Records:**")
                    if not plantation_data.empty:
                        st.write(f"Records: {len(plantation_data)}")
                        try:
                            trees_series = pd.to_numeric(plantation_data.get('Trees_Planted', pd.Series([0])), errors='coerce').fillna(0)
                            trees = trees_series.sum()
                            st.write(f"Trees Planted: {trees:,.0f}")
                        except Exception as e:
                            st.write("Trees Planted: Error calculating")
                    else:
                        st.write("No data available")
    else:
        st.warning("No projects accessible to your account.")

def show_all_projects():
    """Display all projects (viewer access)"""
    st.markdown("""
    <div class="main-header">
        <h1>🔍 All Projects</h1>
        <p>Overview of all plantation projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all projects
    projects_df = db_manager.read_dataframe(None, 'projects')
    
    if not projects_df.empty:
        for _, project in projects_df.iterrows():
            project_name = project['Project_Name']
            
            with st.expander(f"📁 {project_name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Project ID:** {project['Project_ID']}")
                    st.write(f"**Description:** {project['Description']}")
                    st.write(f"**Start Date:** {project['Start_Date']}")
                    st.write(f"**Target Area:** {project['Target_Area']} Ha")
                    st.write(f"**Status:** {project['Status']}")
                
                with col2:
                    # Get summary data
                    kml_data = table_manager.get_table_data(project_name, "KML Tracking")
                    plantation_data = table_manager.get_table_data(project_name, "Plantation Records")
                    
                    if not kml_data.empty:
                        try:
                            total_area_series = pd.to_numeric(kml_data.get('Total_Area', pd.Series([0])), errors='coerce').fillna(0)
                            total_area = total_area_series.sum()
                            st.write(f"**Area Submitted:** {total_area:,.1f} Ha")
                        except Exception as e:
                            st.write("**Area Submitted:** Error calculating")
                    
                    if not plantation_data.empty:
                        try:
                            trees_series = pd.to_numeric(plantation_data.get('Trees_Planted', pd.Series([0])), errors='coerce').fillna(0)
                            trees = trees_series.sum()
                            st.write(f"**Trees Planted:** {trees:,.0f}")
                        except Exception as e:
                            st.write("**Trees Planted:** Error calculating")
    else:
        st.info("No projects found.")

def initialize_default_data():
    """Initialize default projects and tables"""
    # Create default projects
    projects_df = db_manager.read_dataframe(None, 'projects')
    if projects_df.empty:
        default_projects = pd.DataFrame([
            {
                'Project_ID': 'PRJ001',
                'Project_Name': 'MakeMyTrip',
                'Description': 'MakeMyTrip plantation initiative',
                'Start_Date': '2024-01-01',
                'Target_Area': 1000.0,
                'Status': 'Active',
                'Created_Date': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'Project_ID': 'PRJ002',
                'Project_Name': 'Absolute',
                'Description': 'Absolute plantation project',
                'Start_Date': '2024-01-01',
                'Target_Area': 800.0,
                'Status': 'Active',
                'Created_Date': datetime.now().strftime('%Y-%m-%d')
            }
        ])
        db_manager.write_dataframe(None, 'projects', default_projects)
    
    # Initialize tables for projects
    for project_name in ['MakeMyTrip', 'Absolute']:
        table_manager.initialize_project_tables(project_name)

if __name__ == "__main__":
    main()