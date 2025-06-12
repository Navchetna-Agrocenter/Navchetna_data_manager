"""
Authentication Manager for user login and role-based access control
"""

import streamlit as st
import pandas as pd
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import config
from utils.sharepoint_manager import SharePointManager

class AuthManager:
    def __init__(self, sharepoint_manager: SharePointManager):
        self.sp_manager = sharepoint_manager
        self.current_user = None
        self.current_role = None
        
    def initialize_default_users(self):
        """Initialize default users if users file doesn't exist"""
        users_df = self.sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
        
        if users_df.empty:
            # Create default users
            default_users = [
                {
                    'User_ID': 'admin001',
                    'Username': 'admin',
                    'Full_Name': 'System Administrator',
                    'Password_Hash': self._hash_password('admin123'),
                    'Role': 'admin',
                    'Assigned_Projects': 'All',
                    'Email': 'admin@navchetna.com',
                    'Status': 'Active',
                    'Created_Date': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'User_ID': 'pm001',
                    'Username': 'manager1',
                    'Full_Name': 'Project Manager 1',
                    'Password_Hash': self._hash_password('manager123'),
                    'Role': 'project_manager',
                    'Assigned_Projects': 'MakeMyTrip',
                    'Email': 'manager1@navchetna.com',
                    'Status': 'Active',
                    'Created_Date': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'User_ID': 'pm002',
                    'Username': 'manager2',
                    'Full_Name': 'Project Manager 2',
                    'Password_Hash': self._hash_password('manager123'),
                    'Role': 'project_manager',
                    'Assigned_Projects': 'Absolute',
                    'Email': 'manager2@navchetna.com',
                    'Status': 'Active',
                    'Created_Date': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'User_ID': 'viewer001',
                    'Username': 'viewer',
                    'Full_Name': 'Data Viewer',
                    'Password_Hash': self._hash_password('viewer123'),
                    'Role': 'viewer',
                    'Assigned_Projects': 'MakeMyTrip,Absolute',
                    'Email': 'viewer@navchetna.com',
                    'Status': 'Active',
                    'Created_Date': datetime.now().strftime('%Y-%m-%d')
                }
            ]
            
            users_df = pd.DataFrame(default_users)
            self.sp_manager.write_excel_file(None, config.FILE_NAMING['users'], users_df)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user credentials"""
        try:
            users_df = self.sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
            
            if users_df.empty:
                self.initialize_default_users()
                users_df = self.sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
            
            # Find user
            user_row = users_df[users_df['Username'] == username]
            
            if user_row.empty:
                return False
            
            user_data = user_row.iloc[0]
            
            # Check password
            if user_data['Password_Hash'] == self._hash_password(password):
                # Check if user is active
                if user_data['Status'] == 'Active':
                    # Store full user data as dictionary
                    self.current_user = {
                        'username': user_data['Username'],
                        'full_name': user_data['Full_Name'],
                        'role': user_data['Role'],
                        'assigned_projects': user_data['Assigned_Projects'],
                        'user_id': user_data['User_ID'],
                        'email': user_data['Email']
                    }
                    self.current_role = user_data['Role']
                    
                    # Store in session state
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = user_data['Username']
                    st.session_state['full_name'] = user_data['Full_Name']
                    st.session_state['role'] = user_data['Role']
                    st.session_state['assigned_projects'] = user_data['Assigned_Projects']
                    st.session_state['user_id'] = user_data['User_ID']
                    st.session_state['current_user'] = self.current_user
                    
                    return True
                else:
                    st.error("Account is inactive. Please contact administrator.")
                    return False
            else:
                return False
                
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return False
    
    def logout(self):
        """Logout current user"""
        self.current_user = None
        self.current_role = None
        
        # Clear session state
        for key in ['authenticated', 'username', 'full_name', 'role', 'assigned_projects', 'user_id']:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        is_auth = st.session_state.get('authenticated', False)
        
        # Initialize current_user from session state if authenticated
        if is_auth and not self.current_user:
            self.current_user = st.session_state.get('current_user')
            # If current_user is still not set, create it from session data
            if not self.current_user:
                self.current_user = {
                    'username': st.session_state.get('username', ''),
                    'full_name': st.session_state.get('full_name', ''),
                    'role': st.session_state.get('role', ''),
                    'assigned_projects': st.session_state.get('assigned_projects', ''),
                    'user_id': st.session_state.get('user_id', ''),
                    'email': st.session_state.get('email', '')
                }
                st.session_state['current_user'] = self.current_user
        
        return is_auth
    
    def has_role(self, required_role: str) -> bool:
        """Check if current user has required role"""
        if not self.is_authenticated():
            return False
        
        user_role = st.session_state.get('role', '')
        
        # Admin has access to everything
        if user_role == 'admin':
            return True
        
        return user_role == required_role
    
    def has_project_access(self, project_name: str) -> bool:
        """Check if current user has access to specific project"""
        if not self.is_authenticated():
            return False
        
        user_role = st.session_state.get('role', '')
        assigned_projects = st.session_state.get('assigned_projects', '')
        
        # Admin has access to all projects
        if user_role == 'admin' or assigned_projects == 'All':
            return True
        
        # Check if project is in assigned projects
        project_list = [p.strip() for p in assigned_projects.split(',')]
        return project_name in project_list
    
    def get_accessible_projects(self) -> List[str]:
        """Get list of projects accessible to current user"""
        if not self.is_authenticated():
            return []
        
        user_role = st.session_state.get('role', '')
        assigned_projects = st.session_state.get('assigned_projects', '')
        
        # Admin has access to all projects
        if user_role == 'admin' or assigned_projects == 'All':
            return self.sp_manager.get_project_list()
        
        # Return assigned projects
        project_list = [p.strip() for p in assigned_projects.split(',')]
        all_projects = self.sp_manager.get_project_list()
        
        # Filter to only include existing projects
        return [p for p in project_list if p in all_projects]
    
    def can_edit_data(self, project_name: str = None) -> bool:
        """Check if current user can edit data"""
        if not self.is_authenticated():
            return False
        
        user_role = st.session_state.get('role', '')
        
        # Viewers cannot edit
        if user_role == 'viewer':
            return False
        
        # Admin can edit everything
        if user_role == 'admin':
            return True
        
        # Project managers can edit their assigned projects
        if user_role == 'project_manager':
            if project_name:
                return self.has_project_access(project_name)
            return True
        
        return False
    
    def get_current_user_info(self) -> Dict:
        """Get current user information"""
        if not self.is_authenticated():
            return {}
        
        return {
            'username': st.session_state.get('username', ''),
            'full_name': st.session_state.get('full_name', ''),
            'role': st.session_state.get('role', ''),
            'assigned_projects': st.session_state.get('assigned_projects', ''),
            'user_id': st.session_state.get('user_id', '')
        }
    
    def create_user(self, user_data: Dict) -> bool:
        """Create a new user (admin only)"""
        if not self.has_role('admin'):
            st.error("Only administrators can create users")
            return False
        
        try:
            users_df = self.sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
            
            # Check if username already exists
            if not users_df.empty and user_data['Username'] in users_df['Username'].values:
                st.error("Username already exists")
                return False
            
            # Hash password
            user_data['Password_Hash'] = self._hash_password(user_data['Password'])
            del user_data['Password']  # Remove plain password
            
            # Add creation date
            user_data['Created_Date'] = datetime.now().strftime('%Y-%m-%d')
            user_data['Status'] = 'Active'
            
            # Add to DataFrame
            new_user = pd.DataFrame([user_data])
            users_df = pd.concat([users_df, new_user], ignore_index=True)
            
            # Save to file
            return self.sp_manager.write_excel_file(None, config.FILE_NAMING['users'], users_df)
            
        except Exception as e:
            st.error(f"Error creating user: {str(e)}")
            return False
    
    def update_user(self, user_id: str, user_data: Dict) -> bool:
        """Update user information (admin only)"""
        if not self.has_role('admin'):
            st.error("Only administrators can update users")
            return False
        
        try:
            users_df = self.sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
            
            # Find user
            user_index = users_df[users_df['User_ID'] == user_id].index
            
            if user_index.empty:
                st.error("User not found")
                return False
            
            # Update user data
            for key, value in user_data.items():
                if key in users_df.columns:
                    users_df.loc[user_index[0], key] = value
            
            # Save to file
            return self.sp_manager.write_excel_file(None, config.FILE_NAMING['users'], users_df)
            
        except Exception as e:
            st.error(f"Error updating user: {str(e)}")
            return False
    
    def get_all_users(self) -> pd.DataFrame:
        """Get all users (admin only)"""
        if not self.has_role('admin'):
            return pd.DataFrame()
        
        users_df = self.sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
        
        # Remove password hash for security
        if not users_df.empty and 'Password_Hash' in users_df.columns:
            users_df = users_df.drop('Password_Hash', axis=1)
        
        return users_df
    
    def show_login_form(self):
        """Display login form"""
        st.title("🌱 Plantation Data Management System")
        st.subheader("Please login to continue")
        
        # Create login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if username and password:
                    if self.authenticate_user(username, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
        
        # Display demo credentials
        st.info("""
        **Demo Credentials:**
        
        **Administrator:**
        - Username: admin
        - Password: admin123
        
        **Project Manager (MakeMyTrip):**
        - Username: manager1
        - Password: manager123
        
        **Project Manager (Absolute):**
        - Username: manager2
        - Password: manager123
        
        **Viewer:**
        - Username: viewer
        - Password: viewer123
        """)
    
    def require_authentication(self):
        """Decorator-like function to require authentication"""
        if not self.is_authenticated():
            self.show_login_form()
            st.stop()
    
    def require_role(self, required_role: str):
        """Require specific role"""
        if not self.has_role(required_role):
            st.error(f"Access denied. Required role: {config.USER_ROLES.get(required_role, required_role)}")
            st.stop() 