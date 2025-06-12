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

# Create a function for simple user authentication
def authenticate_user(username, password):
    """Simple authentication for demo purposes"""
    # Default admin credentials
    if username == "admin" and password == "admin123":
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.session_state['role'] = 'Administrator'
        return True
    
    # Default manager credentials
    elif username == "manager1" and password == "manager123":
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.session_state['role'] = 'Project Manager'
        st.session_state['project'] = 'MakeMyTrip'
        return True
    
    # Default manager credentials
    elif username == "manager2" and password == "manager123":
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.session_state['role'] = 'Project Manager'
        st.session_state['project'] = 'Absolute'
        return True
        
    # Default viewer credentials
    elif username == "viewer" and password == "viewer123":
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.session_state['role'] = 'Viewer'
        return True
        
    # Invalid credentials
    return False

# Debug information
st.sidebar.markdown("### Debug Information")
st.sidebar.write(f"Current directory: {os.getcwd()}")
st.sidebar.write(f"Python version: {sys.version}")
st.sidebar.write(f"Directory contents: {os.listdir('.')}")
st.sidebar.write(f"Logged in: {st.session_state.get('logged_in', False)}")
st.sidebar.write(f"Username: {st.session_state.get('username', 'None')}")

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

# Import utility modules if they exist
utils_exist = os.path.exists('utils')
if not utils_exist:
    st.warning("Utils directory not found. Creating simplified environment.")
    # Create directory structure if needed
    os.makedirs('utils', exist_ok=True)
    os.makedirs('components', exist_ok=True)

# Main application logic
try:
    # Display storage mode based on environment
    # Will be set by the SharePoint or Google Sheets manager
    if 'deployment_mode' in st.session_state:
        mode = st.session_state['deployment_mode']
        if mode == 'gsheets':
            st.sidebar.success("📊 Connected to Google Sheets for persistent storage")
        elif mode == 'github':
            st.sidebar.info("⚠️ Running in GitHub mode. Data will not persist between sessions.")
        else:
            st.sidebar.info("💾 Running in local storage mode")
    
    # Login screen
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.title("🌱 Plantation Data Management System")
        st.subheader("Login")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                login_button = st.form_submit_button("Login")
                
                if login_button:
                    if authenticate_user(username, password):
                        st.success(f"Login successful! Welcome {username}")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with col2:
            st.info("Demo Credentials")
            st.markdown("""
            - **Admin:** username: `admin`, password: `admin123`
            - **Manager 1:** username: `manager1`, password: `manager123`
            - **Manager 2:** username: `manager2`, password: `manager123`
            - **Viewer:** username: `viewer`, password: `viewer123`
            """)
    
    # Main application
    else:
        # Import utility modules after login is successful
        try:
            # Import config first
            if os.path.exists('config.py'):
                config = import_module_from_path('config', 'config.py')
            else:
                st.warning("config.py is missing, using default configuration.")
                config = None
            
            # Import core modules
            sharepoint_manager = import_module_from_path('sharepoint_manager', 'utils/sharepoint_manager.py')
            auth_manager = import_module_from_path('auth_manager', 'utils/auth_manager.py')
            data_manager = import_module_from_path('data_manager', 'utils/data_manager.py')
            charts = import_module_from_path('charts', 'components/charts.py')
            
            # Check if imports were successful
            if None in [sharepoint_manager, auth_manager, data_manager, charts]:
                st.warning("Some modules couldn't be loaded. Using simplified interface.")
                
                # Create a minimal SharePoint manager
                class SimpleSharePointManager:
                    def __init__(self):
                        self.is_online = False
                        st.session_state['deployment_mode'] = 'github'
                    
                    def authenticate(self):
                        return True
                    
                    def read_excel_file(self, project_name, file_name):
                        key = f"data_{project_name}_{file_name.replace('.xlsx', '')}" if project_name else f"data_master_{file_name.replace('.xlsx', '')}"
                        if key in st.session_state:
                            return st.session_state[key]
                        return pd.DataFrame()
                    
                    def write_excel_file(self, project_name, file_name, data, sheet_name='Sheet1'):
                        key = f"data_{project_name}_{file_name.replace('.xlsx', '')}" if project_name else f"data_master_{file_name.replace('.xlsx', '')}"
                        st.session_state[key] = data
                        return True
                    
                    def get_project_list(self):
                        return ['MakeMyTrip', 'Absolute']
                
                # Use simplified managers
                sp_manager = SimpleSharePointManager()
                st.session_state['sp_manager'] = sp_manager
            else:
                # Use imported managers
                sp_manager = sharepoint_manager.SharePointManager()
                sp_manager.authenticate()
                st.session_state['sp_manager'] = sp_manager
                
                auth_manager_instance = auth_manager.AuthManager(sp_manager)
                data_manager_instance = data_manager.DataManager(sp_manager)
                chart_manager = charts.ChartManager()
                
                # Initialize data
                auth_manager_instance.initialize_default_users()
                data_manager_instance.initialize_default_data()
            
            # Initialize tables data regardless of which managers are used
            initialize_custom_tables()
            initialize_schema_extensions()
            
            # Display main application
            st.title("🌱 Plantation Data Management System")
            st.subheader(f"Welcome, {st.session_state.get('username', 'User')}")
            
            # Navigation sidebar
            st.sidebar.title("Navigation")
            page = st.sidebar.radio(
                "Go to",
                ["Dashboard", "Projects", "Add Data", "Schema Management", "Reports", "User Management"]
            )
            
            # Logout button
            if st.sidebar.button("Logout"):
                for key in ['logged_in', 'username', 'role']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            # Page content
            if page == "Dashboard":
                st.header("Dashboard")
                st.write("Main dashboard content will go here.")
                
                # Simple KPIs
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Projects", "2")
                with col2:
                    st.metric("KML Files", "35")
                with col3:
                    st.metric("Area Planted", "750 ha")
                
            elif page == "Projects":
                st.header("Projects")
                st.write("Projects overview will go here.")
                
                # Show project list
                projects = sp_manager.get_project_list()
                for i, project in enumerate(projects):
                    st.subheader(f"{i+1}. {project}")
                    st.write(f"Description for {project} project")
                
            elif page == "Add Data":
                st.header("Add Data")
                st.write("Data entry forms will go here.")
                
            elif page == "Schema Management":
                st.header("Schema Management")
                
                # Get custom tables
                custom_tables_df = st.session_state.get('data_master_custom_tables', pd.DataFrame())
                
                # Schema management tabs
                schema_tab = st.tabs(["View Schema", "Add Field", "Edit Field", "Delete Field", "Manage Tables"])
                
                with schema_tab[0]:
                    st.subheader("Current Schema")
                    if not custom_tables_df.empty:
                        st.dataframe(custom_tables_df)
                    else:
                        st.warning("No tables defined yet.")
                
                with schema_tab[4]:
                    st.subheader("Manage Tables")
                    if not custom_tables_df.empty:
                        st.dataframe(custom_tables_df)
                        
                        # Add new table form
                        st.subheader("Add New Table")
                        with st.form("add_table_form"):
                            table_name = st.text_input("Table Name")
                            description = st.text_area("Description")
                            st.form_submit_button("Add Table")
                    else:
                        st.warning("No tables defined yet.")
                
            elif page == "Reports":
                st.header("Reports")
                st.write("Reporting tools will go here.")
                
            elif page == "User Management":
                st.header("User Management")
                st.write("User management tools will go here.")
                
        except Exception as e:
            st.error(f"Error loading application components: {str(e)}")
            st.code(traceback.format_exc())
                
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.code(traceback.format_exc()) 