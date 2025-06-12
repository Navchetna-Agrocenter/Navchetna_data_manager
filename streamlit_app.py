"""
Streamlit Application Entry Point for Plantation Data Management System
This is a simplified entry point that handles module imports more gracefully.
"""

import streamlit as st
import os
import sys
import importlib.util
import traceback
import pandas as pd
from datetime import datetime

# Disable file watcher to prevent "inotify watch limit reached" error
os.environ["STREAMLIT_SERVER_WATCH_DIRS"] = "false"
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

# Configure Streamlit page
st.set_page_config(
    page_title="Navchetna Plantation Data Manager",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize custom tables data
def initialize_custom_tables():
    """Initialize custom tables data structure if it doesn't exist"""
    if 'data_master_custom_tables' not in st.session_state:
        # Create default tables structure
        default_tables = [
            {
                'table_name': 'KML Tracking',
                'description': 'Track KML files and approval status',
                'fields': str([
                    {'name': 'Date', 'type': 'Date', 'required': True, 'default': ''},
                    {'name': 'User', 'type': 'Text', 'required': True, 'default': ''},
                    {'name': 'KML_Count_Sent', 'type': 'Number', 'required': True, 'default': '0'},
                    {'name': 'Total_Area', 'type': 'Number', 'required': True, 'default': '0'},
                    {'name': 'Area_Approved', 'type': 'Number', 'required': True, 'default': '0'},
                    {'name': 'Approval_Date', 'type': 'Date', 'required': False, 'default': ''},
                    {'name': 'Status', 'type': 'Text', 'required': True, 'default': 'Pending'},
                    {'name': 'Remarks', 'type': 'Text', 'required': False, 'default': ''}
                ]),
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'table_type': 'system'
            },
            {
                'table_name': 'Plantation Records',
                'description': 'Track plantation activities and progress',
                'fields': str([
                    {'name': 'Date', 'type': 'Date', 'required': True, 'default': ''},
                    {'name': 'User', 'type': 'Text', 'required': True, 'default': ''},
                    {'name': 'Plot_Code', 'type': 'Text', 'required': True, 'default': ''},
                    {'name': 'Area_Planted', 'type': 'Number', 'required': True, 'default': '0'},
                    {'name': 'Farmer_Covered', 'type': 'Number', 'required': True, 'default': '0'},
                    {'name': 'Trees_Planted', 'type': 'Number', 'required': True, 'default': '0'},
                    {'name': 'Pits_Dug', 'type': 'Number', 'required': True, 'default': '0'},
                    {'name': 'Status', 'type': 'Text', 'required': True, 'default': 'In Progress'}
                ]),
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'table_type': 'system'
            }
        ]
        
        # Create DataFrame and store in session state
        custom_tables_df = pd.DataFrame(default_tables)
        st.session_state['data_master_custom_tables'] = custom_tables_df
        
        # If we have a SharePoint/Google Sheets manager, save the data
        if 'sp_manager' in st.session_state:
            try:
                st.session_state['sp_manager'].write_excel_file(None, 'custom_tables.xlsx', custom_tables_df)
            except Exception as e:
                st.error(f"Error saving custom tables: {str(e)}")

# Initialize schema extensions data
def initialize_schema_extensions():
    """Initialize schema extensions data structure if it doesn't exist"""
    if 'data_master_schema_extensions' not in st.session_state:
        # Create default schema extensions
        default_extensions = [
            {
                'table_type': 'KML Tracking',
                'field_name': 'Status',
                'field_type': 'Dropdown',
                'default_value': 'Pending',
                'is_required': True,
                'dropdown_options': 'Pending,Approved,Rejected,Under Review',
                'description': 'Current status of the KML file'
            },
            {
                'table_type': 'Plantation Records',
                'field_name': 'Status',
                'field_type': 'Dropdown',
                'default_value': 'In Progress',
                'is_required': True,
                'dropdown_options': 'In Progress,Completed',
                'description': 'Current status of plantation activity'
            }
        ]
        
        # Create DataFrame and store in session state
        schema_extensions_df = pd.DataFrame(default_extensions)
        st.session_state['data_master_schema_extensions'] = schema_extensions_df
        
        # If we have a SharePoint/Google Sheets manager, save the data
        if 'sp_manager' in st.session_state:
            try:
                st.session_state['sp_manager'].write_excel_file(None, 'schema_extensions.xlsx', schema_extensions_df)
            except Exception as e:
                st.error(f"Error saving schema extensions: {str(e)}")

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
        
        # Store SharePoint manager in session state for access by initialization functions
        st.session_state['sp_manager'] = sp_manager
        
        auth_manager_instance = auth_manager.AuthManager(sp_manager)
        data_manager_instance = data_manager.DataManager(sp_manager)
        chart_manager = charts.ChartManager()
        
        # Initialize data
        auth_manager_instance.initialize_default_users()
        data_manager_instance.initialize_default_data()
        
        # Initialize custom tables and schema extensions
        initialize_custom_tables()
        initialize_schema_extensions()
        
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