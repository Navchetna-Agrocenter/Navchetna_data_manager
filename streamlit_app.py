"""
Streamlit Application Entry Point for Plantation Data Management System
This is a simplified entry point that handles module imports more gracefully.
"""

import streamlit as st
import os
import sys
import importlib.util
import traceback

# Configure Streamlit page
st.set_page_config(
    page_title="Navchetna Plantation Data Manager",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Debug information
st.sidebar.markdown("### Debug Information")
st.sidebar.write(f"Current directory: {os.getcwd()}")
st.sidebar.write(f"Python version: {sys.version}")
st.sidebar.write(f"Directory contents: {os.listdir('.')}")

# Function to safely import a module from a file path
def import_module_from_path(module_name, file_path):
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            st.error(f"Could not find module {module_name} at {file_path}")
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        st.error(f"Error importing {module_name}: {str(e)}")
        st.code(traceback.format_exc())
        return None

# Check for utils directory
if not os.path.exists('utils'):
    st.error("The utils directory is missing! Contents of the current directory:")
    st.write(os.listdir('.'))
    
    # Try to create the basic utility modules from scratch
    st.warning("Attempting to create essential modules from scratch...")
    
    # Create directory structure
    os.makedirs('utils', exist_ok=True)
    os.makedirs('components', exist_ok=True)
    
    # Create minimal utility modules
    with open('utils/__init__.py', 'w') as f:
        f.write('# Utils package\n')
        
    with open('utils/sharepoint_manager.py', 'w') as f:
        f.write('''
"""Minimal SharePoint Manager"""
import streamlit as st
import pandas as pd
import os

class SharePointManager:
    def __init__(self):
        self.is_online = False
        st.session_state['deployment_mode'] = 'github'
        
    def authenticate(self):
        return True
        
    def read_excel_file(self, project_name, file_name):
        # Return empty DataFrame with default structure
        return pd.DataFrame()
        
    def write_excel_file(self, project_name, file_name, data, sheet_name='Sheet1'):
        # Store in session state
        key = f"data_{project_name}_{file_name.replace('.xlsx', '')}" if project_name else f"data_master_{file_name.replace('.xlsx', '')}"
        st.session_state[key] = data
        return True
        
    def get_project_list(self):
        return ['MakeMyTrip', 'Absolute']
        
    def hash_password(self, password):
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
''')
        
    with open('utils/auth_manager.py', 'w') as f:
        f.write('''
"""Minimal Auth Manager"""
import streamlit as st
import pandas as pd

class AuthManager:
    def __init__(self, sharepoint_manager):
        self.sp_manager = sharepoint_manager
        
    def initialize_default_users(self):
        pass
        
    def authenticate_user(self, username, password):
        # Always allow login for emergency access
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.session_state['role'] = 'Administrator'
        return True
''')
        
    with open('utils/data_manager.py', 'w') as f:
        f.write('''
"""Minimal Data Manager"""
import streamlit as st
import pandas as pd

class DataManager:
    def __init__(self, sharepoint_manager):
        self.sp_manager = sharepoint_manager
        
    def initialize_default_data(self):
        pass
        
    def get_all_project_names(self):
        return ['MakeMyTrip', 'Absolute']
        
    def migrate_plantation_data(self, project_name):
        pass
''')
        
    with open('components/__init__.py', 'w') as f:
        f.write('# Components package\n')
        
    with open('components/charts.py', 'w') as f:
        f.write('''
"""Minimal Chart Manager"""
import streamlit as st
import pandas as pd

class ChartManager:
    def __init__(self):
        pass
        
    def create_kml_status_chart(self, data):
        st.write("Chart placeholder - KML Status")
        return None
        
    def create_plantation_progress_chart(self, data):
        st.write("Chart placeholder - Plantation Progress")
        return None
''')

# Try to import the modules
try:
    # First, try to import config
    if os.path.exists('config.py'):
        config = import_module_from_path('config', 'config.py')
    else:
        st.error("config.py is missing!")
        config = None
    
    # Import utility modules
    sharepoint_manager = import_module_from_path('sharepoint_manager', 'utils/sharepoint_manager.py')
    auth_manager = import_module_from_path('auth_manager', 'utils/auth_manager.py')
    data_manager = import_module_from_path('data_manager', 'utils/data_manager.py')
    charts = import_module_from_path('charts', 'components/charts.py')
    
    if None in [sharepoint_manager, auth_manager, data_manager, charts]:
        st.error("Failed to import one or more required modules!")
    else:
        # Initialize managers
        sp_manager = sharepoint_manager.SharePointManager()
        sp_manager.authenticate()
        
        auth_manager_instance = auth_manager.AuthManager(sp_manager)
        data_manager_instance = data_manager.DataManager(sp_manager)
        chart_manager = charts.ChartManager()
        
        # Initialize data
        auth_manager_instance.initialize_default_users()
        data_manager_instance.initialize_default_data()
        
        # Display storage mode
        if 'deployment_mode' in st.session_state:
            mode = st.session_state['deployment_mode']
            if mode == 'gsheets':
                st.sidebar.success("📊 Connected to Google Sheets for persistent storage")
            elif mode == 'github':
                st.sidebar.info("⚠️ Running in GitHub mode. Data will not persist between sessions.")
            else:
                st.sidebar.info("💾 Running in local storage mode")
        
        # Display login form if not logged in
        if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
            st.title("🌱 Plantation Data Management System")
            st.subheader("Login")
            
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    if auth_manager_instance.authenticate_user(username, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                        
            # Show demo credentials
            with st.expander("Demo Credentials"):
                st.markdown("""
                - **Admin:** username: `admin`, password: `admin123`
                - **Manager 1:** username: `manager1`, password: `manager123`
                - **Manager 2:** username: `manager2`, password: `manager123`
                - **Viewer:** username: `viewer`, password: `viewer123`
                """)
        else:
            # Display main app
            st.title("🌱 Plantation Data Management System")
            st.subheader(f"Welcome, {st.session_state.get('username', 'User')}")
            
            # Simple dashboard
            st.markdown("### Dashboard")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Projects", len(data_manager_instance.get_all_project_names()))
                
            with col2:
                st.metric("KML Files", "N/A")
                
            with col3:
                st.metric("Area Planted", "N/A")
                
            # Projects section
            st.markdown("### Projects")
            for project in data_manager_instance.get_all_project_names():
                st.write(f"- {project}")
                
            # Logout button
            if st.button("Logout"):
                for key in ['logged_in', 'username', 'role']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
                
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.code(traceback.format_exc()) 