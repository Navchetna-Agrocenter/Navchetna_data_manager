"""
Charts component for data visualizations and interactive charts
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config

class ChartManager:
    def __init__(self):
        self.colors = config.CHART_COLORS
        
    def create_kpi_cards(self, summary: Dict):
        """Create KPI cards for project summary"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🎯 Target Area (Hectares)",
                value=f"{summary.get('target_area', 0):,.0f}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="📋 KML Files Sent",
                value=f"{summary.get('total_kml_sent', 0):,.0f}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="✅ Area Approved (Hectares)",
                value=f"{summary.get('total_area_approved', 0):,.1f}",
                delta=f"{summary.get('approval_rate', 0):.1f}% approval rate"
            )
        
        with col4:
            st.metric(
                label="🌳 Trees Planted",
                value=f"{summary.get('total_trees_planted', 0):,.0f}",
                delta=f"{summary.get('total_farmers_covered', 0):,.0f} farmers"
            )
    
    def create_progress_charts(self, summary: Dict):
        """Create progress charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Area Progress Chart
            target_area = summary.get('target_area', 1)
            area_approved = summary.get('total_area_approved', 0)
            area_planted = summary.get('total_area_planted', 0)
            
            fig_progress = go.Figure()
            
            # Add bars
            fig_progress.add_trace(go.Bar(
                x=['Area Progress'],
                y=[area_approved],
                name='Approved',
                marker_color=self.colors['primary'],
                text=f'{area_approved:.1f} Ha',
                textposition='inside'
            ))
            
            fig_progress.add_trace(go.Bar(
                x=['Area Progress'],
                y=[area_planted],
                name='Planted',
                marker_color=self.colors['secondary'],
                text=f'{area_planted:.1f} Ha',
                textposition='inside'
            ))
            
            # Add target line
            fig_progress.add_hline(
                y=target_area,
                line_dash="dash",
                line_color=self.colors['danger'],
                annotation_text=f"Target: {target_area:.0f} Ha"
            )
            
            fig_progress.update_layout(
                title="Area Progress vs Target",
                xaxis_title="",
                yaxis_title="Area (Hectares)",
                barmode='group',
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig_progress, use_container_width=True)
        
        with col2:
            # KML Status Pie Chart
            approved_count = summary.get('approved_count', 0)
            pending_count = summary.get('pending_approvals', 0)
            rejected_count = summary.get('rejected_count', 0)
            
            labels = ['Approved', 'Pending', 'Rejected']
            values = [approved_count, pending_count, rejected_count]
            colors = [self.colors['primary'], self.colors['warning'], self.colors['danger']]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=colors
            )])
            
            fig_pie.update_layout(
                title="KML Approval Status",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
    
    def create_daily_trend_chart(self, daily_data: Dict, project_name: str):
        """Create daily trend charts"""
        kml_daily = daily_data.get('kml_daily', {})
        plantation_daily = daily_data.get('plantation_daily', {})
        
        # Prepare data for plotting
        dates = sorted(set(list(kml_daily.keys()) + list(plantation_daily.keys())))
        
        if not dates:
            st.info("No daily data available for trend analysis")
            return
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('KML Files Sent Daily', 'Area Sent vs Approved Daily', 
                           'Daily Plantation Area', 'Trees Planted Daily'),
            specs=[[{"secondary_y": False}, {"secondary_y": True}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # KML count trend
        kml_counts = [kml_daily.get(date, {}).get('KML_Count_Sent', 0) for date in dates]
        fig.add_trace(
            go.Scatter(x=dates, y=kml_counts, mode='lines+markers', name='KML Count', 
                      line=dict(color=self.colors['primary'])),
            row=1, col=1
        )
        
        # Area sent vs approved
        area_sent = [kml_daily.get(date, {}).get('Total_Area', 0) for date in dates]
        area_approved = [kml_daily.get(date, {}).get('Area_Approved', 0) for date in dates]
        
        fig.add_trace(
            go.Scatter(x=dates, y=area_sent, mode='lines+markers', name='Area Sent',
                      line=dict(color=self.colors['info'])),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=dates, y=area_approved, mode='lines+markers', name='Area Approved',
                      line=dict(color=self.colors['primary'])),
            row=1, col=2
        )
        
        # Plantation area
        plantation_area = [plantation_daily.get(date, {}).get('Area_Planted', 0) for date in dates]
        fig.add_trace(
            go.Scatter(x=dates, y=plantation_area, mode='lines+markers', name='Area Planted',
                      line=dict(color=self.colors['accent'])),
            row=2, col=1
        )
        
        # Trees planted
        trees_planted = [plantation_daily.get(date, {}).get('Trees_Planted', 0) for date in dates]
        fig.add_trace(
            go.Scatter(x=dates, y=trees_planted, mode='lines+markers', name='Trees Planted',
                      line=dict(color=self.colors['secondary'])),
            row=2, col=2
        )
        
        fig.update_layout(
            title=f"Daily Trends - {project_name}",
            height=600,
            showlegend=False
        )
        
        # Update x-axis labels
        for i in range(1, 3):
            for j in range(1, 3):
                fig.update_xaxes(tickangle=45, row=i, col=j)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_weekly_comparison_chart(self, comparison_data: Dict):
        """Create weekly comparison chart"""
        if not comparison_data:
            st.info("No weekly comparison data available")
            return
        
        kml_data = comparison_data.get('kml', {})
        plantation_data = comparison_data.get('plantation', {})
        
        # Create comparison chart
        categories = ['KML Count', 'Area Sent (Ha)', 'Area Approved (Ha)', 
                     'Area Planted (Ha)', 'Trees Planted', 'Farmers Covered']
        
        current_week = [
            kml_data.get('current_week', {}).get('count_sent', 0),
            kml_data.get('current_week', {}).get('area_sent', 0),
            kml_data.get('current_week', {}).get('area_approved', 0),
            plantation_data.get('current_week', {}).get('area_planted', 0),
            plantation_data.get('current_week', {}).get('trees_planted', 0),
            plantation_data.get('current_week', {}).get('farmers_covered', 0)
        ]
        
        previous_week = [
            kml_data.get('previous_week', {}).get('count_sent', 0),
            kml_data.get('previous_week', {}).get('area_sent', 0),
            kml_data.get('previous_week', {}).get('area_approved', 0),
            plantation_data.get('previous_week', {}).get('area_planted', 0),
            plantation_data.get('previous_week', {}).get('trees_planted', 0),
            plantation_data.get('previous_week', {}).get('farmers_covered', 0)
        ]
        
        fig = go.Figure(data=[
            go.Bar(name='Current Week', x=categories, y=current_week, 
                   marker_color=self.colors['primary']),
            go.Bar(name='Previous Week', x=categories, y=previous_week, 
                   marker_color=self.colors['secondary'])
        ])
        
        fig.update_layout(
            title='Weekly Performance Comparison',
            xaxis_title='Metrics',
            yaxis_title='Values',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_projects_overview_chart(self, projects_summary: List[Dict]):
        """Create overview chart for all projects"""
        if not projects_summary:
            st.info("No project data available")
            return
        
        # Prepare data
        project_names = [p['project_name'] for p in projects_summary]
        target_areas = [p.get('target_area', 0) for p in projects_summary]
        approved_areas = [p.get('total_area_approved', 0) for p in projects_summary]
        planted_areas = [p.get('total_area_planted', 0) for p in projects_summary]
        
        # Create grouped bar chart
        fig = go.Figure(data=[
            go.Bar(name='Target Area', x=project_names, y=target_areas, 
                   marker_color=self.colors['dark']),
            go.Bar(name='Approved Area', x=project_names, y=approved_areas, 
                   marker_color=self.colors['primary']),
            go.Bar(name='Planted Area', x=project_names, y=planted_areas, 
                   marker_color=self.colors['accent'])
        ])
        
        fig.update_layout(
            title='Projects Overview - Area Comparison',
            xaxis_title='Projects',
            yaxis_title='Area (Hectares)',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Create summary metrics table
        summary_df = pd.DataFrame([
            {
                'Project': p['project_name'],
                'Target (Ha)': f"{p.get('target_area', 0):,.0f}",
                'Approved (Ha)': f"{p.get('total_area_approved', 0):,.1f}",
                'Planted (Ha)': f"{p.get('total_area_planted', 0):,.1f}",
                'Progress (%)': f"{p.get('plantation_completion', 0):.1f}%",
                'Trees Planted': f"{p.get('total_trees_planted', 0):,.0f}",
                'Status': p.get('status', 'Unknown')
            }
            for p in projects_summary
        ])
        
        st.subheader("📊 Projects Summary Table")
        st.dataframe(summary_df, use_container_width=True)
    
    def create_interactive_filter_chart(self, df: pd.DataFrame, chart_type: str, project_name: str):
        """Create interactive charts with filters"""
        if df.empty:
            st.info(f"No data available for {chart_type}")
            return
        
        st.subheader(f"📈 Interactive {chart_type} Analysis")
        
        # Date filter
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            min_date = df['Date'].min().date()
            max_date = df['Date'].max().date()
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
            with col2:
                end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
            
            # Filter data
            mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
            filtered_df = df.loc[mask]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            st.warning("No data available for selected date range")
            return
        
        # Create charts based on type
        if chart_type == "KML Tracking":
            self._create_kml_interactive_charts(filtered_df)
        elif chart_type == "Plantation Records":
            self._create_plantation_interactive_charts(filtered_df)
    
    def _create_kml_interactive_charts(self, df: pd.DataFrame):
        """Create interactive KML charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily KML count
            daily_kml = df.groupby(df['Date'].dt.date)['KML_Count_Sent'].sum().reset_index()
            fig1 = px.line(daily_kml, x='Date', y='KML_Count_Sent', 
                          title='Daily KML Files Sent',
                          color_discrete_sequence=[self.colors['primary']])
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Area efficiency
            df['Approval_Rate'] = (df['Area_Approved'] / df['Total_Area'] * 100).fillna(0)
            fig2 = px.scatter(df, x='Total_Area', y='Area_Approved', 
                             size='KML_Count_Sent', color='Status',
                             title='Area Sent vs Approved',
                             hover_data=['Date', 'User'])
            st.plotly_chart(fig2, use_container_width=True)
        
        # Status distribution
        status_count = df['Status'].value_counts()
        fig3 = px.pie(values=status_count.values, names=status_count.index,
                     title='KML Status Distribution',
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig3, use_container_width=True)
    
    def _create_plantation_interactive_charts(self, df: pd.DataFrame):
        """Create interactive plantation charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily plantation area
            daily_plantation = df.groupby(df['Date'].dt.date)['Area_Planted'].sum().reset_index()
            fig1 = px.bar(daily_plantation, x='Date', y='Area_Planted',
                         title='Daily Plantation Area',
                         color_discrete_sequence=[self.colors['accent']])
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Trees vs Area efficiency
            fig2 = px.scatter(df, x='Area_Planted', y='Trees_Planted',
                             size='Farmer_Covered', color='Status',
                             title='Trees Planted vs Area Efficiency',
                             hover_data=['Date', 'Plot_Code'])
            st.plotly_chart(fig2, use_container_width=True)
        
        # Monthly summary
        df['Month'] = df['Date'].dt.to_period('M')
        monthly_summary = df.groupby('Month').agg({
            'Area_Planted': 'sum',
            'Trees_Planted': 'sum',
            'Farmer_Covered': 'sum'
        }).reset_index()
        monthly_summary['Month'] = monthly_summary['Month'].astype(str)
        
        fig3 = px.line(monthly_summary, x='Month', y=['Area_Planted', 'Trees_Planted'],
                      title='Monthly Plantation Trends')
        st.plotly_chart(fig3, use_container_width=True) 