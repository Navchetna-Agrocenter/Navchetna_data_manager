# Navchetna Plantation Data Management System - MongoDB Version

## 🌟 Complete Production-Ready System

This is the complete MongoDB-powered version of the Navchetna Plantation Data Management System, designed to handle unlimited data growth with dynamic table creation and management.

## 🚀 Quick Start

### Option 1: Using Batch File (Windows)
```bash
# Double-click or run in terminal
run_mongodb_app.bat
```

### Option 2: Manual Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app_mongodb.py
```

### Option 3: Python Module
```bash
python -m streamlit run app_mongodb.py
```

## 🔐 Default Login
- **Username:** admin
- **Password:** admin

## 📊 Key Features

### ✅ Completed Features
1. **Dynamic Table Management**
   - Create, modify, and delete tables without downtime
   - Add/remove fields from existing tables
   - Automatic data consistency across all projects

2. **MongoDB Integration**
   - Scalable database with automatic fallback to local storage
   - Real-time connection monitoring
   - Optimized queries and connection pooling

3. **User Management**
   - Role-based access control (Admin, Project Manager, Viewer)
   - Secure password hashing
   - Project-based permissions

4. **Project Management**
   - Multi-project support with data isolation
   - Project-specific table collections
   - Automatic table initialization

5. **Data Operations**
   - Add, edit, delete records
   - Real-time data validation
   - Bulk operations support

6. **Analytics & Reporting**
   - Dashboard with key metrics
   - Project-wise data analysis
   - Export capabilities

## 🏗️ System Architecture

```
Frontend (Streamlit) → Backend (Python) → Database (MongoDB/Local)
                    ↓
            Table Manager → Dynamic Schema
                    ↓
            Auth Manager → User Security
```

### Database Structure
- **Global Collections:**
  - `users` - User accounts and permissions
  - `projects` - Project definitions
  - `tables` - Table schemas and definitions
  - `schema_extensions` - Dynamic field extensions

- **Project-Specific Collections:**
  - `{project_name}_kml_tracking`
  - `{project_name}_plantation_records`
  - `{project_name}_{custom_table_name}`

## 📁 File Structure

```
navchetna_data_analysis_webapp/
├── app_mongodb.py              # Main MongoDB application
├── mongodb_app.py              # Testing interface
├── run_mongodb_app.bat         # Windows startup script
├── requirements.txt            # Python dependencies
├── config.py                   # Configuration settings
├── utils/
│   ├── mongodb_manager.py      # Database operations
│   ├── table_manager.py        # Dynamic table management
│   ├── auth_manager.py         # Authentication
│   └── data_manager.py         # Data operations
├── components/
│   └── charts.py              # Visualization components
└── docs/
    ├── README_MongoDB.md       # MongoDB setup guide
    └── IMPLEMENTATION_SUMMARY.md # Technical details
```

## 🔧 Configuration

### MongoDB Connection (config.py)
```python
MONGODB_CONFIG = {
    'connection_string': 'mongodb://localhost:27017/',
    'database_name': 'navchetna_plantation',
    'timeout_ms': 5000,
    'retry_attempts': 3
}
```

### Local Storage Fallback
If MongoDB is unavailable, the system automatically falls back to local CSV files in the `local_data/` directory.

## 👥 User Roles & Permissions

### Admin
- Full system access
- User management
- Project creation/deletion
- Schema management
- All data operations

### Project Manager
- Access to assigned projects
- Data entry and editing
- View analytics and reports
- Manage records within projects

### Viewer
- Read-only access to assigned projects
- View data and analytics
- Generate reports

## 📊 Available Tables

### Default System Tables
1. **KML Tracking**
   - Date, User, KML_Count_Sent
   - Total_Area, Area_Approved
   - Approval_Date, Status, Remarks

2. **Plantation Records**
   - Date, User, Plot_Code
   - Area_Planted, Farmer_Covered
   - Trees_Planted, Pits_Dug, Status

### Custom Tables
- Create unlimited custom tables
- Define fields with various data types
- Automatic integration across all projects

## 🔄 Data Operations

### Adding Data
1. Select project from dropdown
2. Choose table type
3. Fill dynamic form based on table schema
4. Data automatically saved with user info

### Managing Records
1. View all records in tabular format
2. Edit individual records
3. Delete records with confirmation
4. Bulk operations available

### Schema Management
1. Add new fields to existing tables
2. Modify field properties
3. Create entirely new table types
4. Changes apply across all projects

## 📈 Analytics Features

### Dashboard Metrics
- Total projects and active status
- Area planted vs. target metrics
- Trees planted statistics
- Recent activity tracking

### Project Analytics
- Project-specific KPIs
- Progress tracking
- Comparative analysis
- Export to Excel/CSV

## 🛠️ Troubleshooting

### MongoDB Connection Issues
1. Check if MongoDB service is running
2. Verify connection string in config.py
3. System will automatically use local storage fallback

### Performance Optimization
1. MongoDB connection pooling enabled
2. Data caching for frequently accessed tables
3. Optimized queries with proper indexing

### Common Issues
- **Import errors:** Run `pip install -r requirements.txt`
- **Permission errors:** Check user role assignments
- **Data not saving:** Verify MongoDB connection or check local storage permissions

## 🔒 Security Features

- Password hashing with secure algorithms
- Session-based authentication
- Role-based access control
- Input validation and sanitization
- Secure database connections

## 📦 Deployment

### Development
```bash
streamlit run app_mongodb.py
```

### Production
1. Set up MongoDB cluster
2. Update connection string in config.py
3. Configure environment variables
4. Use production WSGI server

## 🔄 Backup & Recovery

### MongoDB Backup
```bash
mongodump --db navchetna_plantation --out backup/
```

### Local Storage Backup
All CSV files in `local_data/` directory are automatically backed up.

## 📞 Support

For technical support or feature requests:
1. Check the troubleshooting section
2. Review the MongoDB setup guide
3. Contact the development team

## 🎯 Future Enhancements

- Advanced analytics with machine learning
- Mobile app integration
- Real-time collaboration features
- Advanced reporting with custom templates
- Integration with GIS systems

---

**Version:** 2.0 MongoDB Complete
**Last Updated:** December 2024
**Status:** Production Ready ✅ 