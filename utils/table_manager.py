"""
Dynamic Table Manager for Plantation Data Management System
"""

import os
import pandas as pd
from datetime import datetime
import json
import streamlit as st
import ast
import time

class TableManager:
    """Dynamic Table Manager for handling table operations"""
    
    def __init__(self, db_manager):
        """Initialize with database manager"""
        self.db_manager = db_manager
        
        # Initialize tables cache
        if 'tables_cache' not in st.session_state:
            st.session_state['tables_cache'] = {}
    
    def get_all_tables(self):
        """Get all tables definitions"""
        try:
            # Try to get from cache first, but with timeout
            cache_key = 'all_tables'
            cache_timeout_key = 'tables_cache_time'
            current_time = time.time()
            
            # Check if cache is valid (less than 30 seconds old)
            if (cache_key in st.session_state['tables_cache'] and 
                cache_timeout_key in st.session_state['tables_cache'] and
                current_time - st.session_state['tables_cache'][cache_timeout_key] < 30):
                return st.session_state['tables_cache'][cache_key]
            
            # Get tables from database
            tables_df = self.db_manager.read_dataframe(None, 'tables')
            
            if tables_df.empty:
                # Create default tables structure if none exists
                tables_df = self._create_default_tables()
                
            # Store in cache with timestamp
            st.session_state['tables_cache'][cache_key] = tables_df
            st.session_state['tables_cache'][cache_timeout_key] = current_time
            return tables_df
            
        except Exception as e:
            print(f"Error getting tables: {str(e)}")
            return pd.DataFrame(columns=['table_name', 'description', 'fields', 'table_type', 'associated_projects'])
    
    def get_table_data(self, project_name, table_name):
        """Get data from any table"""
        try:
            # Convert table name to collection name format
            collection_name = table_name.lower().replace(' ', '_')
            
            # Get data from database
            return self.db_manager.read_dataframe(project_name, collection_name)
            
        except Exception as e:
            print(f"Error getting table data: {str(e)}")
            return pd.DataFrame()
    
    def get_project_tables(self, project_name):
        """Get available tables for a specific project"""
        try:
            tables_df = self.get_all_tables()
            if tables_df.empty:
                return []
            
            # Filter tables based on project associations
            project_tables = []
            for _, table in tables_df.iterrows():
                table_name = table['table_name']
                
                # Check if table has associated_projects column (for backward compatibility)
                if 'associated_projects' in table:
                    associated_projects_str = table['associated_projects']
                    try:
                        associated_projects = ast.literal_eval(associated_projects_str)
                    except:
                        associated_projects = ["All"]  # Default for system tables
                else:
                    # Backward compatibility - system tables are available to all projects
                    table_type = table.get('table_type', 'system')
                    if table_type == 'system':
                        associated_projects = ["All"]
                    else:
                        associated_projects = []
                
                # Include table if it's associated with this project or all projects
                if "All" in associated_projects or project_name in associated_projects:
                    project_tables.append(table_name)
            
            return project_tables
            
        except Exception as e:
            print(f"Error getting project tables: {str(e)}")
            return []
    
    def get_table_schema(self, table_name):
        """Get schema for a specific table"""
        try:
            tables_df = self.get_all_tables()
            if tables_df.empty:
                return []
            
            table_row = tables_df[tables_df['table_name'] == table_name]
            if table_row.empty:
                return []
            
            fields_str = table_row.iloc[0]['fields']
            if isinstance(fields_str, str):
                try:
                    return ast.literal_eval(fields_str)
                except:
                    return []
            
            return fields_str if isinstance(fields_str, list) else []
            
        except Exception as e:
            print(f"Error getting table schema: {str(e)}")
            return []
    
    def get_all_table_definitions(self):
        """Get all table definitions as a dictionary"""
        try:
            tables_df = self.get_all_tables()
            if tables_df.empty:
                return {}
            
            definitions = {}
            for _, row in tables_df.iterrows():
                table_name = row['table_name']
                fields_str = row['fields']
                
                if isinstance(fields_str, str):
                    try:
                        schema = ast.literal_eval(fields_str)
                    except:
                        schema = []
                else:
                    schema = fields_str if isinstance(fields_str, list) else []
                
                definitions[table_name] = schema
            
            return definitions
            
        except Exception as e:
            print(f"Error getting table definitions: {str(e)}")
            return {}
    
    def initialize_project_tables(self, project_name):
        """Initialize default tables for a project"""
        try:
            tables_df = self.get_all_tables()
            
            for _, table_row in tables_df.iterrows():
                table_name = table_row['table_name']
                collection_name = table_name.lower().replace(' ', '_')
                
                # Check if table already exists
                existing_data = self.db_manager.read_dataframe(project_name, collection_name)
                
                if existing_data.empty:
                    # Create empty table with schema columns
                    schema = self.get_table_schema(table_name)
                    columns = [field['name'] for field in schema if field.get('name')]
                    
                    if columns:
                        empty_df = pd.DataFrame(columns=columns)
                        self.db_manager.write_dataframe(project_name, collection_name, empty_df)
            
            return True
            
        except Exception as e:
            print(f"Error initializing project tables: {str(e)}")
            return False
    
    def add_record(self, project_name, table_name, record_data):
        """Add record to a table"""
        try:
            collection_name = table_name.lower().replace(' ', '_')
            
            # Get existing data
            existing_data = self.db_manager.read_dataframe(project_name, collection_name)
            
            # Create new record DataFrame
            new_record = pd.DataFrame([record_data])
            
            # Append to existing data
            if existing_data.empty:
                updated_data = new_record
            else:
                updated_data = pd.concat([existing_data, new_record], ignore_index=True)
            
            # Save back to database
            return self.db_manager.write_dataframe(project_name, collection_name, updated_data)
            
        except Exception as e:
            print(f"Error adding record: {str(e)}")
            return False
    
    def update_record(self, project_name, table_name, record_idx, updated_data):
        """Update a record in a table"""
        try:
            collection_name = table_name.lower().replace(' ', '_')
            
            # Get existing data
            existing_data = self.db_manager.read_dataframe(project_name, collection_name)
            
            if existing_data.empty or record_idx >= len(existing_data):
                return False
            
            # Update the record
            for field_name, value in updated_data.items():
                if field_name in existing_data.columns:
                    existing_data.iloc[record_idx, existing_data.columns.get_loc(field_name)] = value
            
            # Save back to database
            return self.db_manager.write_dataframe(project_name, collection_name, existing_data)
            
        except Exception as e:
            print(f"Error updating record: {str(e)}")
            return False
    
    def delete_record(self, project_name, table_name, record_idx):
        """Delete a record from a table"""
        try:
            collection_name = table_name.lower().replace(' ', '_')
            
            # Get existing data
            existing_data = self.db_manager.read_dataframe(project_name, collection_name)
            
            if existing_data.empty or record_idx >= len(existing_data):
                return False
            
            # Remove the record
            updated_data = existing_data.drop(record_idx).reset_index(drop=True)
            
            # Save back to database
            return self.db_manager.write_dataframe(project_name, collection_name, updated_data)
            
        except Exception as e:
            print(f"Error deleting record: {str(e)}")
            return False
    
    def update_table_data(self, project_name, table_name, updated_dataframe):
        """Update entire table data with new dataframe"""
        try:
            collection_name = table_name.lower().replace(' ', '_')
            
            # Save the updated dataframe
            return self.db_manager.write_dataframe(project_name, collection_name, updated_dataframe)
            
        except Exception as e:
            print(f"Error updating table data: {str(e)}")
            return False
    
    def create_table(self, table_name, description, fields, associated_projects=None):
        """Create a new table with optional project associations"""
        try:
            # Clear cache first to get fresh data
            self.clear_cache()
            tables_df = self.get_all_tables()
            
            # Check if table already exists
            if not tables_df.empty and table_name in tables_df['table_name'].values:
                return False
            
            # Default to all projects if none specified
            if associated_projects is None:
                associated_projects = ["All"]
            
            # Create new table record
            new_table = pd.DataFrame([{
                'table_name': table_name,
                'description': description,
                'fields': str(fields),
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'table_type': 'user-created',
                'associated_projects': str(associated_projects)  # Store as string list
            }])
            
            # Append to existing tables
            if tables_df.empty:
                updated_tables = new_table
            else:
                updated_tables = pd.concat([tables_df, new_table], ignore_index=True)
            
            # Save to database
            success = self.db_manager.write_dataframe(None, 'tables', updated_tables)
            
            if success:
                # Clear and update cache
                self.clear_cache()
                st.session_state['tables_cache']['all_tables'] = updated_tables
                
                # Initialize table for associated projects only
                projects_df = self.db_manager.read_dataframe(None, 'projects')
                if not projects_df.empty:
                    for _, project in projects_df.iterrows():
                        project_name = project['Project_Name']
                        
                        # Check if this project should have this table
                        if "All" in associated_projects or project_name in associated_projects:
                            collection_name = table_name.lower().replace(' ', '_')
                            columns = [field['name'] for field in fields if field.get('name')]
                            
                            if columns:
                                empty_df = pd.DataFrame(columns=columns)
                                self.db_manager.write_dataframe(project_name, collection_name, empty_df)
            
            return success
            
        except Exception as e:
            print(f"Error creating table: {str(e)}")
            return False
    
    def add_field_to_table(self, table_name, field_config):
        """Add a field to an existing table"""
        try:
            tables_df = self.get_all_tables()
            if tables_df.empty:
                return False
            
            # Find the table
            table_idx = tables_df[tables_df['table_name'] == table_name].index
            if len(table_idx) == 0:
                return False
            
            idx = table_idx[0]
            
            # Get current fields
            current_fields_str = tables_df.iloc[idx]['fields']
            try:
                current_fields = ast.literal_eval(current_fields_str)
            except:
                current_fields = []
            
            # Check if field already exists
            field_names = [f['name'] for f in current_fields if f.get('name')]
            if field_config['name'] in field_names:
                return False
            
            # Add new field
            current_fields.append(field_config)
            
            # Update table definition
            tables_df.iloc[idx, tables_df.columns.get_loc('fields')] = str(current_fields)
            
            # Save to database
            success = self.db_manager.write_dataframe(None, 'tables', tables_df)
            
            if success:
                # Update cache
                st.session_state['tables_cache']['all_tables'] = tables_df
                
                # Add field to all project data
                projects_df = self.db_manager.read_dataframe(None, 'projects')
                if not projects_df.empty:
                    collection_name = table_name.lower().replace(' ', '_')
                    default_value = field_config.get('default', '')
                    field_type = field_config.get('type', 'Text')
                    
                    for _, project in projects_df.iterrows():
                        project_name = project['Project_Name']
                        table_data = self.db_manager.read_dataframe(project_name, collection_name)
                        
                        if not table_data.empty and field_config['name'] not in table_data.columns:
                            # Set appropriate default value based on field type
                            if field_type == "Number":
                                table_data[field_config['name']] = float(default_value) if default_value else 0.0
                            elif field_type == "True/False":
                                table_data[field_config['name']] = default_value.lower() == 'true' if default_value else False
                            else:
                                table_data[field_config['name']] = default_value
                            
                            # Save updated data
                            self.db_manager.write_dataframe(project_name, collection_name, table_data)
            
            return success
            
        except Exception as e:
            print(f"Error adding field to table: {str(e)}")
            return False
    
    def edit_field_in_table(self, table_name, old_field_name, new_field_config):
        """Edit an existing field in a table"""
        try:
            tables_df = self.get_all_tables()
            if tables_df.empty:
                return False
            
            # Find the table
            table_idx = tables_df[tables_df['table_name'] == table_name].index
            if len(table_idx) == 0:
                return False
            
            idx = table_idx[0]
            
            # Get current fields
            current_fields_str = tables_df.iloc[idx]['fields']
            try:
                current_fields = ast.literal_eval(current_fields_str)
            except:
                current_fields = []
            
            # Find and update the field
            field_found = False
            for i, field in enumerate(current_fields):
                if field.get('name') == old_field_name:
                    current_fields[i] = new_field_config
                    field_found = True
                    break
            
            if not field_found:
                return False
            
            # Update table definition
            tables_df.iloc[idx, tables_df.columns.get_loc('fields')] = str(current_fields)
            
            # Save to database
            success = self.db_manager.write_dataframe(None, 'tables', tables_df)
            
            if success:
                # Update cache
                st.session_state['tables_cache']['all_tables'] = tables_df
                
                # Update field in all project data if field name changed
                if old_field_name != new_field_config['name']:
                    projects_df = self.db_manager.read_dataframe(None, 'projects')
                    if not projects_df.empty:
                        collection_name = table_name.lower().replace(' ', '_')
                        
                        for _, project in projects_df.iterrows():
                            project_name = project['Project_Name']
                            table_data = self.db_manager.read_dataframe(project_name, collection_name)
                            
                            if not table_data.empty and old_field_name in table_data.columns:
                                # Rename column
                                table_data = table_data.rename(columns={old_field_name: new_field_config['name']})
                                # Save updated data
                                self.db_manager.write_dataframe(project_name, collection_name, table_data)
            
            return success
            
        except Exception as e:
            print(f"Error editing field in table: {str(e)}")
            return False
    
    def delete_field_from_table(self, table_name, field_name):
        """Delete a field from a table"""
        try:
            tables_df = self.get_all_tables()
            if tables_df.empty:
                return False
            
            # Find the table
            table_idx = tables_df[tables_df['table_name'] == table_name].index
            if len(table_idx) == 0:
                return False
            
            idx = table_idx[0]
            
            # Get current fields
            current_fields_str = tables_df.iloc[idx]['fields']
            try:
                current_fields = ast.literal_eval(current_fields_str)
            except:
                current_fields = []
            
            # Remove the field
            updated_fields = [f for f in current_fields if f.get('name') != field_name]
            
            if len(updated_fields) == len(current_fields):
                # Field not found
                return False
            
            # Update table definition
            tables_df.iloc[idx, tables_df.columns.get_loc('fields')] = str(updated_fields)
            
            # Save to database
            success = self.db_manager.write_dataframe(None, 'tables', tables_df)
            
            if success:
                # Update cache
                st.session_state['tables_cache']['all_tables'] = tables_df
                
                # Remove field from all project data
                projects_df = self.db_manager.read_dataframe(None, 'projects')
                if not projects_df.empty:
                    collection_name = table_name.lower().replace(' ', '_')
                    
                    for _, project in projects_df.iterrows():
                        project_name = project['Project_Name']
                        table_data = self.db_manager.read_dataframe(project_name, collection_name)
                        
                        if not table_data.empty and field_name in table_data.columns:
                            # Drop column
                            table_data = table_data.drop(columns=[field_name])
                            # Save updated data
                            self.db_manager.write_dataframe(project_name, collection_name, table_data)
            
            return success
            
        except Exception as e:
            print(f"Error deleting field from table: {str(e)}")
            return False

    def clear_cache(self):
        """Clear tables cache"""
        if 'tables_cache' in st.session_state:
            st.session_state['tables_cache'] = {}
    
    def _create_default_tables(self):
        """Create default tables structure"""
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
        
        # Create DataFrame
        tables_df = pd.DataFrame(default_tables)
        
        # Save to database
        self.db_manager.write_dataframe(None, 'tables', tables_df)
        
        return tables_df 