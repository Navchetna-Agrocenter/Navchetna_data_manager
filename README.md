# 🌱 Plantation Data Management System

A comprehensive Streamlit web application for managing plantation data, KML tracking, and spatial analysis for Navchetna Spatial Solutions.

## 🎯 Overview

This system is designed for companies engaged in plantation activities to track and manage:
- KML file submissions and approvals
- Daily plantation activities and progress
- Multi-project management with role-based access
- Interactive analytics and reporting
- SharePoint integration for data storage
- Google Sheets integration for persistent storage

## ✨ Features

### 📊 **Dashboard & Analytics**
- Real-time KPI metrics and progress tracking
- Interactive charts and visualizations
- Daily, weekly, and monthly trend analysis
- Project comparison and overview charts
- Exportable reports and data

### 🏗️ **Project Management**
- Multiple project support (MakeMyTrip, Absolute, etc.)
- Project-specific data isolation
- Progress tracking against targets
- Status monitoring and reporting

### 📋 **Data Management**
- KML tracking (count, area, approval status)
- Plantation records (area planted, trees, farmers)
- Daily data entry forms
- CRUD operations with validation
- Automated data backups

### 👥 **User Management**
- Role-based access control (Admin, Project Manager, Viewer)
- Project-specific permissions
- Secure authentication system
- User activity tracking

### ☁️ **Storage Options**
- Google Sheets integration for persistent cloud storage
- SharePoint integration with Teams support
- Local storage for offline development
- Session state for stateless deployments
- Excel/CSV file format

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or Download the project**
   ```bash
   git clone <repository-url>
   cd navchetna_data_analysis_webapp
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   streamlit run app.py
   ```

4. **Access the Application**
   Open your browser and go to: `http://localhost:8501`

## 🔐 Demo Credentials

### Administrator
- **Username:** admin
- **Password:** admin123
- **Access:** Full system access, user management, all projects

### Project Manager (MakeMyTrip)
- **Username:** manager1  
- **Password:** manager123
- **Access:** MakeMyTrip project data only

### Project Manager (Absolute)
- **Username:** manager2
- **Password:** manager123  
- **Access:** Absolute project data only

### Viewer
- **Username:** viewer
- **Password:** viewer123
- **Access:** Read-only access to all projects

## 📁 Project Structure

```
navchetna_data_analysis_webapp/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── utils/                      # Utility modules
│   ├── __init__.py
│   ├── sharepoint_manager.py   # SharePoint integration
│   ├── gsheets_manager.py      # Google Sheets integration
│   ├── auth_manager.py         # Authentication system
│   └── data_manager.py         # Data operations
├── components/                 # UI components
│   ├── __init__.py
│   └── charts.py              # Chart and visualization components
└── local_data/                # Local storage (created automatically)
    ├── projects/              # Project-specific data
    ├── master_data/           # User and project configuration
    └── reports/               # Generated reports
```

## 🎨 User Interface

### 🏠 Dashboard
- Overall performance metrics
- Project overview charts
- Today's activity summary
- Quick access to all features

### 📈 Project Details
- Project-specific KPIs
- Daily trend analysis
- Weekly performance comparison
- Interactive data filtering

### ➕ Data Entry
- KML tracking forms
- Plantation record forms
- Validation and error handling
- Real-time data updates

### 👥 Administration
- User management (Admin only)
- Project creation and management
- Role and permission assignment
- System configuration

## 📊 Data Structure

### KML Tracking Data
- Date, User, KML Count Sent
- Total Area, Area Approved
- Approval Date, Status, Remarks

### Plantation Records
- Date, User, Plot Code
- Area Planted, Trees Planted
- Farmers Covered, Status

### Project Information
- Project ID, Name, Description
- Target Area, Start Date
- Assigned Users, Manager, Status

## 🔧 Configuration

### Google Sheets Setup (Recommended)
1. Create a Google Cloud project
2. Enable Google Sheets API and Google Drive API
3. Create a service account with appropriate permissions
4. Download the service account credentials JSON file
5. Add the credentials to your Streamlit app:

   **Option 1:** Rename the downloaded JSON file to `service_account.json` and place it in the root directory of your app.

   **Option 2:** For Streamlit Cloud, add the credentials as a secret named `gcp_service_account` in your Streamlit dashboard.

   **Option 3:** Set the environment variable `GOOGLE_SHEETS_CREDS` with the contents of the JSON file.

### SharePoint Setup (Alternative)
1. Create Azure App Registration
2. Configure SharePoint permissions
3. Update `config.py` with credentials:
   ```python
   SHAREPOINT_CONFIG = {
       'site_url': 'your-sharepoint-site',
       'client_id': 'your-client-id',
       'client_secret': 'your-client-secret',
       'tenant_id': 'your-tenant-id'
   }
   ```

### Local Development
- Application runs in offline mode by default
- Data stored in `local_data/` directory
- No SharePoint configuration required for testing

### GitHub Deployment
- Application can run directly from GitHub
- Data is stored in session state for the current session
- Perfect for demos and presentations without need for persistence
- Automatic detection of GitHub deployment environment

## 📱 Usage Scenarios

### Daily Team Meeting
1. Login with appropriate credentials
2. Navigate to Dashboard for overall metrics
3. Check today's activity summary
4. Review project-specific progress

### Data Entry
1. Select "Add Data" from navigation
2. Choose project and data type
3. Fill in the form with daily activities
4. Submit and verify data saved

### Monthly Reporting
1. Go to Projects Overview
2. Select date range and projects
3. Generate comparison charts
4. Export data for presentations

### Project Management
1. Admin access required
2. Create new projects
3. Assign users and set permissions
4. Monitor overall progress

## 🛡️ Security Features

- Password hashing (SHA-256)
- Session-based authentication
- Role-based access control
- Project-level data isolation
- Input validation and sanitization

## 🔄 Data Flow

1. **User Authentication** → Role verification → Project access
2. **Data Entry** → Validation → Storage (Google Sheets/SharePoint/Local) → Visualization
3. **Data Retrieval** → Storage → Processing → Visualization
4. **Reporting** → Data aggregation → Chart generation → Export

## 🚀 Deployment Options

### Google Sheets Deployment (Recommended)
1. **Setup Google Cloud**:
   - Create a project in Google Cloud Console
   - Enable Google Sheets and Drive APIs
   - Create service account credentials
   - Download credentials JSON file

2. **Configure Streamlit Cloud**:
   - Add Google credentials as Streamlit secrets
   - Deploy to Streamlit Cloud from GitHub
   - Data is persisted in Google Sheets across sessions

3. **Access and benefits**:
   - Full data persistence across sessions
   - No database setup required
   - Spreadsheet-based storage for easy manual access
   - Real-time collaboration on data

### GitHub Deployment
1. **Fork the repository** to your GitHub account
2. **Setup Streamlit Community Cloud**:
   - Connect your GitHub account to [Streamlit Community Cloud](https://streamlit.io/cloud)
   - Select your forked repository
   - Set the main file path as `app.py`
   - Deploy the application
3. **Access your application**:
   - The app will be available at a URL like: `https://yourusername-yourappname.streamlit.app`
   - Data will be stored in session state during the active session
   - Perfect for demos and presentations

### Cloud Deployment (Production)
- Streamlit Cloud
- Heroku
- AWS/Azure/Google Cloud
- SharePoint integration required

### Local Network
- Company server deployment
- Intranet access only
- Local file storage option

## 🔧 Troubleshooting

### Common Issues

1. **Login Problems**
   - Check credentials against demo accounts
   - Clear browser cache and session

2. **Data Not Saving**
   - Verify write permissions
   - Check local storage directory
   - For GitHub deployment, data only persists during the active session
   - For Google Sheets, check API permissions and credentials
   - Restart application

3. **Charts Not Loading**
   - Ensure sample data is generated
   - Check browser console for errors
   - Verify pandas/plotly installation

4. **SharePoint Connectivity**
   - Verify network connectivity
   - Check Azure credentials
   - Test with offline mode first

## 📈 Future Enhancements

- Mobile-responsive design
- Advanced analytics and ML predictions
- Real-time collaboration features
- Integration with GIS systems
- Automated report scheduling
- REST API for external integrations

## 💡 Support

For technical support or feature requests:
- Review this documentation
- Check the troubleshooting section
- Contact system administrator

## 📄 License

This project is developed for Navchetna Spatial Solutions. All rights reserved.

---

**Built with ❤️ using Streamlit, Pandas, and Plotly**

🌱 *Empowering sustainable plantation management through data analytics* 