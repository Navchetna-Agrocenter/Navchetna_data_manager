# Configuration settings for Plantation Data Management App

# SharePoint Configuration
SHAREPOINT_CONFIG = {
    'site_url': 'https://yourcompany.sharepoint.com/sites/PlantationData',
    'client_id': 'your-client-id',  # Azure App Registration Client ID
    'client_secret': 'your-client-secret',  # Azure App Registration Secret
    'tenant_id': 'your-tenant-id',  # Azure Tenant ID
    'authority': 'https://login.microsoftonline.com/your-tenant-id',
    'scope': ['https://graph.microsoft.com/.default']
}

# MongoDB Configuration
MONGODB_CONFIG = {
    'connection_string': '',  # Set via environment variable MONGODB_URI
    'database_name': 'navchetna_data',
    'use_local_fallback': True,  # Fall back to local storage if MongoDB is unavailable
}

# Local Storage Configuration (for development/offline mode)
LOCAL_STORAGE = {
    'data_folder': 'local_data',
    'projects_folder': 'local_data/projects',
    'master_data_folder': 'local_data/master_data',
    'reports_folder': 'local_data/reports'
}

# App Configuration
APP_CONFIG = {
    'app_title': 'Plantation Data Management System',
    'company_name': 'Navchetna Spatial Solutions',
    'page_title': 'Plantation Analytics Dashboard',
    'page_icon': '🌱',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# User Roles
USER_ROLES = {
    'admin': 'Administrator',
    'project_manager': 'Project Manager',
    'viewer': 'Viewer'
}

# Project Status Options
PROJECT_STATUS = [
    'Active',
    'Planning',
    'On Hold',
    'Completed',
    'Cancelled'
]

# KML Status Options
KML_STATUS = [
    'Pending',
    'Approved',
    'Rejected',
    'Under Review'
]

# Chart Colors
CHART_COLORS = {
    'primary': '#2E8B57',      # Sea Green
    'secondary': '#90EE90',    # Light Green
    'accent': '#32CD32',       # Lime Green
    'warning': '#FFD700',      # Gold
    'danger': '#DC143C',       # Crimson
    'info': '#4682B4',         # Steel Blue
    'dark': '#2F4F4F',         # Dark Slate Gray
    'light': '#F0F8FF'         # Alice Blue
}

# Default Projects (for initial setup)
DEFAULT_PROJECTS = [
    {
        'name': 'MakeMyTrip',
        'description': 'Plantation project for MakeMyTrip sustainability initiative',
        'target_area': 1000,
        'start_date': '2024-01-01',
        'status': 'Active'
    },
    {
        'name': 'Absolute',
        'description': 'Absolute company plantation and carbon offset project',
        'target_area': 750,
        'start_date': '2024-02-01',
        'status': 'Active'
    }
]

# Project list for backward compatibility
PROJECTS = ['MakeMyTrip', 'Absolute']

# File Naming Conventions
FILE_NAMING = {
    'daily_data': 'daily_data.xlsx',
    'kml_tracking': 'kml_tracking.xlsx',
    'plantation_records': 'plantation_records.xlsx',
    'users': 'users.xlsx',
    'projects': 'projects.xlsx',
    'configuration': 'configuration.xlsx'
}

# Collection Names for MongoDB
COLLECTION_NAMES = {
    'daily_data': 'daily_data',
    'kml_tracking': 'kml_tracking',
    'plantation_records': 'plantation_records',
    'users': 'users',
    'projects': 'projects',
    'configuration': 'configuration',
    'tables': 'tables',  # Stores table definitions
    'schema_extensions': 'schema_extensions'  # Stores schema extensions
} 