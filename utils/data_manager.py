"""
Data Manager for handling all data operations, calculations, and analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import streamlit as st
import config
from utils.sharepoint_manager import SharePointManager

class DataManager:
    def __init__(self, sharepoint_manager: SharePointManager):
        self.sp_manager = sharepoint_manager
    
    def initialize_default_data(self):
        """Initialize default projects and sample data"""
        # Initialize projects if they don't exist
        projects_df = self.sp_manager.read_excel_file(None, config.FILE_NAMING['projects'])
        
        if projects_df.empty:
            # Create default projects
            default_projects_data = []
            for i, project in enumerate(config.DEFAULT_PROJECTS):
                project_data = {
                    'Project_ID': f'PRJ{i+1:03d}',
                    'Project_Name': project['name'],
                    'Description': project['description'],
                    'Start_Date': project['start_date'],
                    'Target_Area': project['target_area'],
                    'Assigned_Users': 'manager1' if project['name'] == 'MakeMyTrip' else 'manager2',
                    'Status': project['status'],
                    'Manager': 'manager1' if project['name'] == 'MakeMyTrip' else 'manager2'
                }
                default_projects_data.append(project_data)
            
            projects_df = pd.DataFrame(default_projects_data)
            self.sp_manager.write_excel_file(None, config.FILE_NAMING['projects'], projects_df)
            
            # Initialize project files with sample data
            for project in config.DEFAULT_PROJECTS:
                self._create_sample_data(project['name'])
    
    def _create_sample_data(self, project_name: str):
        """Create sample data for a project"""
        # Sample KML tracking data
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
                'Status': np.random.choice(config.KML_STATUS, p=[0.1, 0.7, 0.1, 0.1]),
                'Remarks': f'Batch {i+1} submission'
            })
        
        kml_df = pd.DataFrame(kml_data)
        self.sp_manager.write_excel_file(project_name, config.FILE_NAMING['kml_tracking'], kml_df)
        
        # Sample plantation records
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
        self.sp_manager.write_excel_file(project_name, config.FILE_NAMING['plantation_records'], plantation_df)
    
    def add_kml_record(self, project_name: str, record_data: Dict) -> bool:
        """Add new KML tracking record"""
        try:
            kml_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['kml_tracking'])
            
            # Add current date and user if not provided
            if 'Date' not in record_data:
                record_data['Date'] = datetime.now().strftime('%Y-%m-%d')
            if 'User' not in record_data:
                record_data['User'] = st.session_state.get('username', 'Unknown')
            
            # Add new record
            new_record = pd.DataFrame([record_data])
            kml_df = pd.concat([kml_df, new_record], ignore_index=True)
            
            # Sort by date (newest first)
            kml_df['Date'] = pd.to_datetime(kml_df['Date'])
            kml_df = kml_df.sort_values('Date', ascending=False)
            kml_df['Date'] = kml_df['Date'].dt.strftime('%Y-%m-%d')
            
            return self.sp_manager.write_excel_file(project_name, config.FILE_NAMING['kml_tracking'], kml_df)
            
        except Exception as e:
            st.error(f"Error adding KML record: {str(e)}")
            return False
    
    def add_plantation_record(self, project_name: str, record_data: Dict) -> bool:
        """Add new plantation record"""
        try:
            plantation_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['plantation_records'])
            
            # Add current date and user if not provided
            if 'Date' not in record_data:
                record_data['Date'] = datetime.now().strftime('%Y-%m-%d')
            if 'User' not in record_data:
                record_data['User'] = st.session_state.get('username', 'Unknown')
            
            # Add new record
            new_record = pd.DataFrame([record_data])
            plantation_df = pd.concat([plantation_df, new_record], ignore_index=True)
            
            # Sort by date (newest first)
            plantation_df['Date'] = pd.to_datetime(plantation_df['Date'])
            plantation_df = plantation_df.sort_values('Date', ascending=False)
            plantation_df['Date'] = plantation_df['Date'].dt.strftime('%Y-%m-%d')
            
            return self.sp_manager.write_excel_file(project_name, config.FILE_NAMING['plantation_records'], plantation_df)
            
        except Exception as e:
            st.error(f"Error adding plantation record: {str(e)}")
            return False
    
    def get_project_summary(self, project_name: str) -> Dict:
        """Get comprehensive project summary"""
        try:
            kml_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['kml_tracking'])
            plantation_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['plantation_records'])
            projects_df = self.sp_manager.read_excel_file(None, config.FILE_NAMING['projects'])
            
            # Handle backward compatibility for Pit_Digging -> Pits_Dug
            if not plantation_df.empty:
                if 'Pit_Digging' in plantation_df.columns and 'Pits_Dug' not in plantation_df.columns:
                    plantation_df['Pits_Dug'] = 0  # Set default for old data
                elif 'Pit_Digging' in plantation_df.columns and 'Pits_Dug' in plantation_df.columns:
                    plantation_df = plantation_df.drop('Pit_Digging', axis=1)  # Remove old column
            
            # Project basic info
            project_info = projects_df[projects_df['Project_Name'] == project_name].iloc[0] if not projects_df.empty else {}
            target_area = project_info.get('Target_Area', 0) if not projects_df.empty else 0
            
            summary = {
                'project_name': project_name,
                'target_area': target_area,
                'start_date': project_info.get('Start_Date', ''),
                'status': project_info.get('Status', 'Unknown'),
                'manager': project_info.get('Manager', 'Unknown')
            }
            
            # KML data summary
            if not kml_df.empty:
                summary.update({
                    'total_kml_sent': kml_df['KML_Count_Sent'].sum(),
                    'total_area_sent': kml_df['Total_Area'].sum(),
                    'total_area_approved': kml_df['Area_Approved'].sum(),
                    'approval_rate': (kml_df['Area_Approved'].sum() / kml_df['Total_Area'].sum() * 100) if kml_df['Total_Area'].sum() > 0 else 0,
                    'pending_approvals': len(kml_df[kml_df['Status'] == 'Pending']),
                    'approved_count': len(kml_df[kml_df['Status'] == 'Approved']),
                    'rejected_count': len(kml_df[kml_df['Status'] == 'Rejected'])
                })
            else:
                summary.update({
                    'total_kml_sent': 0,
                    'total_area_sent': 0,
                    'total_area_approved': 0,
                    'approval_rate': 0,
                    'pending_approvals': 0,
                    'approved_count': 0,
                    'rejected_count': 0
                })
            
            # Plantation data summary
            if not plantation_df.empty:
                summary.update({
                    'total_area_planted': plantation_df['Area_Planted'].sum(),
                    'total_farmers_covered': plantation_df['Farmer_Covered'].sum(),
                    'total_trees_planted': plantation_df['Trees_Planted'].sum(),
                    'plantation_completion': (plantation_df['Area_Planted'].sum() / target_area * 100) if target_area > 0 else 0,
                    'active_plots': len(plantation_df[plantation_df['Status'] == 'In Progress']),
                    'completed_plots': len(plantation_df[plantation_df['Status'] == 'Completed'])
                })
            else:
                summary.update({
                    'total_area_planted': 0,
                    'total_farmers_covered': 0,
                    'total_trees_planted': 0,
                    'plantation_completion': 0,
                    'active_plots': 0,
                    'completed_plots': 0
                })
            
            return summary
            
        except Exception as e:
            st.error(f"Error getting project summary: {str(e)}")
            return {}
    
    def get_daily_progress_data(self, project_name: str, days: int = 30) -> Dict:
        """Get daily progress data for charts"""
        try:
            kml_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['kml_tracking'])
            plantation_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['plantation_records'])
            
            # Filter data for specified days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Process KML data
            kml_daily = {}
            if not kml_df.empty:
                kml_df['Date'] = pd.to_datetime(kml_df['Date'])
                kml_filtered = kml_df[kml_df['Date'] >= start_date]
                kml_daily = kml_filtered.groupby(kml_filtered['Date'].dt.strftime('%Y-%m-%d')).agg({
                    'KML_Count_Sent': 'sum',
                    'Total_Area': 'sum',
                    'Area_Approved': 'sum'
                }).to_dict('index')
            
            # Process plantation data
            plantation_daily = {}
            if not plantation_df.empty:
                plantation_df['Date'] = pd.to_datetime(plantation_df['Date'])
                plantation_filtered = plantation_df[plantation_df['Date'] >= start_date]
                plantation_daily = plantation_filtered.groupby(plantation_filtered['Date'].dt.strftime('%Y-%m-%d')).agg({
                    'Area_Planted': 'sum',
                    'Trees_Planted': 'sum',
                    'Farmer_Covered': 'sum'
                }).to_dict('index')
            
            return {
                'kml_daily': kml_daily,
                'plantation_daily': plantation_daily
            }
            
        except Exception as e:
            st.error(f"Error getting daily progress data: {str(e)}")
            return {'kml_daily': {}, 'plantation_daily': {}}
    
    def get_all_projects_summary(self) -> List[Dict]:
        """Get summary for all projects"""
        try:
            projects = self.sp_manager.get_project_list()
            summaries = []
            
            for project in projects:
                summary = self.get_project_summary(project)
                if summary:
                    summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            st.error(f"Error getting all projects summary: {str(e)}")
            return []
    
    def get_weekly_comparison(self, project_name: str) -> Dict:
        """Get weekly comparison data"""
        try:
            kml_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['kml_tracking'])
            plantation_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['plantation_records'])
            
            current_week_start = datetime.now() - timedelta(days=7)
            previous_week_start = current_week_start - timedelta(days=7)
            
            comparison = {}
            
            # KML comparison
            if not kml_df.empty:
                kml_df['Date'] = pd.to_datetime(kml_df['Date'])
                
                current_week_kml = kml_df[kml_df['Date'] >= current_week_start]
                previous_week_kml = kml_df[(kml_df['Date'] >= previous_week_start) & (kml_df['Date'] < current_week_start)]
                
                comparison['kml'] = {
                    'current_week': {
                        'count_sent': current_week_kml['KML_Count_Sent'].sum(),
                        'area_sent': current_week_kml['Total_Area'].sum(),
                        'area_approved': current_week_kml['Area_Approved'].sum()
                    },
                    'previous_week': {
                        'count_sent': previous_week_kml['KML_Count_Sent'].sum(),
                        'area_sent': previous_week_kml['Total_Area'].sum(),
                        'area_approved': previous_week_kml['Area_Approved'].sum()
                    }
                }
            
            # Plantation comparison
            if not plantation_df.empty:
                plantation_df['Date'] = pd.to_datetime(plantation_df['Date'])
                
                current_week_plantation = plantation_df[plantation_df['Date'] >= current_week_start]
                previous_week_plantation = plantation_df[(plantation_df['Date'] >= previous_week_start) & (plantation_df['Date'] < current_week_start)]
                
                comparison['plantation'] = {
                    'current_week': {
                        'area_planted': current_week_plantation['Area_Planted'].sum(),
                        'trees_planted': current_week_plantation['Trees_Planted'].sum(),
                        'farmers_covered': current_week_plantation['Farmer_Covered'].sum()
                    },
                    'previous_week': {
                        'area_planted': previous_week_plantation['Area_Planted'].sum(),
                        'trees_planted': previous_week_plantation['Trees_Planted'].sum(),
                        'farmers_covered': previous_week_plantation['Farmer_Covered'].sum()
                    }
                }
            
            return comparison
            
        except Exception as e:
            st.error(f"Error getting weekly comparison: {str(e)}")
            return {}
    
    def export_project_report(self, project_name: str) -> pd.ExcelWriter:
        """Export comprehensive project report"""
        try:
            kml_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['kml_tracking'])
            plantation_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['plantation_records'])
            summary = self.get_project_summary(project_name)
            
            # Create Excel writer
            report_filename = f"{project_name}_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
            writer = pd.ExcelWriter(report_filename, engine='xlsxwriter')
            
            # Summary sheet
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # KML data sheet
            if not kml_df.empty:
                kml_df.to_excel(writer, sheet_name='KML_Tracking', index=False)
            
            # Plantation data sheet
            if not plantation_df.empty:
                plantation_df.to_excel(writer, sheet_name='Plantation_Records', index=False)
            
            return writer
            
        except Exception as e:
            st.error(f"Error exporting report: {str(e)}")
            return None
    
    def update_record(self, project_name: str, file_type: str, record_index: int, updated_data: Dict) -> bool:
        """Update existing record"""
        try:
            file_name = config.FILE_NAMING[file_type]
            df = self.sp_manager.read_excel_file(project_name, file_name)
            
            if df.empty or record_index >= len(df):
                st.error("Record not found")
                return False
            
            # Update record
            for key, value in updated_data.items():
                if key in df.columns:
                    df.loc[record_index, key] = value
            
            return self.sp_manager.write_excel_file(project_name, file_name, df)
            
        except Exception as e:
            st.error(f"Error updating record: {str(e)}")
            return False
    
    def delete_record(self, project_name: str, file_type: str, record_index: int) -> bool:
        """Delete existing record"""
        try:
            file_name = config.FILE_NAMING[file_type]
            df = self.sp_manager.read_excel_file(project_name, file_name)
            
            if df.empty or record_index >= len(df):
                st.error("Record not found")
                return False
            
            # Delete record
            df = df.drop(df.index[record_index])
            df = df.reset_index(drop=True)
            
            return self.sp_manager.write_excel_file(project_name, file_name, df)
            
        except Exception as e:
            st.error(f"Error deleting record: {str(e)}")
            return False
    
    def migrate_plantation_data(self, project_name: str):
        """Migrate plantation data from old format to new format (adding Pits_Dug)"""
        try:
            plantation_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['plantation_records'])
            
            if not plantation_df.empty:
                # Check if migration is needed
                if 'Pit_Digging' in plantation_df.columns and 'Pits_Dug' not in plantation_df.columns:
                    # For old data, convert status-based pit digging to numeric
                    plantation_df['Pits_Dug'] = plantation_df['Area_Planted'] * 80  # Default 80 pits per hectare
                    self.sp_manager.write_excel_file(project_name, config.FILE_NAMING['plantation_records'], plantation_df)
                elif 'Pit_Digging' in plantation_df.columns and 'Pits_Dug' in plantation_df.columns:
                    # Remove old column
                    plantation_df = plantation_df.drop('Pit_Digging', axis=1)
                    self.sp_manager.write_excel_file(project_name, config.FILE_NAMING['plantation_records'], plantation_df)
                    
        except Exception as e:
            # Migration not critical, continue silently
            pass

    def get_kml_data(self, project_name: str) -> pd.DataFrame:
        """Get KML tracking data for a project"""
        try:
            return self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['kml_tracking'])
        except Exception:
            return pd.DataFrame()

    def get_plantation_data(self, project_name: str) -> pd.DataFrame:
        """Get plantation records data for a project"""
        try:
            plantation_df = self.sp_manager.read_excel_file(project_name, config.FILE_NAMING['plantation_records'])
            
            # Handle backward compatibility for Pit_Digging -> Pits_Dug
            if not plantation_df.empty:
                if 'Pit_Digging' in plantation_df.columns and 'Pits_Dug' not in plantation_df.columns:
                    plantation_df['Pits_Dug'] = plantation_df['Area_Planted'] * 80  # Default conversion
                elif 'Pit_Digging' in plantation_df.columns and 'Pits_Dug' in plantation_df.columns:
                    plantation_df = plantation_df.drop('Pit_Digging', axis=1)  # Remove old column
            
            return plantation_df
        except Exception:
            return pd.DataFrame()

    def get_project_data(self, project_name: str) -> Dict:
        """Get all project data including KML and plantation records"""
        return {
            'kml_data': self.get_kml_data(project_name),
            'plantation_data': self.get_plantation_data(project_name),
            'summary': self.get_project_summary(project_name)
        }

    def get_all_project_names(self) -> List[str]:
        """Get list of all project names"""
        try:
            projects_df = self.sp_manager.read_excel_file(None, config.FILE_NAMING['projects'])
            if not projects_df.empty and 'Project_Name' in projects_df.columns:
                return projects_df['Project_Name'].tolist()
            else:
                return ['MakeMyTrip', 'Absolute']  # Fallback
        except Exception:
            return ['MakeMyTrip', 'Absolute']  # Fallback 