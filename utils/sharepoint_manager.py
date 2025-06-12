"""
SharePoint Manager for handling file operations and authentication
"""

import os
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import streamlit as st
from typing import Dict, List, Optional, Tuple
import config

# SharePoint dependencies - only import if available
try:
    import msal
    from office365.runtime.auth.authentication_context import AuthenticationContext
    from office365.sharepoint.client_context import ClientContext
    from office365.sharepoint.files.file import File
    SHAREPOINT_AVAILABLE = True
except ImportError:
    SHAREPOINT_AVAILABLE = False

# Google Sheets manager
try:
    from utils.gsheets_manager import GoogleSheetsManager
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False

class SharePointManager:
    def __init__(self):
        self.config = config.SHAREPOINT_CONFIG
        self.local_config = config.LOCAL_STORAGE
        self.is_online = False
        self.context = None
        self.access_token = None
        self.gsheets_manager = None
        
        # Initialize Google Sheets manager if available
        if GSHEETS_AVAILABLE:
            self.gsheets_manager = GoogleSheetsManager()
            
        self._ensure_local_folders()
        
    def _ensure_local_folders(self):
        """Create local folders if they don't exist"""
        folders = [
            self.local_config['data_folder'],
            self.local_config['projects_folder'],
            self.local_config['master_data_folder'],
            self.local_config['reports_folder']
        ]
        
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
    
    def authenticate(self) -> bool:
        """
        Authenticate with SharePoint using MSAL
        Returns True if successful, False otherwise
        """
        try:
            # First try Google Sheets authentication if available
            if GSHEETS_AVAILABLE and self.gsheets_manager and self.gsheets_manager.connected:
                st.session_state['deployment_mode'] = 'gsheets'
                return True
            
            # Check if SharePoint dependencies are available
            if not SHAREPOINT_AVAILABLE:
                self.is_online = False
                # Check if we're running on Streamlit Cloud (GitHub deployment)
                if os.environ.get('STREAMLIT_SHARING', '') == 'true' or os.environ.get('IS_GITHUB_PAGES', ''):
                    st.session_state['deployment_mode'] = 'github'
                else:
                    st.session_state['deployment_mode'] = 'local'
                return True
            
            # Simulated authentication for development
            self.is_online = False  # Set to True when SharePoint is configured
            
            if not self.is_online:
                return True
                
            # Actual SharePoint authentication code would go here
            if SHAREPOINT_AVAILABLE:
                app = msal.ConfidentialClientApplication(
                    self.config['client_id'],
                    authority=self.config['authority'],
                    client_credential=self.config['client_secret']
                )
                
                result = app.acquire_token_silent(
                    scopes=self.config['scope'],
                    account=None
                )
                
                if not result:
                    result = app.acquire_token_for_client(scopes=self.config['scope'])
                
                if "access_token" in result:
                    self.access_token = result['access_token']
                    self.is_online = True
                    return True
                else:
                    st.error(f"Authentication failed: {result.get('error_description', 'Unknown error')}")
                    return False
            else:
                return True
                
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return False
    
    def read_excel_file(self, project_name: str, file_name: str) -> pd.DataFrame:
        """
        Read Excel file from SharePoint, Google Sheets, or local storage
        """
        try:
            # First try Google Sheets if available and connected
            if st.session_state.get('deployment_mode') == 'gsheets' and self.gsheets_manager:
                return self.gsheets_manager.read_dataframe(project_name, file_name)
                
            # Otherwise try SharePoint or local storage
            if self.is_online and SHAREPOINT_AVAILABLE:
                # SharePoint file reading logic
                return self._read_from_sharepoint(project_name, file_name)
            else:
                # Check if we're running on GitHub deployment
                if st.session_state.get('deployment_mode') == 'github':
                    return self._get_default_structure(file_name)
                else:
                    # Local file reading
                    return self._read_from_local(project_name, file_name)
                
        except Exception as e:
            st.error(f"Error reading file {file_name}: {str(e)}")
            return pd.DataFrame()
    
    def write_excel_file(self, project_name: str, file_name: str, data: pd.DataFrame, sheet_name: str = 'Sheet1') -> bool:
        """
        Write Excel file to SharePoint, Google Sheets, or local storage
        """
        try:
            # First try Google Sheets if available and connected
            if st.session_state.get('deployment_mode') == 'gsheets' and self.gsheets_manager:
                success = self.gsheets_manager.write_dataframe(project_name, file_name, data)
                if success:
                    st.success(f"✅ Data saved successfully to Google Sheets")
                return success
                
            # Otherwise try SharePoint or local storage
            if self.is_online and SHAREPOINT_AVAILABLE:
                # SharePoint file writing logic
                success = self._write_to_sharepoint(project_name, file_name, data, sheet_name)
            else:
                # Check if we're running on GitHub deployment
                if st.session_state.get('deployment_mode') == 'github':
                    # Store in session state for GitHub deployment
                    self._store_in_session_state(project_name, file_name, data)
                    success = True
                else:
                    # Local file writing
                    success = self._write_to_local(project_name, file_name, data, sheet_name)
            
            if success:
                st.success(f"✅ Data saved successfully to {file_name}")
            return success
            
        except Exception as e:
            st.error(f"Error writing file {file_name}: {str(e)}")
            return False
    
    def _store_in_session_state(self, project_name: str, file_name: str, data: pd.DataFrame):
        """Store DataFrame in session state when running on GitHub deployment"""
        # Create a unique key for this file
        if project_name:
            key = f"data_{project_name}_{file_name.replace('.xlsx', '')}"
        else:
            key = f"data_master_{file_name.replace('.xlsx', '')}"
        
        # Store the DataFrame in session state
        st.session_state[key] = data
    
    def _read_from_local(self, project_name: str, file_name: str) -> pd.DataFrame:
        """Read from local storage"""
        # First check if data is in session state (for GitHub deployment)
        if project_name:
            session_key = f"data_{project_name}_{file_name.replace('.xlsx', '')}"
        else:
            session_key = f"data_master_{file_name.replace('.xlsx', '')}"
            
        if session_key in st.session_state:
            return st.session_state[session_key]
            
        # Otherwise try to read from file
        if project_name:
            file_path = os.path.join(self.local_config['projects_folder'], project_name, file_name)
        else:
            file_path = os.path.join(self.local_config['master_data_folder'], file_name)
        
        if os.path.exists(file_path):
            return pd.read_excel(file_path)
        else:
            # Return empty DataFrame with default structure based on file type
            return self._get_default_structure(file_name)
    
    def _write_to_local(self, project_name: str, file_name: str, data: pd.DataFrame, sheet_name: str = 'Sheet1') -> bool:
        """Write to local storage"""
        try:
            # Also store in session state for persistence during the session
            if project_name:
                session_key = f"data_{project_name}_{file_name.replace('.xlsx', '')}"
            else:
                session_key = f"data_master_{file_name.replace('.xlsx', '')}"
                
            st.session_state[session_key] = data.copy()
            
            if project_name:
                folder_path = os.path.join(self.local_config['projects_folder'], project_name)
                os.makedirs(folder_path, exist_ok=True)
                file_path = os.path.join(folder_path, file_name)
            else:
                file_path = os.path.join(self.local_config['master_data_folder'], file_name)
            
            # Read existing file to preserve multiple sheets
            if os.path.exists(file_path):
                with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return True
        except Exception as e:
            st.error(f"Local write error: {str(e)}")
            return False
    
    def _read_from_sharepoint(self, project_name: str, file_name: str) -> pd.DataFrame:
        """Read from SharePoint (placeholder for actual implementation)"""
        # This would contain actual SharePoint REST API calls
        # For now, fallback to local storage
        return self._read_from_local(project_name, file_name)
    
    def _write_to_sharepoint(self, project_name: str, file_name: str, data: pd.DataFrame, sheet_name: str = 'Sheet1') -> bool:
        """Write to SharePoint (placeholder for actual implementation)"""
        # This would contain actual SharePoint REST API calls
        # For now, write to local storage
        return self._write_to_local(project_name, file_name, data, sheet_name)
    
    def _get_default_structure(self, file_name: str) -> pd.DataFrame:
        """Return default DataFrame structure based on file type"""
        if 'kml_tracking' in file_name:
            return pd.DataFrame(columns=[
                'Date', 'User', 'KML_Count_Sent', 'Total_Area', 
                'Area_Approved', 'Approval_Date', 'Status', 'Remarks'
            ])
        elif 'plantation_records' in file_name:
            return pd.DataFrame(columns=[
                'Date', 'User', 'Plot_Code', 'Area_Planted', 
                'Farmer_Covered', 'Trees_Planted', 'Pits_Dug', 'Status'
            ])
        elif 'daily_data' in file_name:
            return pd.DataFrame(columns=[
                'Date', 'User', 'Activity_Type', 'Value', 'Unit', 'Remarks'
            ])
        elif 'projects' in file_name:
            return pd.DataFrame(columns=[
                'Project_ID', 'Project_Name', 'Description', 'Start_Date', 
                'Target_Area', 'Assigned_Users', 'Status', 'Manager'
            ])
        elif 'users' in file_name:
            return pd.DataFrame(columns=[
                'Username', 'Password_Hash', 'Role', 'Full_Name', 
                'Email', 'Accessible_Projects', 'Last_Login'
            ])
        else:
            return pd.DataFrame()
            
    def get_project_list(self) -> List[str]:
        """Get list of all projects"""
        # Try Google Sheets first
        if st.session_state.get('deployment_mode') == 'gsheets' and self.gsheets_manager:
            return self.gsheets_manager.get_project_list()
            
        # First check session state for GitHub deployment
        session_key = f"data_master_projects"
        if session_key in st.session_state:
            df = st.session_state[session_key]
            if not df.empty and 'Project_Name' in df.columns:
                return df['Project_Name'].tolist()
        
        # Try to read from file
        try:
            projects_df = self.read_excel_file(None, config.FILE_NAMING['projects'])
            if not projects_df.empty and 'Project_Name' in projects_df.columns:
                return projects_df['Project_Name'].tolist()
            else:
                return config.PROJECTS  # Fallback to default projects
        except Exception:
            return config.PROJECTS
    
    def create_project(self, project_data: Dict) -> bool:
        """Create a new project"""
        # Try Google Sheets first
        if st.session_state.get('deployment_mode') == 'gsheets' and self.gsheets_manager:
            return self.gsheets_manager.create_project(project_data)
            
        try:
            projects_df = self.read_excel_file(None, config.FILE_NAMING['projects'])
            
            # Check if project already exists
            if not projects_df.empty and 'Project_Name' in projects_df.columns:
                if project_data['Project_Name'] in projects_df['Project_Name'].values:
                    st.error(f"Project {project_data['Project_Name']} already exists!")
                    return False
            
            # Add new project
            new_project = pd.DataFrame([project_data])
            projects_df = pd.concat([projects_df, new_project], ignore_index=True)
            
            # Save updated projects list
            success = self.write_excel_file(None, config.FILE_NAMING['projects'], projects_df)
            
            if success:
                # Initialize project files
                self._initialize_project_files(project_data['Project_Name'])
                return True
            else:
                return False
                
        except Exception as e:
            st.error(f"Error creating project: {str(e)}")
            return False
    
    def _initialize_project_files(self, project_name: str):
        """Initialize empty files for a new project"""
        # Create empty files with default structure
        for file_name in [config.FILE_NAMING['kml_tracking'], config.FILE_NAMING['plantation_records']]:
            df = self._get_default_structure(file_name)
            self.write_excel_file(project_name, file_name, df)
    
    def sync_data(self) -> bool:
        """Sync data between local storage and SharePoint"""
        # Only relevant for actual SharePoint integration
        if self.is_online and SHAREPOINT_AVAILABLE:
            # Placeholder for actual SharePoint sync logic
            return True
        else:
            # For GitHub deployment, data is already in session state
            return True
    
    def hash_password(self, password: str) -> str:
        """Simple password hashing for demo purposes"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() 