"""
Sample Data Generator for GitHub Deployment

This module contains functions to initialize sample data in session state
when running on GitHub deployment where file storage is not available.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def initialize_sample_data():
    """Initialize sample data in session state for GitHub deployment"""
    # Only initialize if we're in GitHub deployment mode
    if st.session_state.get('deployment_mode') != 'github':
        return
        
    # Check if data is already initialized
    if 'data_initialized' in st.session_state:
        return
        
    # Initialize users
    users_df = pd.DataFrame([
        {
            'Username': 'admin',
            'Password_Hash': '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',  # admin123
            'Role': 'Administrator',
            'Full_Name': 'Admin User',
            'Email': 'admin@example.com',
            'Accessible_Projects': 'All',
            'Last_Login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'Username': 'manager1',
            'Password_Hash': '6ee4a469cd4e91053847f5d3fcb61dbcc91e8f0ef10be7748da4c4a1ba382d17',  # manager123
            'Role': 'Project Manager',
            'Full_Name': 'Manager One',
            'Email': 'manager1@example.com',
            'Accessible_Projects': 'MakeMyTrip',
            'Last_Login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'Username': 'manager2',
            'Password_Hash': '6ee4a469cd4e91053847f5d3fcb61dbcc91e8f0ef10be7748da4c4a1ba382d17',  # manager123
            'Role': 'Project Manager',
            'Full_Name': 'Manager Two',
            'Email': 'manager2@example.com',
            'Accessible_Projects': 'Absolute',
            'Last_Login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'Username': 'viewer',
            'Password_Hash': '55e0e0be5f7960f9f5e410fcc8ca37cfe71fea2a6c0d04a79e1c9f4bd0d8dc34',  # viewer123
            'Role': 'Viewer',
            'Full_Name': 'View User',
            'Email': 'viewer@example.com',
            'Accessible_Projects': 'All',
            'Last_Login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ])
    
    st.session_state['data_master_users'] = users_df
    
    # Initialize projects
    projects_df = pd.DataFrame([
        {
            'Project_ID': 'PRJ001',
            'Project_Name': 'MakeMyTrip',
            'Description': 'Plantation project for MakeMyTrip sustainability initiative',
            'Start_Date': '2024-01-01',
            'Target_Area': 1000,
            'Assigned_Users': 'manager1',
            'Status': 'Active',
            'Manager': 'manager1'
        },
        {
            'Project_ID': 'PRJ002',
            'Project_Name': 'Absolute',
            'Description': 'Absolute company plantation and carbon offset project',
            'Target_Area': 750,
            'Start_Date': '2024-02-01',
            'Assigned_Users': 'manager2',
            'Status': 'Active',
            'Manager': 'manager2'
        }
    ])
    
    st.session_state['data_master_projects'] = projects_df
    
    # Generate KML data for each project
    _create_sample_kml_data('MakeMyTrip')
    _create_sample_kml_data('Absolute')
    
    # Generate plantation data for each project
    _create_sample_plantation_data('MakeMyTrip')
    _create_sample_plantation_data('Absolute')
    
    # Mark as initialized
    st.session_state['data_initialized'] = True
    st.success("✅ Sample data initialized successfully!")
    
def _create_sample_kml_data(project_name):
    """Create sample KML tracking data for a project"""
    kml_data = []
    for i in range(30):  # Last 30 days
        date = (datetime.now() - timedelta(days=30-i)).strftime('%Y-%m-%d')
        kml_count = np.random.randint(1, 8)
        total_area = np.random.randint(10, 100)
        approved_area = int(total_area * np.random.uniform(0.7, 1.0))
        
        kml_data.append({
            'Date': date,
            'User': 'manager1' if project_name == 'MakeMyTrip' else 'manager2',
            'KML_Count_Sent': kml_count,
            'Total_Area': total_area,
            'Area_Approved': approved_area,
            'Approval_Date': date if np.random.random() > 0.2 else '',
            'Status': np.random.choice(['Pending', 'Approved', 'Rejected', 'Under Review'], p=[0.1, 0.7, 0.1, 0.1]),
            'Remarks': f'Batch {i+1} submission'
        })
    
    kml_df = pd.DataFrame(kml_data)
    st.session_state[f'data_{project_name}_kml_tracking'] = kml_df
    
def _create_sample_plantation_data(project_name):
    """Create sample plantation records for a project"""
    plantation_data = []
    for i in range(25):  # Last 25 days with plantation activity
        date = (datetime.now() - timedelta(days=25-i)).strftime('%Y-%m-%d')
        area_planted = np.random.randint(5, 50)
        farmers = np.random.randint(1, 5)
        trees = area_planted * np.random.randint(50, 150)
        pits_dug = area_planted * np.random.randint(80, 120)  # Number of pits dug
        
        plantation_data.append({
            'Date': date,
            'User': 'manager1' if project_name == 'MakeMyTrip' else 'manager2',
            'Plot_Code': f'{project_name[:3].upper()}-{i+1:03d}',
            'Area_Planted': area_planted,
            'Farmer_Covered': farmers,
            'Trees_Planted': trees,
            'Pits_Dug': pits_dug,
            'Status': np.random.choice(['Completed', 'In Progress'], p=[0.8, 0.2])
        })
    
    plantation_df = pd.DataFrame(plantation_data)
    st.session_state[f'data_{project_name}_plantation_records'] = plantation_df 