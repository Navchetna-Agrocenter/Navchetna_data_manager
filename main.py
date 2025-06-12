"""
Main Streamlit Application for Plantation Data Management System
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import time
import math

# More robust path handling for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)  # Add the current directory to Python path

# Try different import approaches
try:
    import config
    from utils.sharepoint_manager import SharePointManager
    from utils.auth_manager import AuthManager
    from utils.data_manager import DataManager
    from components.charts import ChartManager
    from sample_data import initialize_sample_data
    print("Imports successful using standard approach")
except ImportError as e:
    print(f"Import error with standard approach: {e}")
    # Try alternative import approach
    try:
        import config
        # Use absolute imports as fallback
        from navchetna_data_manager.utils.sharepoint_manager import SharePointManager
        from navchetna_data_manager.utils.auth_manager import AuthManager
        from navchetna_data_manager.utils.data_manager import DataManager
        from navchetna_data_manager.components.charts import ChartManager
        from navchetna_data_manager.sample_data import initialize_sample_data
        print("Imports successful using absolute imports")
    except ImportError as e2:
        print(f"Import error with absolute imports: {e2}")
        # Create a direct import by manipulating sys.path
        utils_path = os.path.join(current_dir, 'utils')
        components_path = os.path.join(current_dir, 'components')
        sys.path.insert(0, utils_path)
        sys.path.insert(0, components_path)
        
        import config
        from sharepoint_manager import SharePointManager
        from auth_manager import AuthManager
        from data_manager import DataManager
        from charts import ChartManager
        from sample_data import initialize_sample_data
        print("Imports successful using path manipulation")

# Configure Streamlit page
st.set_page_config(
    page_title="Navchetna Plantation Data Manager",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Display directories for debugging
st.sidebar.write("### Debug Info")
st.sidebar.write(f"Current directory: {os.getcwd()}")
st.sidebar.write(f"Python path: {sys.path}")
st.sidebar.write(f"Directory contents: {os.listdir('.')}")

# Initialize managers
@st.cache_resource
def initialize_managers():
    """Initialize all managers"""
    sp_manager = SharePointManager()
    sp_manager.authenticate()
    
    auth_manager = AuthManager(sp_manager)
    data_manager = DataManager(sp_manager)
    chart_manager = ChartManager()
    
    # Initialize default data
    auth_manager.initialize_default_users()
    data_manager.initialize_default_data()
    
    # Initialize sample data for GitHub deployment
    initialize_sample_data()
    
    # Migrate existing data to new format
    try:
        projects = data_manager.get_all_project_names()
        for project in projects:
            data_manager.migrate_plantation_data(project)
    except:
        pass  # Ignore migration errors for now
    
    return sp_manager, auth_manager, data_manager, chart_manager

# Get managers
sp_manager, auth_manager, data_manager, chart_manager = initialize_managers()

# Display storage mode information
if 'deployment_mode' in st.session_state:
    mode = st.session_state['deployment_mode']
    if mode == 'gsheets':
        st.sidebar.success("📊 Connected to Google Sheets for persistent storage")
    elif mode == 'github':
        st.sidebar.info("⚠️ Running in GitHub mode. Data will not persist between sessions.")
    else:
        st.sidebar.info("💾 Running in local storage mode")

# ================================
# ESSENTIAL TABLE MANAGEMENT FUNCTIONS 
# (Must be defined before any functions that use them)
# ================================

def get_all_tables() -> pd.DataFrame:
    """Get all tables by scanning project folders for Excel files"""
    tables_data = []
    
    projects_dir = "local_data/projects"
    if not os.path.exists(projects_dir):
        return pd.DataFrame(columns=['table_name', 'description', 'fields', 'table_type'])
    
    # Scan all project folders to find unique table types
    discovered_tables = set()
    
    for project_name in os.listdir(projects_dir):
        project_path = os.path.join(projects_dir, project_name)
        if os.path.isdir(project_path):
            # Find all Excel files in the project folder
            for file_name in os.listdir(project_path):
                if file_name.endswith('.xlsx'):
                    table_name = file_name.replace('.xlsx', '').replace('_', ' ').title()
                    discovered_tables.add((table_name, file_name))
    
    # Process discovered tables
    for table_name, file_name in discovered_tables:
        # Try to read one instance to get column information
        try:
            sample_project = next(iter(os.listdir(projects_dir)))
            file_path = os.path.join(projects_dir, sample_project, file_name)
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
                
                # Create field definitions from actual columns
                fields = []
                for col in df.columns:
                    # Try to infer field type from data
                    field_type = "Text"  # default
                    if not df[col].empty:
                        sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                        if sample_val is not None:
                            if isinstance(sample_val, (int, float)):
                                field_type = "Number"
                            elif isinstance(sample_val, bool):
                                field_type = "True/False"
                            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                                field_type = "Date"
                    
                    fields.append({
                        'name': col,
                        'type': field_type,
                        'required': False,
                        'default': ''
                    })
                
                tables_data.append({
                    'table_name': table_name,
                    'description': f'{table_name} data table',
                    'fields': str(fields),
                    'table_type': 'discovered'
                })
        
        except Exception:
            # If we can't read the file, still add it as a table
            tables_data.append({
                'table_name': table_name,
                'description': f'{table_name} data table',
                'fields': '[]',
                'table_type': 'discovered'
            })
    
    # Also include any tables from custom_tables.csv if it exists
    custom_tables_file = "local_data/custom_tables.csv"
    if os.path.exists(custom_tables_file):
        try:
            custom_df = pd.read_csv(custom_tables_file)
            for _, row in custom_df.iterrows():
                tables_data.append({
                    'table_name': row['table_name'],
                    'description': row.get('description', ''),
                    'fields': row.get('fields', '[]'),
                    'table_type': 'created'
                })
        except:
            pass
    
    return pd.DataFrame(tables_data)

def get_table_data(project_name: str, table_name: str) -> pd.DataFrame:
    """Get data from any table (unified approach)"""
    try:
        # Convert table name back to file name
        file_name = table_name.lower().replace(' ', '_') + '.xlsx'
        file_path = f"local_data/projects/{project_name}/{file_name}"
        
        if os.path.exists(file_path):
            return pd.read_excel(file_path)
        else:
            # Return empty DataFrame with proper error handling
            return pd.DataFrame()
    
    except Exception as e:
        st.error(f"Error loading {table_name} data: {str(e)}")
        return pd.DataFrame()

def get_schema_extensions() -> pd.DataFrame:
    """Get schema extensions from file"""
    try:
        schema_file = "local_data/schema_extensions.csv"
        if os.path.exists(schema_file):
            return pd.read_csv(schema_file)
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'table_type', 'field_name', 'field_type', 'default_value',
                'is_required', 'dropdown_options', 'description'
            ])
    except Exception:
        return pd.DataFrame(columns=[
            'table_type', 'field_name', 'field_type', 'default_value',
            'is_required', 'dropdown_options', 'description'
        ])

def get_custom_tables() -> pd.DataFrame:
    """Get custom tables from file"""
    try:
        custom_tables_file = "local_data/custom_tables.csv"
        if os.path.exists(custom_tables_file):
            return pd.read_csv(custom_tables_file)
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'table_name', 'description', 'fields', 'created_date', 'table_type'
            ])
    except Exception:
        return pd.DataFrame(columns=[
            'table_name', 'description', 'fields', 'created_date', 'table_type'
        ])

def add_field_to_schema(table_type: str, field_name: str, field_type: str, default_value: str, 
                       is_required: bool, dropdown_options: str, description: str) -> bool:
    """Add field to schema extensions"""
    try:
        # Ensure local_data directory exists
        os.makedirs("local_data", exist_ok=True)
        
        schema_file = "local_data/schema_extensions.csv"
        
        # Check if field already exists
        existing_schema = get_schema_extensions()
        if not existing_schema.empty:
            duplicate = existing_schema[
                (existing_schema['table_type'] == table_type) & 
                (existing_schema['field_name'] == field_name)
            ]
            if not duplicate.empty:
                return False
        
        # Create new field record
        new_field = pd.DataFrame([{
            'table_type': table_type,
            'field_name': field_name,
            'field_type': field_type,
            'default_value': default_value,
            'is_required': is_required,
            'dropdown_options': dropdown_options or '',
            'description': description
        }])
        
        # Append to existing schema
        if os.path.exists(schema_file):
            updated_schema = pd.concat([existing_schema, new_field], ignore_index=True)
        else:
            updated_schema = new_field
        
        # Save to file
        updated_schema.to_csv(schema_file, index=False)
        
        # Add field to all existing project data
        add_field_to_existing_data(table_type, field_name, default_value, field_type)
        
        return True
    except Exception as e:
        st.error(f"Error adding field: {str(e)}")
        return False

def add_field_to_existing_data(table_type: str, field_name: str, default_value: str, field_type: str):
    """Add field to existing data files for all projects"""
    try:
        projects_dir = "local_data/projects"
        if not os.path.exists(projects_dir):
            return
        
        # Convert table type to file name
        file_name = table_type.lower().replace(' ', '_') + '.xlsx'
        
        for project_name in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_name)
            if os.path.isdir(project_path):
                file_path = os.path.join(project_path, file_name)
                if os.path.exists(file_path):
                    # Load existing data
                    df = pd.read_excel(file_path)
                    
                    # Add new column if it doesn't exist
                    if field_name not in df.columns:
                        # Set appropriate default value based on field type
                        if field_type == "Number":
                            df[field_name] = float(default_value) if default_value else 0.0
                        elif field_type == "True/False":
                            df[field_name] = default_value.lower() == 'true' if default_value else False
                        else:
                            df[field_name] = default_value
                        
                        # Save updated data
                        df.to_excel(file_path, index=False)
    except Exception as e:
        st.error(f"Error updating existing data: {str(e)}")

def edit_field_in_schema(field_index: int, update_data: dict) -> bool:
    """Edit an existing field in schema extensions"""
    try:
        schema_extensions = get_schema_extensions()
        if schema_extensions.empty or field_index >= len(schema_extensions):
            return False
        
        # Get old field info for updating project data
        old_field_name = schema_extensions.iloc[field_index]['field_name']
        table_type = schema_extensions.iloc[field_index]['table_type']
        
        # Update the field
        for key, value in update_data.items():
            schema_extensions.iloc[field_index, schema_extensions.columns.get_loc(key)] = value
        
        # Save updated schema
        schema_file = "local_data/schema_extensions.csv"
        schema_extensions.to_csv(schema_file, index=False)
        
        # Update field in project data if name changed
        if 'field_name' in update_data and update_data['field_name'] != old_field_name:
            update_field_in_project_data(table_type, old_field_name, update_data)
        
        return True
    except Exception as e:
        st.error(f"Error editing field: {str(e)}")
        return False

def delete_field_from_schema(field_index: int) -> bool:
    """Delete a field from schema extensions"""
    try:
        schema_extensions = get_schema_extensions()
        if schema_extensions.empty or field_index >= len(schema_extensions):
            return False
        
        # Get field info for deletion from project data
        field_name = schema_extensions.iloc[field_index]['field_name']
        table_type = schema_extensions.iloc[field_index]['table_type']
        
        # Remove the field from schema
        schema_extensions = schema_extensions.drop(field_index).reset_index(drop=True)
        
        # Save updated schema
        schema_file = "local_data/schema_extensions.csv"
        schema_extensions.to_csv(schema_file, index=False)
        
        # Remove field from project data
        remove_field_from_project_data(table_type, field_name)
        
        return True
    except Exception as e:
        st.error(f"Error deleting field: {str(e)}")
        return False

def create_new_table(table_name: str, description: str, fields: list) -> bool:
    """Create a new custom table"""
    try:
        # Ensure local_data directory exists
        os.makedirs("local_data", exist_ok=True)
        
        custom_tables_file = "local_data/custom_tables.csv"
        
        # Check if table already exists
        existing_tables = get_custom_tables()
        if not existing_tables.empty and table_name in existing_tables['table_name'].values:
            return False
        
        # Create new table record
        new_table = pd.DataFrame([{
            'table_name': table_name,
            'description': description,
            'fields': str(fields),
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'table_type': 'user-created'
        }])
        
        # Append to existing tables
        if os.path.exists(custom_tables_file):
            updated_tables = pd.concat([existing_tables, new_table], ignore_index=True)
        else:
            updated_tables = new_table
        
        # Save to file
        updated_tables.to_csv(custom_tables_file, index=False)
        
        # Create empty table files for all projects
        create_empty_table_file(table_name, fields)
        
        return True
    except Exception as e:
        st.error(f"Error creating table: {str(e)}")
        return False

def create_empty_table_file(table_name: str, fields: list):
    """Create empty table files for all projects"""
    try:
        projects_dir = "local_data/projects"
        if not os.path.exists(projects_dir):
            return
        
        # Convert table name to file name
        file_name = table_name.lower().replace(' ', '_').replace('-', '_') + '.xlsx'
        
        # Create column names from fields
        columns = [field['name'] for field in fields if field.get('name')]
        
        for project_name in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_name)
            if os.path.isdir(project_path):
                file_path = os.path.join(project_path, file_name)
                if not os.path.exists(file_path):
                    # Create empty DataFrame with defined columns
                    empty_df = pd.DataFrame(columns=columns)
                    empty_df.to_excel(file_path, index=False)
    except Exception as e:
        st.error(f"Error creating table files: {str(e)}")

def update_field_in_project_data(table_type: str, old_field_name: str, update_data: dict):
    """Update field in project data files"""
    try:
        projects_dir = "local_data/projects"
        if not os.path.exists(projects_dir):
            return
        
        file_name = table_type.lower().replace(' ', '_') + '.xlsx'
        new_field_name = update_data.get('field_name', old_field_name)
        
        for project_name in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_name)
            if os.path.isdir(project_path):
                file_path = os.path.join(project_path, file_name)
                if os.path.exists(file_path):
                    df = pd.read_excel(file_path)
                    
                    # Rename column if name changed
                    if old_field_name in df.columns and new_field_name != old_field_name:
                        df = df.rename(columns={old_field_name: new_field_name})
                        df.to_excel(file_path, index=False)
    except Exception as e:
        st.error(f"Error updating project data: {str(e)}")

def remove_field_from_project_data(table_type: str, field_name: str):
    """Remove field from project data files"""
    try:
        projects_dir = "local_data/projects"
        if not os.path.exists(projects_dir):
            return
        
        file_name = table_type.lower().replace(' ', '_') + '.xlsx'
        
        for project_name in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_name)
            if os.path.isdir(project_path):
                file_path = os.path.join(project_path, file_name)
                if os.path.exists(file_path):
                    df = pd.read_excel(file_path)
                    
                    # Remove column if it exists
                    if field_name in df.columns:
                        df = df.drop(columns=[field_name])
                        df.to_excel(file_path, index=False)
    except Exception as e:
        st.error(f"Error removing field from project data: {str(e)}")

def delete_custom_table(table_name: str) -> bool:
    """Delete a custom table"""
    try:
        custom_tables = get_custom_tables()
        if custom_tables.empty:
            return False
        
        # Remove table from custom tables
        updated_tables = custom_tables[custom_tables['table_name'] != table_name]
        
        # Save updated tables
        custom_tables_file = "local_data/custom_tables.csv"
        updated_tables.to_csv(custom_tables_file, index=False)
        
        # Delete table files from all projects
        projects_dir = "local_data/projects"
        if os.path.exists(projects_dir):
            file_name = table_name.lower().replace(' ', '_').replace('-', '_') + '.xlsx'
            for project_name in os.listdir(projects_dir):
                project_path = os.path.join(projects_dir, project_name)
                if os.path.isdir(project_path):
                    file_path = os.path.join(project_path, file_name)
                    if os.path.exists(file_path):
                        os.remove(file_path)
        
        return True
    except Exception as e:
        st.error(f"Error deleting table: {str(e)}")
        return False

# ================================
# END OF ESSENTIAL FUNCTIONS
# ================================

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

def main():
    """Main application function"""
    
    # Check authentication
    if not auth_manager.is_authenticated():
        show_login_page()
        return
    
    # Show main application
    show_main_app()

def show_login_page():
    """Display login page"""
    st.markdown("""
    <div class="main-header">
        <h1>🌱 Plantation Data Management System</h1>
        <h3>Navchetna Spatial Solutions</h3>
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
        
        # Sync status
        st.markdown("---")
        if sp_manager.is_online:
            st.success("🟢 Online - SharePoint Connected")
        else:
            st.info("🔵 Offline Mode - Local Storage")
    
    # Main content area
    if selected_page == "🏠 Dashboard":
        show_dashboard()
    elif selected_page == "➕ Add Data":
        # Only allow admins and project managers to access this page
        if current_role in ['admin', 'project_manager']:
            show_add_data()
        else:
            st.error("⛔ Access denied. You do not have permission to add data.")
            st.info("Please contact an administrator if you believe this is an error.")
    elif selected_page == "📊 Analytics":
        show_analytics()
    elif selected_page == "📋 Manage Records":
        # Only allow admins and project managers to access this page
        if current_role in ['admin', 'project_manager']:
            show_manage_records()
        else:
            st.error("⛔ Access denied. You do not have permission to manage records.")
            st.info("Please contact an administrator if you believe this is an error.")
    elif selected_page == "📊 Reports":
        show_reports()
    elif selected_page == "👥 User Management":
        # Only allow admins to access this page
        if current_role == 'admin':
            show_user_management()
        else:
            st.error("⛔ Access denied. Only administrators can manage users.")
    elif selected_page == "🆕 Project Management":
        # Only allow admins to access this page
        if current_role == 'admin':
            show_project_management()
        else:
            st.error("⛔ Access denied. Only administrators can manage projects.")
    elif selected_page == "🔧 Schema Management":
        # Only allow admins to access this page
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
    
    # Get all projects summary
    projects_summary = data_manager.get_all_projects_summary()
    
    if not projects_summary:
        st.warning("No project data available. Please contact administrator.")
        return
    
    # Overall KPIs
    st.subheader("📈 Overall Performance Metrics")
    
    total_target = sum(p.get('target_area', 0) for p in projects_summary)
    total_approved = sum(p.get('total_area_approved', 0) for p in projects_summary)
    total_planted = sum(p.get('total_area_planted', 0) for p in projects_summary)
    total_trees = sum(p.get('total_trees_planted', 0) for p in projects_summary)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Total Target Area", f"{total_target:,.0f} Ha")
    with col2:
        st.metric("✅ Total Approved Area", f"{total_approved:,.1f} Ha", 
                 f"{(total_approved/total_target*100) if total_target > 0 else 0:.1f}%")
    with col3:
        st.metric("🌱 Total Planted Area", f"{total_planted:,.1f} Ha",
                 f"{(total_planted/total_target*100) if total_target > 0 else 0:.1f}%")
    with col4:
        st.metric("🌳 Total Trees Planted", f"{total_trees:,.0f}")
    
    # Projects overview chart
    st.markdown("---")
    chart_manager.create_projects_overview_chart(projects_summary)
    
    # Today's activity summary
    st.markdown("---")
    st.subheader("📅 Today's Activity Summary")
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_summary = []
    
    for project in projects_summary:
        project_name = project['project_name']
        
        # Get today's KML data
        kml_df = sp_manager.read_excel_file(project_name, config.FILE_NAMING['kml_tracking'])
        today_kml = kml_df[kml_df['Date'] == today] if not kml_df.empty else pd.DataFrame()
        
        # Get today's plantation data
        plantation_df = sp_manager.read_excel_file(project_name, config.FILE_NAMING['plantation_records'])
        today_plantation = plantation_df[plantation_df['Date'] == today] if not plantation_df.empty else pd.DataFrame()
        
        today_summary.append({
            'Project': project_name,
            'KML Files Sent': today_kml['KML_Count_Sent'].sum() if not today_kml.empty else 0,
            'Area Sent (Ha)': today_kml['Total_Area'].sum() if not today_kml.empty else 0,
            'Area Planted (Ha)': today_plantation['Area_Planted'].sum() if not today_plantation.empty else 0,
            'Trees Planted': today_plantation['Trees_Planted'].sum() if not today_plantation.empty else 0
        })
    
    if today_summary:
        today_df = pd.DataFrame(today_summary)
        st.dataframe(today_df, use_container_width=True)
    else:
        st.info("No activity recorded for today yet.")

def show_projects_overview():
    """Display projects overview with detailed analytics"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Projects Overview</h1>
        <p>Comprehensive analysis of all plantation projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get projects accessible to current user
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible to your account.")
        return
    
    # Project filter
    selected_projects = st.multiselect(
        "Select Projects to Compare",
        accessible_projects,
        default=accessible_projects
    )
    
    if not selected_projects:
        st.warning("Please select at least one project.")
        return
    
    # Get summaries for selected projects
    selected_summaries = []
    for project in selected_projects:
        summary = data_manager.get_project_summary(project)
        if summary:
            selected_summaries.append(summary)
    
    # Comparison charts
    chart_manager.create_projects_overview_chart(selected_summaries)
    
    # Detailed comparison table
    st.markdown("---")
    st.subheader("📋 Detailed Project Comparison")
    
    comparison_data = []
    for summary in selected_summaries:
        comparison_data.append({
            'Project Name': summary['project_name'],
            'Status': summary['status'],
            'Target Area (Ha)': f"{summary.get('target_area', 0):,.0f}",
            'Area Approved (Ha)': f"{summary.get('total_area_approved', 0):,.1f}",
            'Area Planted (Ha)': f"{summary.get('total_area_planted', 0):,.1f}",
            'Completion %': f"{summary.get('plantation_completion', 0):.1f}%",
            'Trees Planted': f"{summary.get('total_trees_planted', 0):,.0f}",
            'Farmers Covered': f"{summary.get('total_farmers_covered', 0):,.0f}",
            'KML Files Sent': f"{summary.get('total_kml_sent', 0):,.0f}",
            'Approval Rate %': f"{summary.get('approval_rate', 0):.1f}%"
        })
    
    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)

def show_project_detail(project_name: str):
    """Display detailed project analysis"""
    if not auth_manager.has_project_access(project_name):
        st.error("Access denied to this project.")
        return
    
    st.markdown(f"""
    <div class="main-header">
        <h1>📈 {project_name} - Detailed Analysis</h1>
        <p>Comprehensive project analytics and data visualization</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get project summary
    summary = data_manager.get_project_summary(project_name)
    
    if not summary:
        st.error("Unable to load project data.")
        return
    
    # KPI Cards
    chart_manager.create_kpi_cards(summary)
    
    st.markdown("---")
    
    # Progress charts
    st.subheader("📊 Progress Analysis")
    chart_manager.create_progress_charts(summary)
    
    st.markdown("---")
    
    # Daily trends
    st.subheader("📈 Daily Trends")
    daily_data = data_manager.get_daily_progress_data(project_name, 30)
    chart_manager.create_daily_trend_chart(daily_data, project_name)
    
    st.markdown("---")
    
    # Weekly comparison
    st.subheader("📅 Weekly Performance")
    weekly_data = data_manager.get_weekly_comparison(project_name)
    chart_manager.create_weekly_comparison_chart(weekly_data)
    
    st.markdown("---")
    
    # Interactive data analysis
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["KML Tracking", "Plantation Records"]
    )
    
    if analysis_type == "KML Tracking":
        kml_df = sp_manager.read_excel_file(project_name, config.FILE_NAMING['kml_tracking'])
        chart_manager.create_interactive_filter_chart(kml_df, "KML Tracking", project_name)
        
        # Show recent records with edit/delete options
        if not kml_df.empty:
            st.subheader("📋 Recent KML Records")
            
            # Add edit/delete controls if user can edit
            if auth_manager.can_edit_data(project_name):
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🔧 Manage Records"):
                        st.session_state['show_kml_edit'] = not st.session_state.get('show_kml_edit', False)
            
            # Show edit interface if enabled
            if st.session_state.get('show_kml_edit', False) and auth_manager.can_edit_data(project_name):
                st.subheader("✏️ Edit/Delete KML Records")
                
                # Select record to edit
                kml_display = kml_df.copy()
                kml_display['Record_Index'] = range(len(kml_display))
                kml_display['Display'] = kml_display.apply(
                    lambda row: f"{row['Date']} - {row['KML_Count_Sent']} files - {row['Total_Area']}Ha", axis=1
                )
                
                selected_record = st.selectbox(
                    "Select Record to Edit/Delete",
                    options=kml_display['Record_Index'].tolist(),
                    format_func=lambda x: kml_display.loc[x, 'Display']
                )
                
                if selected_record is not None:
                    record_data = kml_df.iloc[selected_record]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("✏️ Edit Record", use_container_width=True):
                            st.session_state['edit_kml_record'] = selected_record
                    
                    with col2:
                        if st.button("🗑️ Delete Record", use_container_width=True, type="primary"):
                            if data_manager.delete_record(project_name, 'kml_tracking', selected_record):
                                st.success("✅ Record deleted successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete record.")
                
                # Edit form
                if 'edit_kml_record' in st.session_state:
                    edit_index = st.session_state['edit_kml_record']
                    edit_data = kml_df.iloc[edit_index]
                    
                    st.subheader("✏️ Edit KML Record")
                    
                    with st.form("edit_kml_form"):
                        edit_col1, edit_col2 = st.columns(2)
                        
                        with edit_col1:
                            edit_date = st.date_input("Date", pd.to_datetime(edit_data['Date']).date())
                            edit_kml_count = st.number_input("KML Files Sent", min_value=1, value=int(edit_data['KML_Count_Sent']))
                            edit_total_area = st.number_input("Total Area", min_value=0.1, value=float(edit_data['Total_Area']))
                        
                        with edit_col2:
                            edit_area_approved = st.number_input("Area Approved", min_value=0.0, value=float(edit_data['Area_Approved']))
                            # Handle approval date safely
                            try:
                                if edit_data['Approval_Date'] and pd.notna(edit_data['Approval_Date']) and edit_data['Approval_Date'] != '':
                                    approval_date_value = pd.to_datetime(edit_data['Approval_Date']).date()
                                else:
                                    approval_date_value = None
                            except:
                                approval_date_value = None
                            
                            edit_approval_date = st.date_input("Approval Date", value=approval_date_value)
                            edit_status = st.selectbox("Status", config.KML_STATUS, index=config.KML_STATUS.index(edit_data['Status']))
                        
                        edit_remarks = st.text_area("Remarks", value=edit_data['Remarks'])
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Update Record", use_container_width=True):
                                updated_data = {
                                    'Date': edit_date.strftime('%Y-%m-%d'),
                                    'KML_Count_Sent': edit_kml_count,
                                    'Total_Area': edit_total_area,
                                    'Area_Approved': edit_area_approved,
                                    'Approval_Date': edit_approval_date.strftime('%Y-%m-%d') if edit_approval_date else '',
                                    'Status': edit_status,
                                    'Remarks': edit_remarks
                                }
                                
                                if data_manager.update_record(project_name, 'kml_tracking', edit_index, updated_data):
                                    st.success("✅ Record updated successfully!")
                                    del st.session_state['edit_kml_record']
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update record.")
                        
                        with col2:
                            if st.form_submit_button("❌ Cancel", use_container_width=True):
                                del st.session_state['edit_kml_record']
                                st.rerun()
            
            # Show data table
            recent_kml = kml_df.head(10)
            st.dataframe(recent_kml, use_container_width=True)
    
    elif analysis_type == "Plantation Records":
        plantation_df = sp_manager.read_excel_file(project_name, config.FILE_NAMING['plantation_records'])
        chart_manager.create_interactive_filter_chart(plantation_df, "Plantation Records", project_name)
        
        # Show recent records with edit/delete options
        if not plantation_df.empty:
            st.subheader("📋 Recent Plantation Records")
            
            # Add edit/delete controls if user can edit
            if auth_manager.can_edit_data(project_name):
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🔧 Manage Records "):
                        st.session_state['show_plantation_edit'] = not st.session_state.get('show_plantation_edit', False)
            
            # Show edit interface if enabled
            if st.session_state.get('show_plantation_edit', False) and auth_manager.can_edit_data(project_name):
                st.subheader("✏️ Edit/Delete Plantation Records")
                
                # Select record to edit
                plantation_display = plantation_df.copy()
                plantation_display['Record_Index'] = range(len(plantation_display))
                plantation_display['Display'] = plantation_display.apply(
                    lambda row: f"{row['Date']} - {row['Plot_Code']} - {row['Area_Planted']}Ha", axis=1
                )
                
                selected_plantation_record = st.selectbox(
                    "Select Plantation Record to Edit/Delete",
                    options=plantation_display['Record_Index'].tolist(),
                    format_func=lambda x: plantation_display.loc[x, 'Display']
                )
                
                if selected_plantation_record is not None:
                    record_data = plantation_df.iloc[selected_plantation_record]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("✏️ Edit Plantation Record", use_container_width=True):
                            st.session_state['edit_plantation_record'] = selected_plantation_record
                    
                    with col2:
                        if st.button("🗑️ Delete Plantation Record", use_container_width=True, type="primary"):
                            if data_manager.delete_record(project_name, 'plantation_records', selected_plantation_record):
                                st.success("✅ Record deleted successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete record.")
                
                # Edit form for plantation records
                if 'edit_plantation_record' in st.session_state:
                    edit_index = st.session_state['edit_plantation_record']
                    edit_data = plantation_df.iloc[edit_index]
                    
                    st.subheader("✏️ Edit Plantation Record")
                    
                    with st.form("edit_plantation_form"):
                        edit_col1, edit_col2 = st.columns(2)
                        
                        with edit_col1:
                            edit_date = st.date_input("Date", pd.to_datetime(edit_data['Date']).date())
                            edit_plot_code = st.text_input("Plot Code", value=edit_data['Plot_Code'])
                            edit_area_planted = st.number_input("Area Planted", min_value=0.1, value=float(edit_data['Area_Planted']))
                            edit_farmer_covered = st.number_input("Farmers Covered", min_value=1, value=int(edit_data['Farmer_Covered']))
                        
                        with edit_col2:
                            edit_trees_planted = st.number_input("Trees Planted", min_value=1, value=int(edit_data['Trees_Planted']))
                            # Handle Pits_Dug safely in case of data inconsistency
                            try:
                                # Check for both old and new column names
                                if 'Pits_Dug' in edit_data:
                                    pits_dug_value = int(edit_data['Pits_Dug']) if pd.notna(edit_data['Pits_Dug']) else 0
                                elif 'Pit_Digging' in edit_data:
                                    pits_dug_value = 0  # Default for old status-based data
                                else:
                                    pits_dug_value = 0
                            except:
                                pits_dug_value = 0
                            edit_pits_dug = st.number_input("Pits Dug", min_value=0, value=pits_dug_value)
                            edit_status = st.selectbox("Status", ["Completed", "In Progress"], 
                                                     index=["Completed", "In Progress"].index(edit_data['Status']))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Update Plantation Record", use_container_width=True):
                                updated_data = {
                                    'Date': edit_date.strftime('%Y-%m-%d'),
                                    'Plot_Code': edit_plot_code,
                                    'Area_Planted': edit_area_planted,
                                    'Farmer_Covered': edit_farmer_covered,
                                    'Trees_Planted': edit_trees_planted,
                                    'Pits_Dug': edit_pits_dug,
                                    'Status': edit_status
                                }
                                
                                if data_manager.update_record(project_name, 'plantation_records', edit_index, updated_data):
                                    st.success("✅ Record updated successfully!")
                                    del st.session_state['edit_plantation_record']
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update record.")
                        
                        with col2:
                            if st.form_submit_button("❌ Cancel", use_container_width=True):
                                del st.session_state['edit_plantation_record']
                                st.rerun()
            
            # Show data table
            recent_plantation = plantation_df.head(10)
            st.dataframe(recent_plantation, use_container_width=True)

def show_add_data():
    """Show add data interface"""
    # Check user role - only admin and project managers can add data
    current_role = st.session_state.get('role', 'viewer')
    if current_role not in ['admin', 'project_manager']:
        st.error("⛔ Access denied. You do not have permission to add data.")
        st.info("Please contact an administrator if you believe this is an error.")
        return

    st.title("📝 Add Data")
    
    # Get user's accessible projects
    accessible_projects = get_user_accessible_projects()
    
    if not accessible_projects:
        st.warning("⚠️ You don't have access to any projects. Please contact an administrator.")
        return
    
    # Project selection
    project_name = st.selectbox("🏢 Select Project", accessible_projects)
    
    if not project_name:
        st.info("Please select a project to continue.")
        return
    
    # Discover all tables in the selected project
    project_path = f"local_data/projects/{project_name}"
    available_tables = []
    
    if os.path.exists(project_path):
        for file_name in os.listdir(project_path):
            if file_name.endswith('.xlsx'):
                table_name = file_name.replace('.xlsx', '').replace('_', ' ').title()
                available_tables.append(table_name)
    
    if not available_tables:
        st.info(f"No tables found for project '{project_name}'. Create tables in Schema Management first.")
        return
    
    # Table selection
    st.subheader("📋 Select Table Type")
    table_name = st.radio("Choose table to add data to:", available_tables)
    
    if table_name:
        show_table_form(project_name, table_name)

def show_kml_form(project_name: str):
    """Display KML tracking data entry form"""
    st.subheader("📋 KML Tracking Data Entry")
    
    # Initialize session state for form reset
    if 'kml_form_submitted' not in st.session_state:
        st.session_state.kml_form_submitted = False
    
    with st.form("kml_form", clear_on_submit=True):
        st.markdown('<div class="data-form">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", datetime.now().date())
            kml_count = st.number_input("Number of KML Files Sent", min_value=1, max_value=100, value=1)
            total_area = st.number_input("Total Area (Hectares)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1)
        
        with col2:
            area_approved = st.number_input("Area Approved (Hectares)", min_value=0.0, max_value=1000.0, value=0.0, step=0.1)
            approval_date = st.date_input("Approval Date (if approved)", value=None)
            status = st.selectbox("Status", config.KML_STATUS)
        
        remarks = st.text_area("Remarks", placeholder="Enter any additional notes...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button("💾 Save KML Record", use_container_width=True)
        
        if submitted:
            record_data = {
                'Date': date.strftime('%Y-%m-%d'),
                'KML_Count_Sent': kml_count,
                'Total_Area': total_area,
                'Area_Approved': area_approved,
                'Approval_Date': approval_date.strftime('%Y-%m-%d') if approval_date else '',
                'Status': status,
                'Remarks': remarks
            }
            
            if data_manager.add_kml_record(project_name, record_data):
                st.success("✅ KML record added successfully! Form has been reset for next entry.")
                st.session_state.kml_form_submitted = True
                # Add a small delay to show the success message
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Failed to add KML record. Please try again.")

def show_plantation_form(project_name: str):
    """Display plantation data entry form"""
    st.subheader("🌱 Plantation Record Data Entry")
    
    # Initialize session state for form reset
    if 'plantation_form_submitted' not in st.session_state:
        st.session_state.plantation_form_submitted = False
    
    with st.form("plantation_form", clear_on_submit=True):
        st.markdown('<div class="data-form">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", datetime.now().date())
            plot_code = st.text_input("Plot Code", placeholder="e.g., MMT-001")
            area_planted = st.number_input("Area Planted (Hectares)", min_value=0.1, max_value=1000.0, value=5.0, step=0.1)
            farmer_covered = st.number_input("Number of Farmers Covered", min_value=1, max_value=100, value=1)
        
        with col2:
            trees_planted = st.number_input("Number of Trees Planted", min_value=1, max_value=10000, value=100)
            pits_dug = st.number_input("Number of Pits Dug", min_value=0, max_value=10000, value=80)
            status = st.selectbox("Overall Status", ["Completed", "In Progress"])
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button("💾 Save Plantation Record", use_container_width=True)
        
        if submitted:
            record_data = {
                'Date': date.strftime('%Y-%m-%d'),
                'Plot_Code': plot_code,
                'Area_Planted': area_planted,
                'Farmer_Covered': farmer_covered,
                'Trees_Planted': trees_planted,
                'Pits_Dug': pits_dug,
                'Status': status
            }
            
            if data_manager.add_plantation_record(project_name, record_data):
                st.success("✅ Plantation record added successfully! Form has been reset for next entry.")
                st.session_state.plantation_form_submitted = True
                # Add a small delay to show the success message
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Failed to add plantation record. Please try again.")

def show_table_form(project_name: str, table_name: str):
    """Display dynamic form for any table data entry"""
    st.subheader(f"📝 {table_name} Data Entry")
    
    # Get table definition from all tables
    all_tables = get_all_tables()
    table_def = all_tables[all_tables['table_name'] == table_name]
    
    if table_def.empty:
        st.error("❌ Table definition not found!")
        return
    
    # Parse fields from table definition
    try:
        import ast
        fields_str = table_def.iloc[0]['fields']
        fields = ast.literal_eval(fields_str)
    except:
        st.error("❌ Error parsing table definition!")
        return
        
    # Get any additional fields from schema extensions
    schema_extensions = get_schema_extensions()
    additional_fields = pd.DataFrame()  # Initialize empty DataFrame
    
    # Check if schema_extensions has data and required columns
    if not schema_extensions.empty and 'table_type' in schema_extensions.columns:
        additional_fields = schema_extensions[schema_extensions['table_type'] == table_name]
    
    # Initialize session state for form reset
    form_key = f"{table_name.lower().replace(' ', '_')}_form_submitted"
    if form_key not in st.session_state:
        st.session_state[form_key] = False
    
    with st.form(f"{table_name.lower().replace(' ', '_')}_form", clear_on_submit=True):
        st.markdown('<div class="data-form">', unsafe_allow_html=True)
        
        record_data = {}
        
        # Create form fields dynamically
        col1, col2 = st.columns(2)
        field_count = 0
        
        # Process original table fields
        for field in fields:
            if not field.get('name'):
                continue
                
            field_name = field['name']
            field_type = field['type']
            required = field.get('required', False)
            description = field.get('description', '')
            
            # Alternate between columns
            col = col1 if field_count % 2 == 0 else col2
            
            with col:
                if field_type == "Date":
                    value = st.date_input(
                        field_name, 
                        datetime.now().date(),
                        help=description
                    )
                    record_data[field_name] = value.strftime('%Y-%m-%d')
                    
                elif field_type == "Number":
                    value = st.number_input(
                        field_name,
                        min_value=0.0,
                        value=0.0,
                        step=0.1,
                        help=description
                    )
                    record_data[field_name] = value
                    
                elif field_type == "True/False":
                    value = st.checkbox(field_name, help=description)
                    record_data[field_name] = value
                    
                elif field_type == "Dropdown":
                    # Get dropdown options if available
                    options = ["Option 1", "Option 2", "Option 3"]  # Default
                    value = st.selectbox(field_name, options, help=description)
                    record_data[field_name] = value
                    
                else:  # Text
                    value = st.text_input(
                        field_name,
                        placeholder=f"Enter {field_name.lower()}",
                        help=description
                    )
                    record_data[field_name] = value
            
            field_count += 1
        
        # Process additional fields from schema extensions
        for _, field_row in additional_fields.iterrows():
            field_name = field_row['field_name']
            field_type = field_row['field_type']
            required = field_row.get('is_required', False)
            description = field_row.get('description', '')
            dropdown_options = field_row.get('dropdown_options', '')
            default_value = field_row.get('default_value', '')
            
            # Alternate between columns
            col = col1 if field_count % 2 == 0 else col2
            
            with col:
                if field_type == "Date":
                    default_date = datetime.now().date()
                    if default_value:
                        try:
                            default_date = pd.to_datetime(default_value).date()
                        except:
                            pass
                    value = st.date_input(field_name, default_date, help=description)
                    record_data[field_name] = value.strftime('%Y-%m-%d')
                    
                elif field_type == "Number":
                    default_num = float(default_value) if default_value else 0.0
                    value = st.number_input(
                        field_name,
                        min_value=0.0,
                        value=default_num,
                        step=0.1,
                        help=description
                    )
                    record_data[field_name] = value
                    
                elif field_type == "True/False":
                    default_bool = default_value.lower() == 'true' if default_value else False
                    value = st.checkbox(field_name, value=default_bool, help=description)
                    record_data[field_name] = value
                    
                elif field_type == "Dropdown":
                    options = dropdown_options.split('\n') if dropdown_options else ["Option 1", "Option 2"]
                    options = [opt.strip() for opt in options if opt.strip()]
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
            # For special table types, use their specific add functions
            if table_name == "Kml Tracking":
                success = data_manager.add_kml_record(project_name, record_data)
            elif table_name == "Plantation Records":
                success = data_manager.add_plantation_record(project_name, record_data)
            else:
                success = add_table_record(project_name, table_name, record_data)
                
            if success:
                st.success(f"✅ {table_name} record added successfully! Form has been reset for next entry.")
                st.session_state[form_key] = True
                # Add a small delay to show the success message
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ Failed to add {table_name} record. Please try again.")

def show_custom_table_form(project_name: str, table_name: str):
    """Backward compatibility wrapper"""
    show_table_form(project_name, table_name)

def add_table_record(project_name: str, table_name: str, record_data: dict) -> bool:
    """Add record to any table (unified approach)"""
    try:
        # Convert table name to file name
        file_name = table_name.lower().replace(' ', '_') + '.xlsx'
        file_path = f"local_data/projects/{project_name}/{file_name}"
        
        # Ensure project directory exists
        project_dir = f"local_data/projects/{project_name}"
        os.makedirs(project_dir, exist_ok=True)
        
        # Load existing data or create new DataFrame
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
        else:
            # Create new file with columns from record_data
            df = pd.DataFrame(columns=list(record_data.keys()))
        
        # Add the new record
        new_record = pd.DataFrame([record_data])
        df = pd.concat([df, new_record], ignore_index=True)
        
        # Save the data
        df.to_excel(file_path, index=False)
        return True
        
    except Exception as e:
        st.error(f"Error adding record to {table_name}: {str(e)}")
        return False

def add_custom_table_record(project_name: str, table_name: str, record_data: dict) -> bool:
    """Backward compatibility wrapper"""
    return add_table_record(project_name, table_name, record_data)

def show_user_management():
    """Display user management page (Admin only)"""
    current_role = st.session_state.get('role', 'viewer')
    if current_role != 'admin':
        st.error("❌ Access denied. Admin privileges required.")
        return
    
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
                if new_role == "project_manager" or new_role == "viewer":
                    try:
                        all_projects = data_manager.get_all_project_names()
                    except:
                        all_projects = ['MakeMyTrip', 'Absolute']
                    accessible_projects = st.multiselect("Accessible Projects", all_projects)
                else:
                    try:
                        all_projects = data_manager.get_all_project_names()
                    except:
                        all_projects = ['MakeMyTrip', 'Absolute']
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
                    # Clear cache to force refresh
                    if 'users_cache' in st.session_state:
                        del st.session_state['users_cache']
                    st.rerun()
                else:
                    st.error("❌ Failed to create user. Username might already exist.")
    
    with tab2:
        st.subheader("Current Users")
        
        # Add refresh button
        if st.button("🔄 Refresh User List"):
            if 'users_cache' in st.session_state:
                del st.session_state['users_cache']
            st.rerun()
        
        users_df = get_users_dataframe()
        if not users_df.empty:
            st.dataframe(users_df, use_container_width=True)
            
            # Delete user functionality
            st.subheader("Delete User")
            user_to_delete = st.selectbox("Select user to delete", users_df['Username'].tolist())
            if st.button("🗑️ Delete User", type="secondary"):
                if user_to_delete != st.session_state.get('username', ''):
                    if delete_user(user_to_delete):
                        st.success(f"✅ User '{user_to_delete}' deleted successfully!")
                        # Clear cache and refresh
                        if 'users_cache' in st.session_state:
                            del st.session_state['users_cache']
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete user.")
                else:
                    st.error("❌ You cannot delete your own account.")
        else:
            st.info("No users found.")
    
    with tab3:
        st.subheader("Edit User")
        users_df = get_users_dataframe()
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
                            if edit_role == "project_manager" or edit_role == "viewer":
                                try:
                                    all_projects = data_manager.get_all_project_names()
                                except:
                                    all_projects = ['MakeMyTrip', 'Absolute']
                                
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
                                        
                                        # Filter out any NaN values or invalid projects
                                        current_projects = [p for p in current_projects if p in all_projects and not (isinstance(p, float) and math.isnan(p))]
                                    except:
                                        current_projects = []
                                else:
                                    current_projects = []
                                
                                # Make sure current_projects only contains valid options from all_projects
                                valid_projects = [p for p in current_projects if p in all_projects]
                                
                                edit_accessible_projects = st.multiselect(
                                    "Accessible Projects", 
                                    all_projects, 
                                    default=valid_projects
                                )
                            else:
                                try:
                                    all_projects = data_manager.get_all_project_names()
                                except:
                                    all_projects = ['MakeMyTrip', 'Absolute']
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
                                        # Clear cache to force refresh
                                        if 'users_cache' in st.session_state:
                                            del st.session_state['users_cache']
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to update user.")
                            else:
                                if update_user(user_to_edit, update_data):
                                    st.success(f"✅ User '{user_to_edit}' updated successfully!")
                                    # Clear cache to force refresh
                                    if 'users_cache' in st.session_state:
                                        del st.session_state['users_cache']
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update user.")
                else:
                    st.error("❌ User data not found.")
        else:
            st.info("No users available for editing.")

def get_users_dataframe() -> pd.DataFrame:
    """Get users as DataFrame for display"""
    try:
        # Try to get users from the SharePoint manager
        users_df = sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
        
        if not users_df.empty:
            # Show relevant columns for display and ensure proper data types
            display_columns = ['Username', 'Full_Name', 'Role', 'Assigned_Projects', 'Email', 'Status']
            available_columns = [col for col in display_columns if col in users_df.columns]
            display_df = users_df[available_columns].copy()
            
            # Convert all columns to string to avoid PyArrow type errors
            for col in display_df.columns:
                display_df[col] = display_df[col].astype(str)
            
            # Clean up NaN values
            display_df = display_df.fillna('')
            
            return display_df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")
        return pd.DataFrame()

def get_user_data(username: str) -> dict:
    """Get user data for editing"""
    try:
        users_df = sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
        if not users_df.empty:
            user_row = users_df[users_df['Username'] == username]
            if not user_row.empty:
                user_data = user_row.iloc[0].to_dict()
                # No need to convert accessible_projects here as we handle it in the form
                return user_data
        return {}
    except Exception as e:
        st.error(f"Error getting user data: {str(e)}")
        return {}

def create_user(username: str, password: str, role: str, accessible_projects: list, full_name: str, email: str) -> bool:
    """Create a new user"""
    try:
        users_df = sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
        
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
            'Password_Hash': sp_manager.hash_password(password),  # Use the existing hash function
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
        
        # Save to file
        sp_manager.write_excel_file(None, config.FILE_NAMING['users'], users_df)
        return True
        
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return False

def update_user(username: str, update_data: dict) -> bool:
    """Update user data"""
    try:
        users_df = sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
        
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
                    users_df.at[idx, 'Password_Hash'] = sp_manager.hash_password(update_data['password'])
                
                # Save updated data
                sp_manager.write_excel_file(None, config.FILE_NAMING['users'], users_df)
                return True
        return False
    except Exception as e:
        st.error(f"Error updating user: {str(e)}")
        return False

def delete_user(username: str) -> bool:
    """Delete a user"""
    try:
        users_df = sp_manager.read_excel_file(None, config.FILE_NAMING['users'])
        
        if not users_df.empty:
            users_df = users_df[users_df['Username'] != username]
            sp_manager.write_excel_file(None, config.FILE_NAMING['users'], users_df)
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting user: {str(e)}")
        return False

def show_project_management():
    """Display project management interface (admin only)"""
    auth_manager.require_role('admin')
    
    st.markdown("""
    <div class="main-header">
        <h1>🏗️ Project Management</h1>
        <p>Create and manage plantation projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display current projects
    projects_df = sp_manager.read_excel_file(None, config.FILE_NAMING['projects'])
    
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
            status = st.selectbox("Status*", config.PROJECT_STATUS)
        
        manager = st.selectbox("Project Manager", auth_manager.get_all_users()['Username'].tolist() if not auth_manager.get_all_users().empty else [])
        
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
                    'Manager': manager
                }
                
                if sp_manager.create_project(project_data):
                    st.success("✅ Project created successfully!")
                    st.rerun()
            else:
                st.error("❌ Please fill in all required fields.")

def show_reports():
    """Display reports generation page"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Reports</h1>
        <p>Generate and download various reports for your projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get projects accessible based on user role
    current_role = st.session_state.get('role', 'viewer')
    
    if current_role == 'admin':
        # Admin can see all projects
        try:
            accessible_projects = data_manager.get_all_project_names()
        except:
            accessible_projects = ['MakeMyTrip', 'Absolute']
    elif current_role == 'viewer':
        # Viewers can see all projects but in read-only mode
        try:
            accessible_projects = data_manager.get_all_project_names()
        except:
            accessible_projects = ['MakeMyTrip', 'Absolute']
    else:
        # Project managers see only their assigned projects
        accessible_projects = get_user_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible for reports.")
        return
    
    # Project selection
    selected_project = st.selectbox("Select Project", accessible_projects)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Date Range Reports")
        
        # Date range selection
        date_range = st.selectbox(
            "Select Report Period",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"]
        )
        
        if date_range == "Custom Range":
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
        else:
            end_date = datetime.now().date()
            if date_range == "Last 7 Days":
                start_date = end_date - timedelta(days=7)
            elif date_range == "Last 30 Days":
                start_date = end_date - timedelta(days=30)
            else:  # Last 90 Days
                start_date = end_date - timedelta(days=90)
        
        # Report type selection
        report_type = st.selectbox(
            "Select Report Type",
            ["Summary Report", "Detailed KML Report", "Detailed Plantation Report", "Combined Report"]
        )
        
        if st.button("📥 Generate & Download Report", use_container_width=True):
            generate_report(selected_project, start_date, end_date, report_type)
    
    with col2:
        st.subheader("📈 Quick Reports")
        
        if st.button("📊 Project Overview", use_container_width=True):
            generate_project_overview(selected_project)
        
        if st.button("📋 Current Month Summary", use_container_width=True):
            current_month_start = datetime.now().replace(day=1).date()
            generate_report(selected_project, current_month_start, datetime.now().date(), "Summary Report")
        
        if st.button("🌱 Plantation Progress", use_container_width=True):
            generate_plantation_progress_report(selected_project)
        
        if st.button("📄 KML Tracking Status", use_container_width=True):
            generate_kml_status_report(selected_project)

def generate_report(project_name: str, start_date, end_date, report_type: str):
    """Generate and download report based on parameters"""
    try:
        # Get data for the date range using existing DataManager methods
        kml_data = data_manager.get_kml_data(project_name)
        plantation_data = data_manager.get_plantation_data(project_name)
        
        # Filter by date range
        if not kml_data.empty and 'Date' in kml_data.columns:
            kml_data['Date'] = pd.to_datetime(kml_data['Date'], errors='coerce')
            kml_data = kml_data[(kml_data['Date'] >= pd.to_datetime(start_date)) & 
                               (kml_data['Date'] <= pd.to_datetime(end_date))]
        
        if not plantation_data.empty and 'Date' in plantation_data.columns:
            plantation_data['Date'] = pd.to_datetime(plantation_data['Date'], errors='coerce')
            plantation_data = plantation_data[(plantation_data['Date'] >= pd.to_datetime(start_date)) & 
                                            (plantation_data['Date'] <= pd.to_datetime(end_date))]
        
        # Generate report filename
        report_filename = f"{project_name}_{report_type.replace(' ', '_')}_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
        
        # Create Excel writer
        with pd.ExcelWriter(report_filename, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Create summary sheet
            if report_type in ["Summary Report", "Combined Report"]:
                create_summary_sheet(writer, workbook, kml_data, plantation_data, project_name)
            
            # Create detailed sheets based on report type
            if report_type in ["Detailed KML Report", "Combined Report"]:
                if not kml_data.empty:
                    kml_data.to_excel(writer, sheet_name='KML Details', index=False)
                    format_worksheet(writer.sheets['KML Details'], workbook)
            
            if report_type in ["Detailed Plantation Report", "Combined Report"]:
                if not plantation_data.empty:
                    plantation_data.to_excel(writer, sheet_name='Plantation Details', index=False)
                    format_worksheet(writer.sheets['Plantation Details'], workbook)
        
        # Provide download link
        with open(report_filename, 'rb') as file:
            st.download_button(
                label=f"📥 Download {report_type}",
                data=file.read(),
                file_name=report_filename,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        st.success(f"✅ Report generated successfully! Click the download button above.")
        
        # Clean up the local file
        os.remove(report_filename)
        
    except Exception as e:
        st.error(f"❌ Error generating report: {str(e)}")

def generate_plantation_progress_report(project_name: str):
    """Generate plantation progress report"""
    try:
        plantation_data = data_manager.get_plantation_data(project_name)
        
        if plantation_data.empty:
            st.warning("No plantation data available for this project.")
            return
        
        report_filename = f"{project_name}_Plantation_Progress_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        with pd.ExcelWriter(report_filename, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Progress summary
            progress_data = []
            progress_data.append(['PLANTATION PROGRESS REPORT', ''])
            progress_data.append(['Project', project_name])
            
            # Safe calculations with error handling
            total_plots = plantation_data['Plot_Code'].nunique() if 'Plot_Code' in plantation_data.columns else 0
            total_area = plantation_data['Area_Planted'].sum() if 'Area_Planted' in plantation_data.columns else 0
            total_trees = plantation_data['Trees_Planted'].sum() if 'Trees_Planted' in plantation_data.columns else 0
            total_farmers = plantation_data['Farmer_Covered'].sum() if 'Farmer_Covered' in plantation_data.columns else 0
            
            progress_data.append(['Total Plots', total_plots])
            progress_data.append(['Total Area Planted', f"{total_area:.2f} hectares"])
            progress_data.append(['Total Trees Planted', total_trees])
            progress_data.append(['Total Farmers Covered', total_farmers])
            
            if total_area > 0:
                progress_data.append(['Average Trees per Hectare', f"{total_trees / total_area:.0f}"])
            
            df = pd.DataFrame(progress_data, columns=['Metric', 'Value'])
            df.to_excel(writer, sheet_name='Progress Summary', index=False)
            format_worksheet(writer.sheets['Progress Summary'], workbook, is_summary=True)
            
            # Detailed data
            plantation_data.to_excel(writer, sheet_name='Detailed Data', index=False)
            format_worksheet(writer.sheets['Detailed Data'], workbook)
        
        with open(report_filename, 'rb') as file:
            st.download_button(
                label="📥 Download Plantation Progress Report",
                data=file.read(),
                file_name=report_filename,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        st.success("✅ Plantation progress report generated!")
        os.remove(report_filename)
        
    except Exception as e:
        st.error(f"❌ Error generating plantation report: {str(e)}")

def generate_kml_status_report(project_name: str):
    """Generate KML status report"""
    try:
        kml_data = data_manager.get_kml_data(project_name)
        
        if kml_data.empty:
            st.warning("No KML data available for this project.")
            return
        
        report_filename = f"{project_name}_KML_Status_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        with pd.ExcelWriter(report_filename, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Status summary
            if 'Status' in kml_data.columns:
                status_summary = kml_data['Status'].value_counts().reset_index()
                status_summary.columns = ['Status', 'Count']
                status_summary.to_excel(writer, sheet_name='Status Summary', index=False)
                format_worksheet(writer.sheets['Status Summary'], workbook)
            
            # Detailed data
            kml_data.to_excel(writer, sheet_name='Detailed Data', index=False)
            format_worksheet(writer.sheets['Detailed Data'], workbook)
        
        with open(report_filename, 'rb') as file:
            st.download_button(
                label="📥 Download KML Status Report",
                data=file.read(),
                file_name=report_filename,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        st.success("✅ KML status report generated!")
        os.remove(report_filename)
        
    except Exception as e:
        st.error(f"❌ Error generating KML report: {str(e)}")

def create_summary_sheet(writer, workbook, kml_data, plantation_data, project_name):
    """Create summary sheet for the report"""
    summary_data = []
    
    # Project information
    summary_data.append(['Project Name', project_name])
    summary_data.append(['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    summary_data.append(['', ''])
    
    # KML Summary
    summary_data.append(['KML TRACKING SUMMARY', ''])
    if not kml_data.empty:
        kml_count = kml_data['KML_Count_Sent'].sum() if 'KML_Count_Sent' in kml_data.columns else 0
        total_area = kml_data['Total_Area'].sum() if 'Total_Area' in kml_data.columns else 0
        area_approved = kml_data['Area_Approved'].sum() if 'Area_Approved' in kml_data.columns else 0
        
        summary_data.append(['Total KML Files Sent', kml_count])
        summary_data.append(['Total Area Submitted', f"{total_area:.2f} hectares"])
        summary_data.append(['Total Area Approved', f"{area_approved:.2f} hectares"])
        
        if total_area > 0:
            summary_data.append(['Approval Rate', f"{(area_approved / total_area * 100):.1f}%"])
    else:
        summary_data.append(['No KML data available', ''])
    
    summary_data.append(['', ''])
    
    # Plantation Summary
    summary_data.append(['PLANTATION SUMMARY', ''])
    if not plantation_data.empty:
        area_planted = plantation_data['Area_Planted'].sum() if 'Area_Planted' in plantation_data.columns else 0
        trees_planted = plantation_data['Trees_Planted'].sum() if 'Trees_Planted' in plantation_data.columns else 0
        farmers_covered = plantation_data['Farmer_Covered'].sum() if 'Farmer_Covered' in plantation_data.columns else 0
        pits_dug = plantation_data['Pits_Dug'].sum() if 'Pits_Dug' in plantation_data.columns else 0
        
        summary_data.append(['Total Area Planted', f"{area_planted:.2f} hectares"])
        summary_data.append(['Total Trees Planted', trees_planted])
        summary_data.append(['Total Farmers Covered', farmers_covered])
        summary_data.append(['Total Pits Dug', pits_dug])
    else:
        summary_data.append(['No plantation data available', ''])
    
    # Convert to DataFrame and save
    summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
    summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # Format the summary sheet
    format_worksheet(writer.sheets['Summary'], workbook, is_summary=True)

def format_worksheet(worksheet, workbook, is_summary=False):
    """Format Excel worksheet"""
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#4CAF50',
        'font_color': 'white',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'text_wrap': True,
        'valign': 'top',
        'border': 1
    })
    
    if is_summary:
        # Format summary sheet
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 20)
        worksheet.set_row(0, 20, header_format)
    else:
        # Format data sheets
        worksheet.set_column('A:Z', 15)
        worksheet.set_row(0, 20, header_format)

def generate_project_overview(project_name: str):
    """Generate project overview report"""
    try:
        report_filename = f"{project_name}_Project_Overview_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # Get all data
        kml_data = data_manager.get_kml_data(project_name)
        plantation_data = data_manager.get_plantation_data(project_name)
        
        with pd.ExcelWriter(report_filename, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Create overview sheet
            create_overview_sheet(writer, workbook, kml_data, plantation_data, project_name)
            
            # Add monthly trends
            create_monthly_trends_sheet(writer, workbook, kml_data, plantation_data)
        
        # Download
        with open(report_filename, 'rb') as file:
            st.download_button(
                label="📥 Download Project Overview",
                data=file.read(),
                file_name=report_filename,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        st.success("✅ Project overview report generated!")
        os.remove(report_filename)
        
    except Exception as e:
        st.error(f"❌ Error generating overview: {str(e)}")

def create_overview_sheet(writer, workbook, kml_data, plantation_data, project_name):
    """Create project overview sheet"""
    overview_data = []
    
    # Header
    overview_data.append([f'PROJECT OVERVIEW - {project_name}', ''])
    overview_data.append(['Generated on', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    overview_data.append(['', ''])
    
    # Overall statistics
    overview_data.append(['OVERALL STATISTICS', ''])
    overview_data.append(['Total Records', len(kml_data) + len(plantation_data)])
    overview_data.append(['Date Range', f"{min(kml_data['Date'].min() if not kml_data.empty else datetime.now().date(), plantation_data['Date'].min() if not plantation_data.empty else datetime.now().date())} to {max(kml_data['Date'].max() if not kml_data.empty else datetime.now().date(), plantation_data['Date'].max() if not plantation_data.empty else datetime.now().date())}"])
    
    df = pd.DataFrame(overview_data, columns=['Metric', 'Value'])
    df.to_excel(writer, sheet_name='Overview', index=False)
    format_worksheet(writer.sheets['Overview'], workbook, is_summary=True)

def create_monthly_trends_sheet(writer, workbook, kml_data, plantation_data):
    """Create monthly trends analysis"""
    trends_data = []
    
    # Get monthly aggregations
    if not kml_data.empty:
        kml_data['Month'] = pd.to_datetime(kml_data['Date']).dt.to_period('M')
        kml_monthly = kml_data.groupby('Month').agg({
            'KML_Count_Sent': 'sum',
            'Total_Area': 'sum',
            'Area_Approved': 'sum'
        }).reset_index()
        kml_monthly['Month'] = kml_monthly['Month'].astype(str)
        
        trends_data.append(['KML MONTHLY TRENDS', '', '', ''])
        trends_data.append(['Month', 'KML Files', 'Area Submitted', 'Area Approved'])
        for _, row in kml_monthly.iterrows():
            trends_data.append([row['Month'], row['KML_Count_Sent'], row['Total_Area'], row['Area_Approved']])
    
    df = pd.DataFrame(trends_data)
    df.to_excel(writer, sheet_name='Monthly Trends', index=False, header=False)
    format_worksheet(writer.sheets['Monthly Trends'], workbook)

def show_schema_management():
    """Display schema management page (Admin only)"""
    current_role = st.session_state.get('role', 'viewer')
    if current_role != 'admin':
        st.error("❌ Access denied. Admin privileges required.")
        return
    
    st.markdown("""
    <div class="main-header">
        <h1>🔧 Schema Management</h1>
        <p>Manage database tables and fields</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 View Schema", "➕ Add Field", "✏️ Edit Field", "🗑️ Delete Field", "🆕 Manage Tables"])
    
    with tab1:
        st.subheader("Current Database Schema")
        
        # Get available projects
        try:
            projects = data_manager.get_all_project_names()
        except:
            projects = []
            projects_dir = "local_data/projects"
            if os.path.exists(projects_dir):
                projects = [name for name in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, name))]
        
        if not projects:
            st.error("No projects found")
            return
        
        selected_project = st.selectbox("Select Project to View Schema", projects)
        
        # Discover all tables in the selected project
        project_path = f"local_data/projects/{selected_project}"
        discovered_tables = []
        
        if os.path.exists(project_path):
            for file_name in os.listdir(project_path):
                if file_name.endswith('.xlsx'):
                    table_name = file_name.replace('.xlsx', '').replace('_', ' ').title()
                    discovered_tables.append((table_name, file_name))
        
        if not discovered_tables:
            st.info(f"No tables found in project '{selected_project}'")
            return
        
        # Show schemas for all discovered tables
        num_cols = min(3, len(discovered_tables))
        cols = st.columns(num_cols)
        
        for i, (table_name, file_name) in enumerate(discovered_tables):
            with cols[i % num_cols]:
                st.markdown(f"**{table_name} Table**")
                
                try:
                    file_path = os.path.join(project_path, file_name)
                    table_data = pd.read_excel(file_path)
                    
                    if not table_data.empty:
                        schema_info = []
                        for col in table_data.columns:
                            dtype = str(table_data[col].dtype)
                            # Simplify dtype display
                            if 'int' in dtype:
                                dtype = 'Number'
                            elif 'float' in dtype:
                                dtype = 'Number'
                            elif 'datetime' in dtype or 'date' in dtype:
                                dtype = 'Date'
                            elif 'bool' in dtype:
                                dtype = 'True/False'
                            else:
                                dtype = 'Text'
                            
                            schema_info.append([col, dtype, "Optional"])
                        
                        schema_df = pd.DataFrame(schema_info, columns=['Field Name', 'Data Type', 'Required'])
                        st.dataframe(schema_df, use_container_width=True)
                    else:
                        st.info(f"No data in {table_name} to analyze schema")
                
                except Exception as e:
                    st.error(f"Error reading {table_name}: {str(e)}")
        
        # Show schema extensions if any
        st.markdown("**Added Fields (Schema Extensions)**")
        schema_extensions = get_schema_extensions()
        if not schema_extensions.empty:
            # Filter extensions for selected project tables
            project_extensions = schema_extensions[
                schema_extensions['table_type'].isin([t[0] for t in discovered_tables])
            ]
            if not project_extensions.empty:
                st.dataframe(project_extensions, use_container_width=True)
            else:
                st.info("No schema extensions for current project tables")
        else:
            st.info("No additional fields added to existing tables")

    with tab2:
        st.subheader("➕ Add Field to Existing Table")
        
        # Get all tables
        all_tables = get_all_tables()
        if all_tables.empty:
            st.warning("No tables found to add fields to.")
        else:
            available_tables = all_tables['table_name'].tolist()
            
            with st.form("add_field_form"):
                selected_table = st.selectbox("Select Table to Add Field to:", available_tables)
                field_name = st.text_input("Field Name:")
                field_type = st.selectbox("Field Type:", ["Text", "Number", "Date", "True/False", "Dropdown"])
                default_value = st.text_input("Default Value (optional):")
                is_required = st.checkbox("Required Field")
                
                dropdown_options = ""
                if field_type == "Dropdown":
                    dropdown_options = st.text_area("Dropdown Options (one per line):")
                
                description = st.text_area("Field Description (optional):")
                
                submitted = st.form_submit_button("Add Field")
                
                if submitted and selected_table and field_name:
                    if add_field_to_schema(selected_table, field_name, field_type, default_value, is_required, dropdown_options, description):
                        st.success(f"✅ Field '{field_name}' added to {selected_table} successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Failed to add field. Field may already exist.")
    
    with tab3:
        st.subheader("✏️ Edit Existing Field")
        
        schema_extensions = get_schema_extensions()
        if schema_extensions.empty:
            st.info("No custom fields to edit.")
        else:
            st.markdown("**Current Custom Fields:**")
            st.dataframe(schema_extensions, use_container_width=True)
            
            with st.form("edit_field_form"):
                field_index = st.number_input("Field Index to Edit:", min_value=0, max_value=len(schema_extensions)-1, value=0)
                
                if field_index < len(schema_extensions):
                    current_field = schema_extensions.iloc[field_index]
                    
                    st.markdown(f"**Editing:** {current_field['field_name']} in {current_field['table_type']}")
                    
                    new_field_name = st.text_input("New Field Name:", value=current_field['field_name'])
                    new_field_type = st.selectbox("New Field Type:", ["Text", "Number", "Date", "True/False", "Dropdown"], 
                                                 index=["Text", "Number", "Date", "True/False", "Dropdown"].index(current_field['field_type']) if current_field['field_type'] in ["Text", "Number", "Date", "True/False", "Dropdown"] else 0)
                    new_default_value = st.text_input("New Default Value:", value=current_field.get('default_value', ''))
                    new_is_required = st.checkbox("Required Field", value=current_field.get('is_required', False))
                    new_dropdown_options = st.text_area("New Dropdown Options:", value=current_field.get('dropdown_options', ''))
                    new_description = st.text_area("New Description:", value=current_field.get('description', ''))
                    
                    submitted = st.form_submit_button("Update Field")
                    
                    if submitted:
                        update_data = {
                            'field_name': new_field_name,
                            'field_type': new_field_type,
                            'default_value': new_default_value,
                            'is_required': new_is_required,
                            'dropdown_options': new_dropdown_options,
                            'description': new_description
                        }
                        
                        if edit_field_in_schema(field_index, update_data):
                            st.success("✅ Field updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to update field.")
    
    with tab4:
        st.subheader("🗑️ Delete Field")
        
        schema_extensions = get_schema_extensions()
        if schema_extensions.empty:
            st.info("No custom fields to delete.")
        else:
            st.markdown("**Current Custom Fields:**")
            st.dataframe(schema_extensions, use_container_width=True)
            
            with st.form("delete_field_form"):
                field_index = st.number_input("Field Index to Delete:", min_value=0, max_value=len(schema_extensions)-1, value=0)
                
                if field_index < len(schema_extensions):
                    current_field = schema_extensions.iloc[field_index]
                    st.warning(f"⚠️ You are about to delete: **{current_field['field_name']}** from **{current_field['table_type']}**")
                    st.error("This action cannot be undone and will remove the field from all project data!")
                    
                    confirm_delete = st.checkbox("I understand this will permanently delete the field")
                    submitted = st.form_submit_button("Delete Field", type="primary")
                    
                    if submitted and confirm_delete:
                        if delete_field_from_schema(field_index):
                            st.success("✅ Field deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete field.")
    
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
                col1, col2 = st.columns(2)
                with col1:
                    field_name = st.text_input(f"Field {i+1} Name:", key=f"field_name_{i}")
                with col2:
                    field_type = st.selectbox(f"Field {i+1} Type:", ["Text", "Number", "Date", "True/False"], key=f"field_type_{i}")
                
                if field_name:
                    fields.append({
                        'name': field_name,
                        'type': field_type,
                        'required': False,
                        'default': ''
                    })
            
            submitted = st.form_submit_button("Create Table")
            
            if submitted and table_name and fields:
                if create_new_table(table_name, table_description, fields):
                    st.success(f"✅ Table '{table_name}' created successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to create table. Table may already exist.")
        
        # Show existing custom tables
        st.markdown("---")
        st.markdown("**Existing Custom Tables**")
        custom_tables = get_custom_tables()
        if custom_tables.empty:
            st.info("No custom tables created yet.")
        else:
            st.dataframe(custom_tables, use_container_width=True)
            
            # Add table deletion functionality
            st.markdown("**Delete Existing Table**")
            with st.form("delete_table_form"):
                if not custom_tables.empty:
                    table_to_delete = st.selectbox("Select Table to Delete:", custom_tables['table_name'].tolist())
                    
                    st.warning(f"⚠️ You are about to delete the table: **{table_to_delete}**")
                    st.error("This action cannot be undone and will remove all data in this table across all projects!")
                    
                    confirm_delete = st.checkbox("I understand this will permanently delete the table and all its data")
                    submitted = st.form_submit_button("Delete Table", type="primary")
                    
                    if submitted and confirm_delete and table_to_delete:
                        if delete_custom_table(table_to_delete):
                            st.success(f"✅ Table '{table_to_delete}' deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete table.")

def get_user_accessible_projects():
    """Get projects accessible to current user"""
    current_role = st.session_state.get('role', 'viewer')
    assigned_projects = st.session_state.get('assigned_projects', '')
    
    # Get actual project list from DataManager
    try:
        all_projects = data_manager.get_all_project_names()
    except:
        # Fallback to default projects if DataManager is not available
        all_projects = ['MakeMyTrip', 'Absolute']
    
    if current_role == 'admin' or assigned_projects == 'All':
        return all_projects
    elif assigned_projects:
        # Convert assigned_projects to string if it's not already
        if not isinstance(assigned_projects, str):
            try:
                assigned_projects = str(assigned_projects)
            except:
                return all_projects  # Return all projects if conversion fails
        
        # Handle the case where assigned_projects is a single project (no commas)
        if ',' in assigned_projects:
            project_list = [p.strip() for p in assigned_projects.split(',')]
        else:
            project_list = [assigned_projects.strip()]
            
        # Filter to only include existing projects
        return [p for p in project_list if p in all_projects]
    else:
        return all_projects

def manage_kml_records(project_name: str):
    """Manage KML tracking records"""
    try:
        kml_data = data_manager.get_kml_data(project_name)
        
        if kml_data.empty:
            st.info("No KML records found for this project.")
            return
        
        st.subheader("📄 KML Tracking Records")
        
        # Display records with edit/delete options
        for idx, record in kml_data.iterrows():
            with st.expander(f"Record {idx + 1}: {record.get('Date', 'N/A')} - {record.get('KML_Count_Sent', 0)} KML files"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Date:** {record.get('Date', 'N/A')}")
                    st.write(f"**KML Files:** {record.get('KML_Count_Sent', 0)}")
                    st.write(f"**Total Area:** {record.get('Total_Area', 0)} hectares")
                    st.write(f"**Status:** {record.get('Status', 'N/A')}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_kml_{idx}"):
                        edit_kml_record(project_name, idx, record)
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_kml_{idx}"):
                        if delete_kml_record(project_name, idx):
                            st.success("Record deleted successfully!")
                            st.rerun()
    
    except Exception as e:
        st.error(f"Error loading KML records: {str(e)}")

def manage_plantation_records(project_name: str):
    """Manage plantation records"""
    try:
        plantation_data = data_manager.get_plantation_data(project_name)
        
        if plantation_data.empty:
            st.info("No plantation records found for this project.")
            return
        
        st.subheader("🌱 Plantation Records")
        
        # Display records with edit/delete options
        for idx, record in plantation_data.iterrows():
            with st.expander(f"Record {idx + 1}: {record.get('Date', 'N/A')} - Plot {record.get('Plot_Code', 'N/A')}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Date:** {record.get('Date', 'N/A')}")
                    st.write(f"**Plot Code:** {record.get('Plot_Code', 'N/A')}")
                    st.write(f"**Area Planted:** {record.get('Area_Planted', 0)} hectares")
                    st.write(f"**Trees Planted:** {record.get('Trees_Planted', 0)}")
                    st.write(f"**Status:** {record.get('Status', 'N/A')}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_plant_{idx}"):
                        edit_plantation_record(project_name, idx, record)
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_plant_{idx}"):
                        if delete_plantation_record(project_name, idx):
                            st.success("Record deleted successfully!")
                            st.rerun()
    
    except Exception as e:
        st.error(f"Error loading plantation records: {str(e)}")

def manage_table_records(project_name: str, table_name: str):
    """Manage records for any table (unified approach)"""
    try:
        table_data = get_table_data(project_name, table_name)
        
        if table_data.empty:
            st.info(f"No {table_name} records found for this project.")
            return
        
        st.subheader(f"📄 {table_name} Records")
        
        # Display records with edit/delete options
        for idx, record in table_data.iterrows():
            # Create a summary of the record for the expander
            summary_fields = []
            for col in table_data.columns[:3]:  # Show first 3 columns in summary
                if col in record and pd.notna(record[col]):
                    summary_fields.append(f"{col}: {record[col]}")
            
            summary = " | ".join(summary_fields) if summary_fields else f"Record {idx + 1}"
            
            with st.expander(f"Record {idx + 1}: {summary}"):
                # Display all record fields
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    for col in table_data.columns:
                        if col in record and pd.notna(record[col]):
                            st.write(f"**{col}:** {record[col]}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{table_name}_{idx}"):
                        edit_table_record(project_name, table_name, idx, record)
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{table_name}_{idx}"):
                        if delete_table_record(project_name, table_name, idx):
                            st.success("Record deleted successfully!")
                            st.rerun()
    
    except Exception as e:
        st.error(f"Error loading {table_name} records: {str(e)}")

def edit_table_record(project_name: str, table_name: str, record_idx: int, record_data):
    """Edit any table record (unified approach)"""
    st.subheader(f"✏️ Edit {table_name} Record")
    
    # Get table definition for field types
    all_tables = get_all_tables()
    table_def = all_tables[all_tables['table_name'] == table_name]
    
    if table_def.empty:
        st.error("❌ Table definition not found!")
        return
    
    # Parse fields from table definition
    try:
        import ast
        fields_str = table_def.iloc[0]['fields']
        fields = ast.literal_eval(fields_str)
        field_types = {field['name']: field['type'] for field in fields if field.get('name')}
    except:
        field_types = {}
    
    # Get additional fields from schema extensions
    schema_extensions = get_schema_extensions()
    if not schema_extensions.empty and 'table_type' in schema_extensions.columns:
        additional_fields = schema_extensions[schema_extensions['table_type'] == table_name]
        for _, field_row in additional_fields.iterrows():
            field_types[field_row['field_name']] = field_row['field_type']
    
    with st.form(f"edit_{table_name}_{record_idx}_form"):
        updated_data = {}
        
        col1, col2 = st.columns(2)
        field_count = 0
        
        for field_name, current_value in record_data.items():
            if pd.isna(current_value):
                current_value = ""
            
            field_type = field_types.get(field_name, "Text")
            col = col1 if field_count % 2 == 0 else col2
            
            with col:
                if field_type == "Date":
                    try:
                        if current_value:
                            default_date = pd.to_datetime(current_value).date()
                        else:
                            default_date = datetime.now().date()
                    except:
                        default_date = datetime.now().date()
                    
                    value = st.date_input(field_name, default_date)
                    updated_data[field_name] = value.strftime('%Y-%m-%d')
                    
                elif field_type == "Number":
                    try:
                        default_num = float(current_value) if current_value else 0.0
                    except:
                        default_num = 0.0
                    
                    value = st.number_input(field_name, value=default_num, step=0.1)
                    updated_data[field_name] = value
                    
                elif field_type == "True/False":
                    try:
                        default_bool = bool(current_value) if current_value else False
                    except:
                        default_bool = False
                    
                    value = st.checkbox(field_name, value=default_bool)
                    updated_data[field_name] = value
                    
                else:  # Text or other
                    value = st.text_input(field_name, value=str(current_value))
                    updated_data[field_name] = value
            
            field_count += 1
        
        if st.form_submit_button(f"💾 Update {table_name} Record"):
            if update_table_record(project_name, table_name, record_idx, updated_data):
                st.success("✅ Record updated successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to update record.")

def update_table_record(project_name: str, table_name: str, record_idx: int, updated_data: dict) -> bool:
    """Update any table record (unified approach)"""
    try:
        # Convert table name to file name
        file_name = table_name.lower().replace(' ', '_') + '.xlsx'
        file_path = f"local_data/projects/{project_name}/{file_name}"
        
        if not os.path.exists(file_path):
            return False
        
        df = pd.read_excel(file_path)
        
        if record_idx >= len(df):
            return False
        
        # Update the record
        for field_name, value in updated_data.items():
            if field_name in df.columns:
                df.iloc[record_idx, df.columns.get_loc(field_name)] = value
        
        df.to_excel(file_path, index=False)
        return True
        
    except Exception as e:
        st.error(f"Error updating record: {str(e)}")
        return False

def delete_table_record(project_name: str, table_name: str, record_idx: int) -> bool:
    """Delete any table record (unified approach)"""
    try:
        # Convert table name to file name
        file_name = table_name.lower().replace(' ', '_') + '.xlsx'
        file_path = f"local_data/projects/{project_name}/{file_name}"
        
        if not os.path.exists(file_path):
            return False
        
        df = pd.read_excel(file_path)
        
        if record_idx >= len(df):
            return False
        
        # Remove the record
        df = df.drop(record_idx).reset_index(drop=True)
        df.to_excel(file_path, index=False)
        return True
        
    except Exception as e:
        st.error(f"Error deleting record: {str(e)}")
        return False

def manage_custom_table_records(project_name: str, table_name: str):
    """Manage custom table records"""
    try:
        table_data = get_custom_table_data(project_name, table_name)
        
        if table_data.empty:
            st.info(f"No {table_name} records found for this project.")
            return
        
        st.subheader(f"📄 {table_name} Records")
        
        # Display records with edit/delete options
        for idx, record in table_data.iterrows():
            # Create a summary of the record for the expander
            summary_fields = []
            for col in table_data.columns[:3]:  # Show first 3 columns in summary
                if col in record and pd.notna(record[col]):
                    summary_fields.append(f"{col}: {record[col]}")
            
            summary = " | ".join(summary_fields) if summary_fields else f"Record {idx + 1}"
            
            with st.expander(f"Record {idx + 1}: {summary}"):
                # Display all record fields
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    for col in table_data.columns:
                        if col in record and pd.notna(record[col]):
                            st.write(f"**{col}:** {record[col]}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{table_name}_{idx}"):
                        edit_custom_table_record(project_name, table_name, idx, record)
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{table_name}_{idx}"):
                        if delete_custom_table_record(project_name, table_name, idx):
                            st.success("Record deleted successfully!")
                            st.rerun()
    
    except Exception as e:
        st.error(f"Error loading {table_name} records: {str(e)}")

def edit_custom_table_record(project_name: str, table_name: str, record_idx: int, record_data):
    """Edit a custom table record"""
    st.subheader(f"✏️ Edit {table_name} Record")
    
    # Get table definition for field types
    custom_tables = get_custom_tables()
    table_def = custom_tables[custom_tables['table_name'] == table_name]
    
    if table_def.empty:
        st.error("❌ Table definition not found!")
        return
    
    # Parse fields from table definition
    try:
        import ast
        fields_str = table_def.iloc[0]['fields']
        fields = ast.literal_eval(fields_str)
        field_types = {field['name']: field['type'] for field in fields if field.get('name')}
    except:
        field_types = {}
    
    # Get additional fields from schema extensions
    schema_extensions = get_schema_extensions()
    additional_fields = schema_extensions[schema_extensions['table_type'] == table_name]
    for _, field_row in additional_fields.iterrows():
        field_types[field_row['field_name']] = field_row['field_type']
    
    with st.form(f"edit_{table_name}_{record_idx}_form"):
        updated_data = {}
        
        col1, col2 = st.columns(2)
        field_count = 0
        
        for field_name, current_value in record_data.items():
            if pd.isna(current_value):
                current_value = ""
            
            field_type = field_types.get(field_name, "Text")
            col = col1 if field_count % 2 == 0 else col2
            
            with col:
                if field_type == "Date":
                    try:
                        if current_value:
                            default_date = pd.to_datetime(current_value).date()
                        else:
                            default_date = datetime.now().date()
                    except:
                        default_date = datetime.now().date()
                    
                    value = st.date_input(field_name, default_date)
                    updated_data[field_name] = value.strftime('%Y-%m-%d')
                    
                elif field_type == "Number":
                    try:
                        default_num = float(current_value) if current_value else 0.0
                    except:
                        default_num = 0.0
                    
                    value = st.number_input(field_name, value=default_num, step=0.1)
                    updated_data[field_name] = value
                    
                elif field_type == "True/False":
                    try:
                        default_bool = bool(current_value) if current_value else False
                    except:
                        default_bool = False
                    
                    value = st.checkbox(field_name, value=default_bool)
                    updated_data[field_name] = value
                    
                else:  # Text or other
                    value = st.text_input(field_name, value=str(current_value))
                    updated_data[field_name] = value
            
            field_count += 1
        
        if st.form_submit_button(f"💾 Update {table_name} Record"):
            if update_custom_table_record(project_name, table_name, record_idx, updated_data):
                st.success("✅ Record updated successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to update record.")

def update_custom_table_record(project_name: str, table_name: str, record_idx: int, updated_data: dict) -> bool:
    """Update a custom table record"""
    try:
        clean_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        file_path = f"local_data/projects/{project_name}/{clean_table_name}.xlsx"
        
        if not os.path.exists(file_path):
            return False
        
        df = pd.read_excel(file_path)
        
        if record_idx >= len(df):
            return False
        
        # Update the record
        for field_name, value in updated_data.items():
            if field_name in df.columns:
                df.iloc[record_idx, df.columns.get_loc(field_name)] = value
        
        df.to_excel(file_path, index=False)
        return True
        
    except Exception as e:
        st.error(f"Error updating record: {str(e)}")
        return False

def delete_custom_table_record(project_name: str, table_name: str, record_idx: int) -> bool:
    """Delete a custom table record"""
    try:
        clean_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        file_path = f"local_data/projects/{project_name}/{clean_table_name}.xlsx"
        
        if not os.path.exists(file_path):
            return False
        
        df = pd.read_excel(file_path)
        
        if record_idx >= len(df):
            return False
        
        # Remove the record
        df = df.drop(record_idx).reset_index(drop=True)
        df.to_excel(file_path, index=False)
        return True
        
    except Exception as e:
        st.error(f"Error deleting record: {str(e)}")
        return False

def edit_kml_record(project_name: str, record_idx: int, record_data):
    """Edit KML record"""
    st.subheader("Edit KML Record")
    
    with st.form(f"edit_kml_form_{record_idx}"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", value=pd.to_datetime(record_data['Date']).date())
            kml_count = st.number_input("KML Count", value=int(record_data['KML_Count_Sent']), min_value=1)
            total_area = st.number_input("Total Area", value=float(record_data['Total_Area']), min_value=0.0)
        
        with col2:
            area_approved = st.number_input("Area Approved", value=float(record_data['Area_Approved']), min_value=0.0)
            status = st.selectbox("Status", config.KML_STATUS, index=config.KML_STATUS.index(record_data['Status']))
            
        remarks = st.text_area("Remarks", value=record_data['Remarks'])
        
        if st.form_submit_button("💾 Update Record"):
            updated_data = {
                'Date': date.strftime('%Y-%m-%d'),
                'KML_Count_Sent': kml_count,
                'Total_Area': total_area,
                'Area_Approved': area_approved,
                'Status': status,
                'Remarks': remarks
            }
            if update_kml_record(project_name, record_idx, updated_data):
                st.success("Record updated successfully!")
                st.rerun()

def edit_plantation_record(project_name: str, record_idx: int, record_data):
    """Edit plantation record"""
    st.subheader("Edit Plantation Record")
    
    with st.form(f"edit_plantation_form_{record_idx}"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", value=pd.to_datetime(record_data['Date']).date())
            plot_code = st.text_input("Plot Code", value=record_data['Plot_Code'])
            area_planted = st.number_input("Area Planted", value=float(record_data['Area_Planted']), min_value=0.0)
            farmer_covered = st.number_input("Farmers Covered", value=int(record_data['Farmer_Covered']), min_value=1)
        
        with col2:
            trees_planted = st.number_input("Trees Planted", value=int(record_data['Trees_Planted']), min_value=0)
            pits_dug = st.number_input("Pits Dug", value=int(record_data['Pits_Dug']), min_value=0)
            status = st.selectbox("Status", ["Completed", "In Progress"], index=0 if record_data['Status'] == 'Completed' else 1)
        
        if st.form_submit_button("💾 Update Record"):
            updated_data = {
                'Date': date.strftime('%Y-%m-%d'),
                'Plot_Code': plot_code,
                'Area_Planted': area_planted,
                'Farmer_Covered': farmer_covered,
                'Trees_Planted': trees_planted,
                'Pits_Dug': pits_dug,
                'Status': status
            }
            if update_plantation_record(project_name, record_idx, updated_data):
                st.success("Record updated successfully!")
                st.rerun()

def update_kml_record(project_name: str, record_idx: int, updated_data: dict) -> bool:
    """Update KML record"""
    try:
        kml_data = data_manager.get_kml_data(project_name)
        for key, value in updated_data.items():
            kml_data.at[record_idx, key] = value
        
        file_path = f"local_data/projects/{project_name}_kml_data.xlsx"
        kml_data.to_excel(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error updating record: {str(e)}")
        return False

def update_plantation_record(project_name: str, record_idx: int, updated_data: dict) -> bool:
    """Update plantation record"""
    try:
        plantation_data = data_manager.get_plantation_data(project_name)
        for key, value in updated_data.items():
            plantation_data.at[record_idx, key] = value
        
        file_path = f"local_data/projects/{project_name}_plantation_data.xlsx"
        plantation_data.to_excel(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error updating record: {str(e)}")
        return False

def delete_kml_record(project_name: str, record_idx: int) -> bool:
    """Delete KML record"""
    try:
        kml_data = data_manager.get_kml_data(project_name)
        kml_data = kml_data.drop(record_idx).reset_index(drop=True)
        
        file_path = f"local_data/projects/{project_name}_kml_data.xlsx"
        kml_data.to_excel(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error deleting record: {str(e)}")
        return False

def delete_plantation_record(project_name: str, record_idx: int) -> bool:
    """Delete plantation record"""
    try:
        plantation_data = data_manager.get_plantation_data(project_name)
        plantation_data = plantation_data.drop(record_idx).reset_index(drop=True)
        
        file_path = f"local_data/projects/{project_name}_plantation_data.xlsx"
        plantation_data.to_excel(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error deleting record: {str(e)}")
        return False

def show_analytics():
    """Display analytics and charts page"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Analytics</h1>
        <p>Analyze plantation data with interactive charts and insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get available projects based on user role
    current_role = st.session_state.get('role', 'viewer')
    
    # Viewers can see all projects regardless of assignments
    if current_role == 'viewer':
        try:
            accessible_projects = data_manager.get_all_project_names()
        except:
            accessible_projects = ['MakeMyTrip', 'Absolute']
    else:
        # For admin and project_manager, use their assigned projects
        accessible_projects = get_user_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible for analytics.")
        return
    
    # Project selection
    selected_project = st.selectbox("Select Project for Analysis", accessible_projects)
    
    # Get data
    kml_data = data_manager.get_kml_data(selected_project)
    plantation_data = data_manager.get_plantation_data(selected_project)
    
    if kml_data.empty and plantation_data.empty:
        st.info("No data available for analysis. Please add some data first.")
        return
    
    # Analytics tabs
    tab1, tab2, tab3 = st.tabs(["📈 KML Analytics", "🌱 Plantation Analytics", "📊 Combined Insights"])
    
    with tab1:
        if not kml_data.empty:
            show_kml_analytics(kml_data, selected_project)
        else:
            st.info("No KML data available for analysis.")
    
    with tab2:
        if not plantation_data.empty:
            show_plantation_analytics(plantation_data, selected_project)
        else:
            st.info("No plantation data available for analysis.")
    
    with tab3:
        show_combined_analytics(kml_data, plantation_data, selected_project)

def show_kml_analytics(kml_data, project_name):
    """Show KML tracking analytics"""
    st.subheader(f"📄 KML Tracking Analytics - {project_name}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_files = kml_data['KML_Count_Sent'].sum() if 'KML_Count_Sent' in kml_data.columns else 0
        st.metric("Total KML Files", total_files)
    
    with col2:
        total_area = kml_data['Total_Area'].sum() if 'Total_Area' in kml_data.columns else 0
        st.metric("Total Area Submitted", f"{total_area:.1f} Ha")
    
    with col3:
        approved_area = kml_data['Area_Approved'].sum() if 'Area_Approved' in kml_data.columns else 0
        st.metric("Area Approved", f"{approved_area:.1f} Ha")
    
    with col4:
        approval_rate = (approved_area / total_area * 100) if total_area > 0 else 0
        st.metric("Approval Rate", f"{approval_rate:.1f}%")
    
    # Charts
    if 'Date' in kml_data.columns and 'Status' in kml_data.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
            status_counts = kml_data['Status'].value_counts()
            if not status_counts.empty:
                import plotly.express as px
                fig = px.pie(values=status_counts.values, names=status_counts.index, 
                           title="KML Status Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Monthly trends
            if len(kml_data) > 1:
                kml_data['Date'] = pd.to_datetime(kml_data['Date'], errors='coerce')
                kml_data['Month'] = kml_data['Date'].dt.to_period('M').astype(str)
                monthly_data = kml_data.groupby('Month')['Total_Area'].sum().reset_index()
                
                if not monthly_data.empty:
                    fig = px.line(monthly_data, x='Month', y='Total_Area', 
                                title="Monthly Area Submission Trend")
                    st.plotly_chart(fig, use_container_width=True)

def show_plantation_analytics(plantation_data, project_name):
    """Show plantation analytics"""
    st.subheader(f"🌱 Plantation Analytics - {project_name}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_area = plantation_data['Area_Planted'].sum() if 'Area_Planted' in plantation_data.columns else 0
        st.metric("Total Area Planted", f"{total_area:.1f} Ha")
    
    with col2:
        total_trees = plantation_data['Trees_Planted'].sum() if 'Trees_Planted' in plantation_data.columns else 0
        st.metric("Total Trees Planted", f"{total_trees:,}")
    
    with col3:
        total_farmers = plantation_data['Farmer_Covered'].sum() if 'Farmer_Covered' in plantation_data.columns else 0
        st.metric("Farmers Covered", total_farmers)
    
    with col4:
        trees_per_ha = total_trees / total_area if total_area > 0 else 0
        st.metric("Trees per Hectare", f"{trees_per_ha:.0f}")
    
    # Charts
    if len(plantation_data) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly planting trends
            if 'Date' in plantation_data.columns:
                plantation_data['Date'] = pd.to_datetime(plantation_data['Date'], errors='coerce')
                plantation_data['Month'] = plantation_data['Date'].dt.to_period('M').astype(str)
                monthly_planting = plantation_data.groupby('Month')['Area_Planted'].sum().reset_index()
                
                if not monthly_planting.empty:
                    import plotly.express as px
                    fig = px.bar(monthly_planting, x='Month', y='Area_Planted', 
                               title="Monthly Plantation Area")
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Plot status distribution
            if 'Status' in plantation_data.columns:
                status_counts = plantation_data['Status'].value_counts()
                if not status_counts.empty:
                    fig = px.pie(values=status_counts.values, names=status_counts.index, 
                               title="Plantation Status Distribution")
                    st.plotly_chart(fig, use_container_width=True)

def show_combined_analytics(kml_data, plantation_data, project_name):
    """Show combined analytics"""
    st.subheader(f"📊 Combined Project Insights - {project_name}")
    
    # Combined metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**KML vs Plantation Comparison**")
        
        kml_area = kml_data['Total_Area'].sum() if not kml_data.empty and 'Total_Area' in kml_data.columns else 0
        planted_area = plantation_data['Area_Planted'].sum() if not plantation_data.empty and 'Area_Planted' in plantation_data.columns else 0
        
        comparison_data = {
            'Category': ['Area Submitted (KML)', 'Area Planted'],
            'Area (Ha)': [kml_area, planted_area]
        }
        
        if kml_area > 0 or planted_area > 0:
            import plotly.express as px
            fig = px.bar(comparison_data, x='Category', y='Area (Ha)', 
                        title="KML Submission vs Actual Plantation")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Project Progress Summary**")
        
        # Calculate progress percentage
        progress_percentage = (planted_area / kml_area * 100) if kml_area > 0 else 0
        
        progress_data = []
        progress_data.append(['Total KML Area Submitted', f"{kml_area:.1f} Ha"])
        progress_data.append(['Total Area Planted', f"{planted_area:.1f} Ha"])
        progress_data.append(['Implementation Progress', f"{progress_percentage:.1f}%"])
        
        if not plantation_data.empty:
            total_trees = plantation_data['Trees_Planted'].sum() if 'Trees_Planted' in plantation_data.columns else 0
            total_farmers = plantation_data['Farmer_Covered'].sum() if 'Farmer_Covered' in plantation_data.columns else 0
            progress_data.append(['Total Trees Planted', f"{total_trees:,}"])
            progress_data.append(['Total Farmers Involved', total_farmers])
        
        progress_df = pd.DataFrame(progress_data, columns=['Metric', 'Value'])
        st.dataframe(progress_df, use_container_width=True)

def update_dynamic_forms():
    """Update dynamic forms cache"""
    # This function can be used to clear any cached form data
    pass

def show_manage_records():
    """Display manage records page"""
    # Check user role - only admin and project managers can manage records
    current_role = st.session_state.get('role', 'viewer')
    if current_role not in ['admin', 'project_manager']:
        st.error("⛔ Access denied. You do not have permission to manage records.")
        st.info("Please contact an administrator if you believe this is an error.")
        return
        
    st.markdown("""
    <div class="main-header">
        <h1>📋 Manage Records</h1>
        <p>View, edit, and delete existing records</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get user accessible projects
    user_projects = get_user_accessible_projects()
    
    if not user_projects:
        st.warning("No projects assigned to your account.")
        return
    
    # Get tables available for this project
    st.subheader("📁 Select Project")
    project_name = st.selectbox("Choose project:", user_projects)
    
    if not project_name:
        return
    
    # Get tables available for this project
    project_path = f"local_data/projects/{project_name}"
    available_tables = []
    
    if os.path.exists(project_path):
        for file_name in os.listdir(project_path):
            if file_name.endswith('.xlsx'):
                table_name = file_name.replace('.xlsx', '').replace('_', ' ').title()
                available_tables.append(table_name)
    
    if not available_tables:
        st.info(f"No tables found for project '{project_name}'.")
        return
    
    # Table selection
    st.subheader("📊 Select Table")
    table_name = st.selectbox("Choose table to manage:", available_tables)
    
    if not table_name:
        return
        
    # Manage records for the selected table
    st.subheader(f"📋 Manage {table_name} Records")
    
    # Load and display current records
    table_data = get_table_data(project_name, table_name)
    
    if table_data.empty:
        st.info(f"No records found in {table_name}.")
        return
    
    st.markdown(f"**Total Records:** {len(table_data)}")
    
    # Display records with action buttons
    for idx, row in table_data.iterrows():
        with st.expander(f"Record {idx + 1}: {row.iloc[0] if len(row) > 0 else 'N/A'}", expanded=False):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Display record data
                record_df = pd.DataFrame([row]).T
                record_df.columns = ['Value']
                # Convert all values to strings to prevent PyArrow serialization errors
                record_df['Value'] = record_df['Value'].astype(str)
                record_df.index.name = 'Field'
                st.dataframe(record_df, use_container_width=True)
            
            with col2:
                if st.button(f"✏️ Edit", key=f"edit_{table_name}_{idx}"):
                    st.session_state[f'editing_{table_name}_{idx}'] = True
                    st.rerun()
            
            with col3:
                if st.button(f"🗑️ Delete", key=f"delete_{table_name}_{idx}"):
                    if delete_table_record(project_name, table_name, idx):
                        st.success("Record deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete record.")
            
            # Edit form (if editing)
            if st.session_state.get(f'editing_{table_name}_{idx}', False):
                st.markdown("**Edit Record:**")
                
                # Get table schema for form generation
                edit_data = {}
                
                for col in table_data.columns:
                    current_value = row[col]
                    
                    # Generate appropriate input based on data type
                    if pd.api.types.is_numeric_dtype(table_data[col]):
                        edit_data[col] = st.number_input(f"{col}:", value=float(current_value) if pd.notna(current_value) else 0.0, key=f"edit_{col}_{idx}")
                    elif pd.api.types.is_datetime64_any_dtype(table_data[col]):
                        if pd.notna(current_value):
                            edit_data[col] = st.date_input(f"{col}:", value=pd.to_datetime(current_value).date(), key=f"edit_{col}_{idx}")
                        else:
                            edit_data[col] = st.date_input(f"{col}:", key=f"edit_{col}_{idx}")
                    elif pd.api.types.is_bool_dtype(table_data[col]):
                        edit_data[col] = st.checkbox(f"{col}:", value=bool(current_value) if pd.notna(current_value) else False, key=f"edit_{col}_{idx}")
                    else:
                        edit_data[col] = st.text_input(f"{col}:", value=str(current_value) if pd.notna(current_value) else "", key=f"edit_{col}_{idx}")
                
                col_save, col_cancel = st.columns(2)
                
                with col_save:
                    if st.button(f"💾 Save Changes", key=f"save_{table_name}_{idx}"):
                        if update_table_record(project_name, table_name, idx, edit_data):
                            st.success("Record updated successfully!")
                            st.session_state[f'editing_{table_name}_{idx}'] = False
                            st.rerun()
                        else:
                            st.error("Failed to update record.")
                
                with col_cancel:
                    if st.button(f"❌ Cancel", key=f"cancel_{table_name}_{idx}"):
                        st.session_state[f'editing_{table_name}_{idx}'] = False
                        st.rerun()

def show_my_projects():
    """Display detailed view of manager's assigned projects with complete tables"""
    st.markdown("""
    <div class="main-header">
        <h1>🏢 My Projects</h1>
        <p>Detailed view of all your assigned projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get user's accessible projects
    user_projects = get_user_accessible_projects()
    
    if not user_projects:
        st.warning("No projects assigned to your account. Please contact an administrator.")
        return
    
    # Project selection
    selected_project = st.selectbox("Select Project:", user_projects)
    
    if not selected_project:
        return
    
    # Display project details
    st.subheader(f"📊 Project: {selected_project}")
    
    # Create tabs for different data views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📝 KML Data", "🌱 Plantation Data", "📊 All Tables"])
    
    with tab1:
        # Show project overview/summary
        st.subheader("Project Summary")
        
        # Load KML and plantation data
        kml_data = data_manager.get_kml_data(selected_project)
        plantation_data = data_manager.get_plantation_data(selected_project)
        
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
        
        # Show combined analytics
        show_combined_analytics(kml_data, plantation_data, selected_project)
    
    with tab2:
        st.subheader("KML Tracking Data")
        if kml_data.empty:
            st.info("No KML tracking data available for this project.")
        else:
            # Show complete KML data table
            st.dataframe(kml_data, use_container_width=True)
    
    with tab3:
        st.subheader("Plantation Records")
        if plantation_data.empty:
            st.info("No plantation records available for this project.")
        else:
            # Show complete plantation data table
            st.dataframe(plantation_data, use_container_width=True)
    
    with tab4:
        st.subheader("All Project Tables")
        
        # Get all available tables for this project
        project_path = f"local_data/projects/{selected_project}"
        available_tables = []
        
        if os.path.exists(project_path):
            for file_name in os.listdir(project_path):
                if file_name.endswith('.xlsx'):
                    table_name = file_name.replace('.xlsx', '').replace('_', ' ').title()
                    available_tables.append((table_name, file_name))
        
        if not available_tables:
            st.info(f"No tables found for project '{selected_project}'.")
            return
        
        # Create selectbox for table selection
        table_options = [t[0] for t in available_tables]
        selected_table = st.selectbox("Select table to view:", table_options)
        
        if selected_table:
            # Find the corresponding file name
            file_name = next((f for t, f in available_tables if t == selected_table), None)
            
            if file_name:
                # Load and display the table data
                file_path = os.path.join(project_path, file_name)
                if os.path.exists(file_path):
                    table_data = pd.read_excel(file_path)
                    if table_data.empty:
                        st.info(f"No records in {selected_table}.")
                    else:
                        st.markdown(f"**Total Records:** {len(table_data)}")
                        st.dataframe(table_data, use_container_width=True)

def show_all_projects():
    """Display all projects for viewers with read-only access"""
    st.markdown("""
    <div class="main-header">
        <h1>🔍 All Projects</h1>
        <p>Browse all projects data (read-only)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all projects
    try:
        all_projects = data_manager.get_all_project_names()
    except:
        # Fallback to default projects if DataManager is not available
        all_projects = ['MakeMyTrip', 'Absolute']
    
    if not all_projects:
        st.warning("No projects available in the system.")
        return
    
    # Project selection
    selected_project = st.selectbox("Select Project:", all_projects)
    
    if not selected_project:
        return
    
    # Display project details (similar to show_my_projects but read-only)
    st.subheader(f"📊 Project: {selected_project}")
    
    # Create tabs for different data views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📝 KML Data", "🌱 Plantation Data", "📊 All Tables"])
    
    with tab1:
        # Show project overview/summary
        st.subheader("Project Summary")
        
        # Load KML and plantation data
        kml_data = data_manager.get_kml_data(selected_project)
        plantation_data = data_manager.get_plantation_data(selected_project)
        
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
        
        # Show combined analytics
        show_combined_analytics(kml_data, plantation_data, selected_project)
    
    with tab2:
        st.subheader("KML Tracking Data")
        if kml_data.empty:
            st.info("No KML tracking data available for this project.")
        else:
            # Show complete KML data table
            st.dataframe(kml_data, use_container_width=True)
    
    with tab3:
        st.subheader("Plantation Records")
        if plantation_data.empty:
            st.info("No plantation records available for this project.")
        else:
            # Show complete plantation data table
            st.dataframe(plantation_data, use_container_width=True)
    
    with tab4:
        st.subheader("All Project Tables")
        
        # Get all available tables for this project
        project_path = f"local_data/projects/{selected_project}"
        available_tables = []
        
        if os.path.exists(project_path):
            for file_name in os.listdir(project_path):
                if file_name.endswith('.xlsx'):
                    table_name = file_name.replace('.xlsx', '').replace('_', ' ').title()
                    available_tables.append((table_name, file_name))
        
        if not available_tables:
            st.info(f"No tables found for project '{selected_project}'.")
            return
        
        # Create selectbox for table selection
        table_options = [t[0] for t in available_tables]
        selected_table = st.selectbox("Select table to view:", table_options)
        
        if selected_table:
            # Find the corresponding file name
            file_name = next((f for t, f in available_tables if t == selected_table), None)
            
            if file_name:
                # Load and display the table data
                file_path = os.path.join(project_path, file_name)
                if os.path.exists(file_path):
                    table_data = pd.read_excel(file_path)
                    if table_data.empty:
                        st.info(f"No records in {selected_table}.")
                    else:
                        st.markdown(f"**Total Records:** {len(table_data)}")
                        st.dataframe(table_data, use_container_width=True)

if __name__ == "__main__":
    main()