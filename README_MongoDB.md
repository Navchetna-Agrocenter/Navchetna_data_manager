# Navchetna Plantation Data Management System - MongoDB Version

## Overview

This MongoDB-powered version of the Navchetna Plantation Data Management System provides a fully dynamic, scalable solution for managing plantation data with real-time schema management capabilities.

## Key Features

### 🚀 Dynamic Schema Management
- Create, modify, and delete tables on the fly
- Add/remove fields without downtime
- Real-time schema updates across all projects
- Support for multiple data types (Text, Number, Date, Boolean, Dropdown)

### 📊 Project-Based Data Organization
- Automatic project-specific collections
- Consistent naming conventions
- Isolated data per project
- Easy project management

### 🔄 Seamless Fallback
- Automatic fallback to local storage when MongoDB is unavailable
- Transparent operation switching
- Data consistency maintained

### 🛡️ User Authentication & Security
- Role-based access control (Admin, Project Manager, Viewer)
- Secure password hashing
- Project-specific permissions
- Session management

## Installation & Setup

### Prerequisites

1. **Python 3.8+**
2. **MongoDB** (local or cloud instance)
3. **Required Python packages:**

```bash
pip install pymongo dnspython streamlit pandas
```

### MongoDB Setup

#### Option 1: Local MongoDB
1. Install MongoDB Community Edition
2. Start MongoDB service:
   ```bash
   mongod --dbpath /path/to/your/data/directory
   ```

#### Option 2: MongoDB Atlas (Cloud)
1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster
3. Get your connection string

### Configuration

Update `config.py` with your MongoDB settings:

```python
# MongoDB Configuration
MONGODB_CONFIG = {
    'connection_string': 'mongodb://localhost:27017/',  # or your Atlas connection string
    'database_name': 'navchetna_plantation',
    'timeout': 5000,
    'max_pool_size': 10,
    'retry_writes': True
}

# Collection naming conventions
COLLECTION_NAMING = {
    'users': 'users',
    'projects': 'projects',
    'tables': 'table_definitions',
    'schema_extensions': 'schema_extensions'
}
```

## Running the Application

### MongoDB Version
```bash
streamlit run mongodb_app.py
```

### Original Version (for comparison)
```bash
streamlit run main.py
```

## Architecture

### Database Structure

```
navchetna_plantation/
├── users                    # User accounts and permissions
├── projects                 # Project definitions
├── table_definitions        # Dynamic table schemas
├── schema_extensions        # Additional field definitions
└── project_collections/     # Project-specific data
    ├── project1_kml_tracking
    ├── project1_plantation_records
    ├── project2_kml_tracking
    └── ...
```

### Core Components

#### 1. MongoDBManager (`utils/mongodb_manager.py`)
- Database connection management
- CRUD operations
- Local storage fallback
- Performance optimization

#### 2. TableManager (`utils/table_manager.py`)
- Dynamic schema management
- Table creation and modification
- Field operations
- Data consistency

#### 3. Authentication System
- User management
- Role-based permissions
- Session handling
- Security features

## Usage Guide

### 1. First Time Setup

1. **Start the application:**
   ```bash
   streamlit run mongodb_app.py
   ```

2. **Login with default admin:**
   - Username: `admin`
   - Password: `admin`

3. **Create your first project:**
   - Go to Project Management
   - Add project details
   - Assign users

### 2. Schema Management

#### Creating Tables
1. Navigate to "Schema Management"
2. Go to "Manage Tables" tab
3. Define table name and fields
4. Specify field types and requirements

#### Adding Fields
1. Select existing table
2. Go to "Add Field" tab
3. Define field properties
4. Field is automatically added to all projects

#### Managing Fields
- Edit existing fields
- Delete unused fields
- Modify field types and requirements

### 3. Data Operations

#### Adding Data
1. Select project
2. Choose table type
3. Fill dynamic form (auto-generated from schema)
4. Submit data

#### Managing Records
1. View existing records
2. Edit individual records
3. Delete records with confirmation
4. Bulk operations

### 4. Analytics & Reporting

- Real-time analytics
- Project comparisons
- Custom date ranges
- Export capabilities

## API Reference

### MongoDBManager Methods

```python
# Connection
db_manager = MongoDBManager(connection_string)
db_manager.is_online  # Check connection status

# Data operations
df = db_manager.read_dataframe(project_name, collection_name)
success = db_manager.write_dataframe(project_name, collection_name, dataframe)
success = db_manager.add_document(project_name, collection_name, document)
success = db_manager.update_document(project_name, collection_name, index, data)
success = db_manager.delete_document(project_name, collection_name, index)

# Collection management
collections = db_manager.get_all_collections()
success = db_manager.delete_collection(project_name, collection_name)
```

### TableManager Methods

```python
# Table operations
tables_df = table_manager.get_all_tables()
data_df = table_manager.get_table_data(project_name, table_name)

# Schema management
success = table_manager.add_field_to_schema(table_type, field_name, field_type, default_value, is_required, dropdown_options, description)
success = table_manager.create_new_table(table_name, description, fields)
success = table_manager.delete_custom_table(table_name)

# Record operations
success = table_manager.add_table_record(project_name, table_name, record_data)
success = table_manager.update_table_record(project_name, table_name, record_idx, updated_data)
success = table_manager.delete_table_record(project_name, table_name, record_idx)
```

## Performance Considerations

### Optimization Features
- Connection pooling
- Automatic retry logic
- Caching for frequently accessed data
- Efficient query patterns
- Batch operations support

### Scaling Recommendations
- Use MongoDB Atlas for production
- Implement proper indexing
- Monitor query performance
- Consider sharding for large datasets

## Troubleshooting

### Common Issues

#### 1. Connection Failed
```
Error: Could not connect to MongoDB
```
**Solutions:**
- Check MongoDB service is running
- Verify connection string
- Check network connectivity
- Ensure authentication credentials

#### 2. Import Errors
```
ModuleNotFoundError: No module named 'pymongo'
```
**Solution:**
```bash
pip install pymongo dnspython
```

#### 3. Permission Denied
```
Error: Authentication failed
```
**Solutions:**
- Check MongoDB user permissions
- Verify database access rights
- Update connection string with credentials

### Debug Mode

Enable debug logging in `config.py`:

```python
DEBUG_MODE = True
LOGGING_LEVEL = 'DEBUG'
```

## Migration from File-Based System

### Automatic Migration
The system automatically detects existing file-based data and offers migration options:

1. **Data Import:** Existing Excel files are imported into MongoDB
2. **Schema Detection:** Table schemas are automatically detected
3. **User Migration:** User accounts are transferred
4. **Project Setup:** Projects are recreated in MongoDB

### Manual Migration
For custom migration needs:

```python
from utils.mongodb_manager import MongoDBManager
from utils.migration_tools import migrate_project_data

db_manager = MongoDBManager()
migrate_project_data('project_name', source_path, db_manager)
```

## Security Best Practices

### Database Security
- Use authentication in production
- Enable SSL/TLS encryption
- Implement network security
- Regular security updates

### Application Security
- Strong password policies
- Session timeout
- Input validation
- SQL injection prevention

## Contributing

### Development Setup
1. Clone repository
2. Install dependencies
3. Set up development MongoDB instance
4. Run tests
5. Submit pull requests

### Code Standards
- Follow PEP 8
- Add docstrings
- Include unit tests
- Update documentation

## Support

For issues and questions:
- Create GitHub issues
- Check documentation
- Review troubleshooting guide
- Contact development team

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note:** This MongoDB version provides enhanced scalability and dynamic schema management compared to the file-based system. It's recommended for production deployments and growing datasets. 