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
                # Initialize custom tables data structure
                self.initialize_custom_tables()
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
                # Initialize custom tables data structure
                self.initialize_custom_tables()
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
                # Initialize custom tables data structure
                self.initialize_custom_tables()
                return True
                
            else:
                st.session_state['deployment_mode'] = 'local'
                return False
                
        except Exception as e:
            st.error(f"Failed to connect to Google Sheets: {str(e)}")
            st.session_state['deployment_mode'] = 'local'
            return False
            
    def initialize_custom_tables(self):
        """Initialize custom tables data structure if it doesn't exist"""
        try:
            # Check if custom tables data exists
            custom_tables_df = self.read_dataframe(None, 'custom_tables.xlsx')
            if custom_tables_df.empty:
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
                        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
                        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'table_type': 'system'
                    }
                ]
                
                # Create DataFrame and store
                custom_tables_df = pd.DataFrame(default_tables)
                self.write_dataframe(None, 'custom_tables.xlsx', custom_tables_df)
                
                # Store in session state for immediate access
                st.session_state['data_master_custom_tables'] = custom_tables_df
                
            # Check if schema extensions data exists
            schema_extensions_df = self.read_dataframe(None, 'schema_extensions.xlsx')
            if schema_extensions_df.empty:
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
                
                # Create DataFrame and store
                schema_extensions_df = pd.DataFrame(default_extensions)
                self.write_dataframe(None, 'schema_extensions.xlsx', schema_extensions_df)
                
                # Store in session state for immediate access
                st.session_state['data_master_schema_extensions'] = schema_extensions_df
                
        except Exception as e:
            st.error(f"Error initializing custom tables: {str(e)}")
            
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
        elif 'users' in file_name:
            return pd.DataFrame(columns=[
                'username', 'password_hash', 'role', 'accessible_projects',
                'full_name', 'email', 'created_date', 'last_login'
            ])
        elif 'projects' in file_name:
            return pd.DataFrame(columns=[
                'project_name', 'description', 'client', 'manager',
                'start_date', 'target_area', 'target_trees', 'status'
            ])
        elif 'custom_tables' in file_name:
            return pd.DataFrame(columns=[
                'table_name', 'description', 'fields', 'created_date', 'table_type'
            ])
        elif 'schema_extensions' in file_name:
            return pd.DataFrame(columns=[
                'table_type', 'field_name', 'field_type', 'default_value', 
                'is_required', 'dropdown_options', 'description'
            ])
        else:
            # For custom tables, return empty DataFrame
            return pd.DataFrame()
    
    def get_project_list(self):
        """Get list of projects"""
        try:
            projects_df = self.read_dataframe(None, 'projects.xlsx')
            if not projects_df.empty:
                return projects_df['project_name'].tolist()
            return ['MakeMyTrip', 'Absolute']  # Default projects
        except Exception:
            return ['MakeMyTrip', 'Absolute']  # Default projects
    
    def create_project(self, project_data):
        """Create a new project"""
        try:
            projects_df = self.read_dataframe(None, 'projects.xlsx')
            
            # Check if project already exists
            if not projects_df.empty and project_data['project_name'] in projects_df['project_name'].values:
                return False
            
            # Create new project record
            new_project = pd.DataFrame([{
                'project_name': project_data['project_name'],
                'description': project_data.get('description', ''),
                'client': project_data.get('client', ''),
                'manager': project_data.get('manager', ''),
                'start_date': project_data.get('start_date', datetime.now().strftime('%Y-%m-%d')),
                'target_area': project_data.get('target_area', 0),
                'target_trees': project_data.get('target_trees', 0),
                'status': 'Active'
            }])
            
            # Append to existing projects
            if projects_df.empty:
                updated_projects = new_project
            else:
                updated_projects = pd.concat([projects_df, new_project], ignore_index=True)
            
            # Save updated projects
            success = self.write_dataframe(None, 'projects.xlsx', updated_projects)
            
            if success:
                # Initialize project files
                self._initialize_project_files(project_data['project_name'])
            
            return success
        
        except Exception as e:
            st.error(f"Error creating project: {str(e)}")
            return False
    
    def _initialize_project_files(self, project_name):
        """Initialize required files for a new project"""
        try:
            # Create KML tracking file
            self.write_dataframe(project_name, 'kml_tracking.xlsx', pd.DataFrame())
            
            # Create plantation records file
            self.write_dataframe(project_name, 'plantation_records.xlsx', pd.DataFrame())
            
            # Get custom tables and create files for them
            custom_tables = self.read_dataframe(None, 'custom_tables.xlsx')
            if not custom_tables.empty:
                for _, row in custom_tables.iterrows():
                    table_name = row['table_name'].lower().replace(' ', '_').replace('-', '_')
                    self.write_dataframe(project_name, f"{table_name}.xlsx", pd.DataFrame())
                    
        except Exception as e:
            st.error(f"Error initializing project files: {str(e)}") 