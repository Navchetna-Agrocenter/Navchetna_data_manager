# -*- coding: utf-8 -*-
"""
Additional functions for MongoDB-powered Streamlit Application
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def show_add_data():
    """Show add data interface"""
    st.title("📝 Add Data")
    
    # Get user's accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("⚠️ You don't have access to any projects. Please contact an administrator.")
        return
    
    # Project selection
    project_name = st.selectbox("🏢 Select Project", accessible_projects)
    
    if not project_name:
        st.info("Please select a project to continue.")
        return
    
    # Get available tables for the project
    available_tables = table_manager.get_project_tables(project_name)
    
    if not available_tables:
        st.info(f"No tables found for project '{project_name}'. Create tables in Schema Management first.")
        return
    
    # Table selection
    st.subheader("📋 Select Table Type")
    table_name = st.radio("Choose table to add data to:", available_tables)
    
    if table_name:
        show_dynamic_form(project_name, table_name)

def show_dynamic_form(project_name: str, table_name: str):
    """Display dynamic form for data entry"""
    st.subheader(f"📝 {table_name} Data Entry")
    
    # Get table schema
    schema = table_manager.get_table_schema(table_name)
    
    if not schema:
        st.error("❌ Table schema not found!")
        return
    
    with st.form(f"{table_name.lower().replace(' ', '_')}_form", clear_on_submit=True):
        st.markdown('<div class="data-form">', unsafe_allow_html=True)
        
        record_data = {}
        
        # Create form fields dynamically
        col1, col2 = st.columns(2)
        field_count = 0
        
        for field in schema:
            field_name = field['name']
            field_type = field['type']
            required = field.get('required', False)
            default_value = field.get('default', '')
            description = field.get('description', '')
            
            # Alternate between columns
            col = col1 if field_count % 2 == 0 else col2
            
            with col:
                if field_type == "Date":
                    if default_value:
                        try:
                            default_date = pd.to_datetime(default_value).date()
                        except:
                            default_date = datetime.now().date()
                    else:
                        default_date = datetime.now().date()
                    
                    value = st.date_input(field_name, default_date, help=description)
                    record_data[field_name] = value.strftime('%Y-%m-%d')
                    
                elif field_type == "Number":
                    default_num = float(default_value) if default_value else 0.0
                    value = st.number_input(field_name, value=default_num, step=0.1, help=description)
                    record_data[field_name] = value
                    
                elif field_type == "True/False":
                    default_bool = default_value.lower() == 'true' if default_value else False
                    value = st.checkbox(field_name, value=default_bool, help=description)
                    record_data[field_name] = value
                    
                elif field_type == "Dropdown":
                    options = field.get('options', ['Option 1', 'Option 2'])
                    if isinstance(options, str):
                        options = [opt.strip() for opt in options.split(',')]
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
            if table_manager.add_record(project_name, table_name, record_data):
                st.success(f"✅ {table_name} record added successfully! Form has been reset for next entry.")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ Failed to add {table_name} record. Please try again.")

def show_analytics():
    """Display analytics and charts page"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Analytics</h1>
        <p>Analyze plantation data with interactive charts and insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get available projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects accessible for analytics.")
        return
    
    # Project selection
    selected_project = st.selectbox("Select Project for Analysis", accessible_projects)
    
    if not selected_project:
        return
    
    # Get data
    kml_data = table_manager.get_table_data(selected_project, "KML Tracking")
    plantation_data = table_manager.get_table_data(selected_project, "Plantation Records")
    
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
    if 'Date' in kml_data.columns and len(kml_data) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
            if 'Status' in kml_data.columns:
                status_counts = kml_data['Status'].value_counts()
                if not status_counts.empty:
                    fig = px.pie(values=status_counts.values, names=status_counts.index, 
                               title="KML Status Distribution")
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Monthly trends
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

def show_manage_records():
    """Display manage records page"""
    st.markdown("""
    <div class="main-header">
        <h1>📋 Manage Records</h1>
        <p>View, edit, and delete existing records</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get user accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
    if not accessible_projects:
        st.warning("No projects assigned to your account.")
        return
    
    # Project selection
    project_name = st.selectbox("Choose project:", accessible_projects)
    
    if not project_name:
        return
    
    # Get available tables
    available_tables = table_manager.get_project_tables(project_name)
    
    if not available_tables:
        st.info(f"No tables found for project '{project_name}'.")
        return
    
    # Table selection
    table_name = st.selectbox("Choose table to manage:", available_tables)
    
    if not table_name:
        return
    
    # Load and display records
    table_data = table_manager.get_table_data(project_name, table_name)
    
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
                record_df['Value'] = record_df['Value'].astype(str)
                record_df.index.name = 'Field'
                st.dataframe(record_df, use_container_width=True)
            
            with col2:
                if st.button(f"✏️ Edit", key=f"edit_{table_name}_{idx}"):
                    st.session_state[f'editing_{table_name}_{idx}'] = True
                    st.rerun()
            
            with col3:
                if st.button(f"🗑️ Delete", key=f"delete_{table_name}_{idx}"):
                    if table_manager.delete_record(project_name, table_name, idx):
                        st.success("Record deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete record.")
            
            # Edit form
            if st.session_state.get(f'editing_{table_name}_{idx}', False):
                show_edit_form(project_name, table_name, idx, row)

def show_edit_form(project_name, table_name, record_idx, record_data):
    """Show edit form for a record"""
    st.markdown("**Edit Record:**")
    
    # Get table schema
    schema = table_manager.get_table_schema(table_name)
    
    edit_data = {}
    
    for field in schema:
        field_name = field['name']
        field_type = field['type']
        current_value = record_data.get(field_name, '')
        
        if pd.isna(current_value):
            current_value = ""
        
        if field_type == "Date":
            try:
                if current_value:
                    default_date = pd.to_datetime(current_value).date()
                else:
                    default_date = datetime.now().date()
            except:
                default_date = datetime.now().date()
            
            value = st.date_input(f"{field_name}:", default_date, key=f"edit_{field_name}_{record_idx}")
            edit_data[field_name] = value.strftime('%Y-%m-%d')
            
        elif field_type == "Number":
            try:
                default_num = float(current_value) if current_value else 0.0
            except:
                default_num = 0.0
            
            value = st.number_input(f"{field_name}:", value=default_num, step=0.1, key=f"edit_{field_name}_{record_idx}")
            edit_data[field_name] = value
            
        elif field_type == "True/False":
            try:
                default_bool = bool(current_value) if current_value else False
            except:
                default_bool = False
            
            value = st.checkbox(f"{field_name}:", value=default_bool, key=f"edit_{field_name}_{record_idx}")
            edit_data[field_name] = value
            
        elif field_type == "Dropdown":
            options = field.get('options', ['Option 1', 'Option 2'])
            if isinstance(options, str):
                options = [opt.strip() for opt in options.split(',')]
            
            try:
                index = options.index(str(current_value)) if str(current_value) in options else 0
            except:
                index = 0
            
            value = st.selectbox(f"{field_name}:", options, index=index, key=f"edit_{field_name}_{record_idx}")
            edit_data[field_name] = value
            
        else:  # Text
            value = st.text_input(f"{field_name}:", value=str(current_value), key=f"edit_{field_name}_{record_idx}")
            edit_data[field_name] = value
    
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button(f"💾 Save Changes", key=f"save_{table_name}_{record_idx}"):
            if table_manager.update_record(project_name, table_name, record_idx, edit_data):
                st.success("Record updated successfully!")
                st.session_state[f'editing_{table_name}_{record_idx}'] = False
                st.rerun()
            else:
                st.error("Failed to update record.")
    
    with col_cancel:
        if st.button(f"❌ Cancel", key=f"cancel_{table_name}_{record_idx}"):
            st.session_state[f'editing_{table_name}_{record_idx}'] = False
            st.rerun()

def show_reports():
    """Display reports generation page"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Reports</h1>
        <p>Generate and download various reports for your projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get accessible projects
    accessible_projects = auth_manager.get_accessible_projects()
    
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

def generate_report(project_name: str, start_date, end_date, report_type: str):
    """Generate and download report"""
    try:
        # Get data for the date range
        kml_data = table_manager.get_table_data(project_name, "KML Tracking")
        plantation_data = table_manager.get_table_data(project_name, "Plantation Records")
        
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
            
            if report_type in ["Detailed Plantation Report", "Combined Report"]:
                if not plantation_data.empty:
                    plantation_data.to_excel(writer, sheet_name='Plantation Details', index=False)
        
        # Provide download link
        with open(report_filename, 'rb') as file:
            st.download_button(
                label=f"📥 Download {report_type}",
                data=file.read(),
                file_name=report_filename,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        st.success(f"✅ Report generated successfully!")
        
        # Clean up the local file
        import os
        os.remove(report_filename)
        
    except Exception as e:
        st.error(f"❌ Error generating report: {str(e)}")

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
        
        summary_data.append(['Total Area Planted', f"{area_planted:.2f} hectares"])
        summary_data.append(['Total Trees Planted', trees_planted])
        summary_data.append(['Total Farmers Covered', farmers_covered])
    else:
        summary_data.append(['No plantation data available', ''])
    
    # Convert to DataFrame and save
    summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
    summary_df.to_excel(writer, sheet_name='Summary', index=False)

def generate_project_overview(project_name: str):
    """Generate project overview report"""
    try:
        report_filename = f"{project_name}_Project_Overview_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # Get all data
        kml_data = table_manager.get_table_data(project_name, "KML Tracking")
        plantation_data = table_manager.get_table_data(project_name, "Plantation Records")
        
        with pd.ExcelWriter(report_filename, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Create overview sheet
            create_summary_sheet(writer, workbook, kml_data, plantation_data, project_name)
        
        # Download
        with open(report_filename, 'rb') as file:
            st.download_button(
                label="📥 Download Project Overview",
                data=file.read(),
                file_name=report_filename,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        st.success("✅ Project overview report generated!")
        import os
        os.remove(report_filename)
        
    except Exception as e:
        st.error(f"❌ Error generating overview: {str(e)}")

# Continue with user management, project management, and schema management functions... 