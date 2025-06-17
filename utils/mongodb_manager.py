"""
MongoDB Manager for Plantation Data Management System
Handles all database operations with MongoDB
"""

import os
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import streamlit as st
import json
import hashlib
import time

class MongoDBManager:
    """MongoDB Manager for handling database operations"""
    
    def __init__(self, connection_string=None):
        """Initialize MongoDB connection"""
        # Try to get connection string from multiple sources
        self.connection_string = connection_string
        
        if not self.connection_string:
            # Try Streamlit secrets first (for deployment)
            try:
                if hasattr(st, 'secrets') and 'mongodb' in st.secrets:
                    self.connection_string = st.secrets.mongodb.connection_string
                    print("Using MongoDB connection from Streamlit secrets")
            except:
                pass
        
        if not self.connection_string:
            # Try environment variable
            self.connection_string = os.environ.get("MONGODB_URI")
            if self.connection_string:
                print("Using MongoDB connection from environment variable")
        
        self.client = None
        self.db = None
        self.is_online = False
        
        # Try to connect to MongoDB
        try:
            if self.connection_string:
                self.client = MongoClient(self.connection_string)
                # Get database name from secrets or use default
                db_name = "navchetna_data"
                try:
                    if hasattr(st, 'secrets') and 'mongodb' in st.secrets:
                        db_name = st.secrets.mongodb.get('database_name', 'navchetna_data')
                except:
                    pass
                
                self.db = self.client[db_name]
                # Test the connection
                self.client.admin.command('ping')
                self.is_online = True
                print(f"Connected to MongoDB successfully - Database: {db_name}")
            else:
                # Use local MongoDB if no connection string is provided
                self.client = MongoClient('localhost', 27017)
                self.db = self.client.navchetna_data
                # Test the connection
                self.client.admin.command('ping')
                self.is_online = True
                print("Connected to local MongoDB successfully")
        except Exception as e:
            print(f"MongoDB connection error: {str(e)}")
            self.is_online = False
            # Create fallback to local file system
            os.makedirs("local_data", exist_ok=True)
            os.makedirs("local_data/projects", exist_ok=True)
            print("Using local file system as fallback")
    
    def authenticate(self):
        """Authentication placeholder for compatibility"""
        # No authentication needed for MongoDB in this implementation
        # This is kept for compatibility with existing code
        return self.is_online
    
    def get_collection(self, project_name, collection_name):
        """Get MongoDB collection for a specific project and collection name"""
        if not self.is_online or self.db is None:
            return None
            
        # Format collection name to be valid for MongoDB
        formatted_name = f"{project_name}_{collection_name}" if project_name else collection_name
        formatted_name = formatted_name.replace(' ', '_').lower()
        
        return self.db[formatted_name]
    
    def read_dataframe(self, project_name, collection_name):
        """Read data from MongoDB and return as DataFrame"""
        try:
            if self.is_online and self.db is not None:
                collection = self.get_collection(project_name, collection_name)
                if collection is not None:
                    # Get all documents from collection
                    cursor = collection.find({}, {'_id': 0})  # Exclude MongoDB _id field
                    data = list(cursor)
                    
                    if data:
                        return pd.DataFrame(data)
                    else:
                        return pd.DataFrame()  # Empty DataFrame if no data
            
            # Fallback to local file
            file_path = self._get_local_file_path(project_name, collection_name)
            if os.path.exists(file_path):
                return pd.read_excel(file_path)
            else:
                return pd.DataFrame()  # Return empty DataFrame if file doesn't exist
                
        except Exception as e:
            print(f"Error reading data: {str(e)}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
    def write_dataframe(self, project_name, collection_name, df):
        """Write DataFrame to MongoDB"""
        try:
            # Clean DataFrame to prevent data type issues
            df_clean = self._clean_dataframe_for_storage(df.copy())
            
            if self.is_online and self.db is not None:
                collection = self.get_collection(project_name, collection_name)
                if collection is not None and not df_clean.empty:
                    # Convert DataFrame to list of dictionaries
                    records = df_clean.to_dict('records')
                    
                    # Delete all existing documents in the collection
                    collection.delete_many({})
                    
                    # Insert new documents
                    if records:
                        collection.insert_many(records)
                    
                    print(f"Data written to MongoDB: {project_name}_{collection_name}")
                    
            # Always save to local file as backup
            self._save_to_local_file(project_name, collection_name, df_clean)
            
            return True
        except Exception as e:
            print(f"Error writing data: {str(e)}")
            # Try to save to local file as fallback
            self._save_to_local_file(project_name, collection_name, df)
            return False
    
    def read_excel_file(self, project_name, file_name):
        """Read Excel file data (compatibility method)"""
        # Convert file_name to collection_name format
        collection_name = file_name.replace('.xlsx', '').replace('.xls', '')
        return self.read_dataframe(project_name, collection_name)
    
    def write_excel_file(self, project_name, file_name, df):
        """Write Excel file data (compatibility method)"""
        # Convert file_name to collection_name format
        collection_name = file_name.replace('.xlsx', '').replace('.xls', '')
        return self.write_dataframe(project_name, collection_name, df)
    
    def create_project(self, project_data):
        """Create a new project"""
        try:
            # Get existing projects
            projects_df = self.read_dataframe(None, "projects")
            
            # Check if project already exists
            if not projects_df.empty and project_data['Project_Name'] in projects_df['Project_Name'].values:
                return False
            
            # Add new project
            new_project = pd.DataFrame([project_data])
            if projects_df.empty:
                projects_df = new_project
            else:
                projects_df = pd.concat([projects_df, new_project], ignore_index=True)
            
            # Save updated projects
            success = self.write_dataframe(None, "projects", projects_df)
            
            # Create project directory in local storage
            if success:
                project_dir = f"local_data/projects/{project_data['Project_Name']}"
                os.makedirs(project_dir, exist_ok=True)
            
            return success
        except Exception as e:
            print(f"Error creating project: {str(e)}")
            return False
    
    def hash_password(self, password):
        """Hash password for security"""
        salt = "navchetna_salt"  # In production, use a secure random salt for each user
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _get_local_file_path(self, project_name, collection_name):
        """Get local file path for a collection"""
        # Convert collection name to file name format
        file_name = f"{collection_name}.xlsx"
        
        if project_name:
            # Ensure project directory exists
            project_dir = f"local_data/projects/{project_name}"
            os.makedirs(project_dir, exist_ok=True)
            return f"{project_dir}/{file_name}"
        else:
            return f"local_data/{file_name}"
    
    def _save_to_local_file(self, project_name, collection_name, df):
        """Save data to local Excel file"""
        try:
            file_path = self._get_local_file_path(project_name, collection_name)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save to Excel file
            df.to_excel(file_path, index=False)
            print(f"Data saved to local file: {file_path}")
            return True
        except Exception as e:
            print(f"Error saving to local file: {str(e)}")
            return False
    
    def _clean_dataframe_for_storage(self, df):
        """Clean DataFrame to prevent data type conversion issues and PyArrow errors"""
        try:
            # Make a copy to avoid modifying original
            df_clean = df.copy()
            
            # Clean each column based on its content
            for col in df_clean.columns:
                # First, handle NaN and None values
                df_clean[col] = df_clean[col].fillna('')
                
                # Convert to string to handle mixed types
                df_clean[col] = df_clean[col].astype(str)
                
                # Clean empty strings and 'nan' strings
                df_clean[col] = df_clean[col].replace(['nan', 'None', 'NaN', 'null'], '')
                
                # Try to identify and convert numeric columns
                if self._is_numeric_column(df_clean[col]):
                    # Convert to numeric, replacing empty strings with 0
                    df_clean[col] = df_clean[col].replace('', '0')
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                    # Ensure consistent numeric type
                    df_clean[col] = df_clean[col].astype('float64')
                else:
                    # Keep as string, ensure consistent string type
                    df_clean[col] = df_clean[col].astype('str')
                    # Replace empty strings with proper empty string
                    df_clean[col] = df_clean[col].replace('', '')
            
            return df_clean
        except Exception as e:
            print(f"Error cleaning dataframe: {str(e)}")
            return df
    
    def _is_numeric_column(self, series):
        """Check if a series should be treated as numeric"""
        try:
            # Remove empty strings and common non-numeric values
            non_empty = series[~series.isin(['', 'nan', 'None', 'NaN', 'null'])]
            
            if len(non_empty) == 0:
                return False
            
            # Try to convert to numeric
            pd.to_numeric(non_empty, errors='raise')
            return True
        except:
            return False
    
    def get_all_collections(self, project_name=None):
        """Get all collections for a project or global collections"""
        try:
            if self.is_online and self.db:
                # Get all collections from MongoDB
                all_collections = self.db.list_collection_names()
                
                if project_name:
                    # Filter collections for specific project
                    prefix = f"{project_name}_".lower()
                    project_collections = [coll.replace(prefix, '') for coll in all_collections 
                                          if coll.startswith(prefix)]
                    return project_collections
                else:
                    # Filter out project-specific collections
                    global_collections = [coll for coll in all_collections 
                                         if '_' not in coll or coll.count('_') < 2]
                    return global_collections
            
            # Fallback to local file system
            if project_name:
                project_dir = f"local_data/projects/{project_name}"
                if os.path.exists(project_dir):
                    return [f.replace('.xlsx', '') for f in os.listdir(project_dir) 
                           if f.endswith('.xlsx')]
            else:
                return [f.replace('.xlsx', '') for f in os.listdir("local_data") 
                       if f.endswith('.xlsx') and os.path.isfile(os.path.join("local_data", f))]
                
            return []
        except Exception as e:
            print(f"Error getting collections: {str(e)}")
            return []
    
    def delete_collection(self, project_name, collection_name):
        """Delete a collection"""
        try:
            if self.is_online and self.db:
                collection = self.get_collection(project_name, collection_name)
                if collection:
                    collection.drop()
            
            # Also delete local file
            file_path = self._get_local_file_path(project_name, collection_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return True
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")
            return False
    
    def add_document(self, project_name, collection_name, document):
        """Add a single document to a collection"""
        try:
            # Read existing data
            df = self.read_dataframe(project_name, collection_name)
            
            # Add new document
            new_df = pd.DataFrame([document])
            if df.empty:
                df = new_df
            else:
                df = pd.concat([df, new_df], ignore_index=True)
            
            # Write updated data
            return self.write_dataframe(project_name, collection_name, df)
        except Exception as e:
            print(f"Error adding document: {str(e)}")
            return False
    
    def update_document(self, project_name, collection_name, document_index, updated_data):
        """Update a document by index"""
        try:
            # Read existing data
            df = self.read_dataframe(project_name, collection_name)
            
            if df.empty or document_index >= len(df):
                return False
            
            # Update document
            for key, value in updated_data.items():
                if key in df.columns:
                    df.at[document_index, key] = value
            
            # Write updated data
            return self.write_dataframe(project_name, collection_name, df)
        except Exception as e:
            print(f"Error updating document: {str(e)}")
            return False
    
    def delete_document(self, project_name, collection_name, document_index):
        """Delete a document by index"""
        try:
            # Read existing data
            df = self.read_dataframe(project_name, collection_name)
            
            if df.empty or document_index >= len(df):
                return False
            
            # Delete document
            df = df.drop(document_index).reset_index(drop=True)
            
            # Write updated data
            return self.write_dataframe(project_name, collection_name, df)
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False 