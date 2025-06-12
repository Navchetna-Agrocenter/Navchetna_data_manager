"""
Google Sheets Manager for handling data operations using Google Sheets as storage
"""

import os
import json
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
import gspread
from datetime import datetime
import time
import config

class GoogleSheetsManager:
    def __init__(self):
        self.connected = False
        self.client = None
        self.sheets = {}
        self.connect()
        
    def connect(self):
        """Connect to Google Sheets API"""
        try:
            # Check if credentials are available as a Streamlit secret
            if hasattr(st.secrets, "gcp_service_account"):
                # Use Streamlit secrets
                credentials = service_account.Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"],
                    scopes=["https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive"]
                )
                self.client = gspread.authorize(credentials)
                self.connected = True
                st.session_state['deployment_mode'] = 'gsheets'
                return True
            
            # Check if credentials are stored as environment variables
            elif os.environ.get('GOOGLE_SHEETS_CREDS'):
                creds_json = json.loads(os.environ.get('GOOGLE_SHEETS_CREDS'))
                credentials = service_account.Credentials.from_service_account_info(
                    creds_json,
                    scopes=["https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive"]
                )
                self.client = gspread.authorize(credentials)
                self.connected = True
                st.session_state['deployment_mode'] = 'gsheets'
                return True
                
            # Check if credentials file exists
            elif os.path.exists('service_account.json'):
                credentials = service_account.Credentials.from_service_account_file(
                    'service_account.json',
                    scopes=["https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive"]
                )
                self.client = gspread.authorize(credentials)
                self.connected = True
                st.session_state['deployment_mode'] = 'gsheets'
                return True
                
            else:
                st.session_state['deployment_mode'] = 'local'
                return False
                
        except Exception as e:
            st.error(f"Failed to connect to Google Sheets: {str(e)}")
            st.session_state['deployment_mode'] = 'local'
            return False
            
    def get_or_create_spreadsheet(self, name):
        """Get existing spreadsheet or create a new one"""
        if not self.connected:
            return None
            
        try:
            # Cache spreadsheet objects to avoid repeated API calls
            if name in self.sheets:
                return self.sheets[name]
                
            # Try to open existing spreadsheet
            try:
                spreadsheet = self.client.open(name)
            except gspread.exceptions.SpreadsheetNotFound:
                # Create new spreadsheet if it doesn't exist
                spreadsheet = self.client.create(name)
                # Make it accessible to anyone with the link
                spreadsheet.share(None, perm_type='anyone', role='reader')
                
            self.sheets[name] = spreadsheet
            return spreadsheet
            
        except Exception as e:
            st.error(f"Error accessing spreadsheet '{name}': {str(e)}")
            return None
            
    def get_or_create_worksheet(self, spreadsheet, sheet_name):
        """Get existing worksheet or create a new one"""
        if not spreadsheet:
            return None
            
        try:
            # Try to get existing worksheet
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                # Create new worksheet if it doesn't exist
                worksheet = spreadsheet.add_worksheet(sheet_name, 1000, 100)
                
            return worksheet
            
        except Exception as e:
            st.error(f"Error accessing worksheet '{sheet_name}': {str(e)}")
            return None
    
    def read_dataframe(self, project_name, file_name):
        """Read data from Google Sheets as pandas DataFrame"""
        if not self.connected:
            return pd.DataFrame()
            
        try:
            # Determine spreadsheet and worksheet names
            if project_name:
                spreadsheet_name = f"Navchetna_Project_{project_name}"
                worksheet_name = file_name.replace('.xlsx', '')
            else:
                spreadsheet_name = "Navchetna_Master_Data"
                worksheet_name = file_name.replace('.xlsx', '')
                
            # Get spreadsheet and worksheet
            spreadsheet = self.get_or_create_spreadsheet(spreadsheet_name)
            if not spreadsheet:
                return pd.DataFrame()
                
            worksheet = self.get_or_create_worksheet(spreadsheet, worksheet_name)
            if not worksheet:
                return pd.DataFrame()
                
            # Get all data
            data = worksheet.get_all_records()
            
            # Return as DataFrame
            if data:
                return pd.DataFrame(data)
            else:
                # Return empty DataFrame with default structure
                return self._get_default_structure(file_name)
                
        except Exception as e:
            st.error(f"Error reading data from Google Sheets: {str(e)}")
            return pd.DataFrame()
    
    def write_dataframe(self, project_name, file_name, df):
        """Write pandas DataFrame to Google Sheets"""
        if not self.connected:
            return False
            
        try:
            # Determine spreadsheet and worksheet names
            if project_name:
                spreadsheet_name = f"Navchetna_Project_{project_name}"
                worksheet_name = file_name.replace('.xlsx', '')
            else:
                spreadsheet_name = "Navchetna_Master_Data"
                worksheet_name = file_name.replace('.xlsx', '')
                
            # Get spreadsheet and worksheet
            spreadsheet = self.get_or_create_spreadsheet(spreadsheet_name)
            if not spreadsheet:
                return False
                
            worksheet = self.get_or_create_worksheet(spreadsheet, worksheet_name)
            if not worksheet:
                return False
                
            # Convert DataFrame to list of lists
            data = [df.columns.tolist()] + df.values.tolist()
            
            # Clear existing data and update with new data
            worksheet.clear()
            if data and len(data) > 0:
                # Update cells with data
                worksheet.update(data)
            
            return True
            
        except Exception as e:
            st.error(f"Error writing data to Google Sheets: {str(e)}")
            return False
    
    def _get_default_structure(self, file_name):
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
        elif 'custom_tables' in file_name:
            return pd.DataFrame(columns=[
                'table_name', 'description', 'fields', 'created_date', 'table_type'
            ])
        else:
            return pd.DataFrame()
    
    def get_project_list(self):
        """Get list of all projects"""
        # Try to read from Google Sheets
        projects_df = self.read_dataframe(None, config.FILE_NAMING['projects'])
        if not projects_df.empty and 'Project_Name' in projects_df.columns:
            return projects_df['Project_Name'].tolist()
        else:
            return config.PROJECTS  # Fallback to default projects
            
    def create_project(self, project_data):
        """Create a new project in Google Sheets"""
        try:
            # Read existing projects
            projects_df = self.read_dataframe(None, config.FILE_NAMING['projects'])
            
            # Check if project already exists
            if not projects_df.empty and 'Project_Name' in projects_df.columns:
                if project_data['Project_Name'] in projects_df['Project_Name'].values:
                    st.error(f"Project {project_data['Project_Name']} already exists!")
                    return False
            
            # Add new project
            new_project = pd.DataFrame([project_data])
            projects_df = pd.concat([projects_df, new_project], ignore_index=True)
            
            # Save updated projects list
            success = self.write_dataframe(None, config.FILE_NAMING['projects'], projects_df)
            
            if success:
                # Initialize project files
                self._initialize_project_files(project_data['Project_Name'])
                return True
            else:
                return False
                
        except Exception as e:
            st.error(f"Error creating project: {str(e)}")
            return False
            
    def _initialize_project_files(self, project_name):
        """Initialize empty files for a new project"""
        # Create empty files with default structure
        for file_name in [config.FILE_NAMING['kml_tracking'], config.FILE_NAMING['plantation_records']]:
            df = self._get_default_structure(file_name)
            self.write_dataframe(project_name, file_name, df) 