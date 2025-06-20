# -*- coding: utf-8 -*-
"""
MongoDB-based Streamlit Application for Plantation Data Management System
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Navchetna Plantation Data Manager - MongoDB",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Main title
st.title("🌱 Navchetna Plantation Data Management System")
st.markdown("### MongoDB Version - Dynamic Schema Management")

# Initialize MongoDB manager
try:
    import config
    from utils.mongodb_manager import MongoDBManager
    
    db_manager = MongoDBManager()
    
    # Display connection status
    if db_manager.is_online:
        st.sidebar.success("✅ Connected to MongoDB")
        st.success("Successfully connected to MongoDB!")
    else:
        st.sidebar.warning("⚠️ Using local storage fallback")
        st.warning("Could not connect to MongoDB. Using local storage fallback.")
        
except Exception as e:
    st.sidebar.error(f"❌ Error initializing MongoDB: {str(e)}")
    st.error(f"Error initializing MongoDB manager: {str(e)}")
    db_manager = None

# Show MongoDB features
if db_manager:
    st.subheader("MongoDB Features Available:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**✅ Dynamic Schema Management**")
        st.write("Create and modify table schemas on the fly")
    
    with col2:
        st.markdown("**✅ Project-based Collections**") 
        st.write("Data organized by projects with automatic naming")
    
    with col3:
        st.markdown("**✅ Local Fallback**")
        st.write("Seamless fallback to local storage when offline")
    
    # Test MongoDB operations
    st.subheader("Test MongoDB Operations")
    
    if st.button("Test Database Connection"):
        try:
            # Test writing data
            test_data = pd.DataFrame({
                'test_field': ['value1', 'value2'],
                'timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * 2
            })
            
            if db_manager.write_dataframe('test_project', 'test_collection', test_data):
                st.success("✅ Successfully wrote test data to MongoDB")
                
                # Test reading data
                read_data = db_manager.read_dataframe('test_project', 'test_collection')
                if not read_data.empty:
                    st.success("✅ Successfully read test data from MongoDB")
                    st.dataframe(read_data)
                else:
                    st.warning("⚠️ Could not read data back from MongoDB")
            else:
                st.error("❌ Failed to write test data to MongoDB")
                
        except Exception as e:
            st.error(f"Error testing MongoDB: {str(e)}")
    
    # Show collections
    st.subheader("Database Collections")
    try:
        collections = db_manager.get_all_collections()
        if collections:
            st.write(f"Found {len(collections)} collections:")
            for collection in collections:
                st.write(f"- {collection}")
        else:
            st.info("No collections found in the database")
    except Exception as e:
        st.error(f"Error getting collections: {str(e)}")

else:
    st.error("MongoDB manager not initialized. Please check your configuration.")
    
    # Show configuration help
    st.subheader("MongoDB Configuration Help")
    st.write("To use MongoDB, you need to:")
    st.write("1. Install MongoDB Python packages: `pip install pymongo dnspython`")
    st.write("2. Set up your MongoDB connection string in config.py")
    st.write("3. Ensure your MongoDB instance is running and accessible")
    
    st.code("""
# Example MongoDB configuration in config.py
MONGODB_CONFIG = {
    'connection_string': 'mongodb://localhost:27017/',
    'database_name': 'navchetna_plantation',
    'timeout': 5000
}
""")

# Footer
st.markdown("---")
st.markdown("**Note:** This is the MongoDB version of the Navchetna Plantation Data Management System. It provides dynamic schema management and scalable data storage.")
