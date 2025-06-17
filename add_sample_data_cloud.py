#!/usr/bin/env python3
"""
Add comprehensive sample data to MongoDB for demonstration
Run this script to populate your cloud deployment with realistic data
"""

import os
import sys
from datetime import datetime, timedelta
import random
from pymongo import MongoClient
import pandas as pd

# MongoDB connection
MONGODB_URI = "mongodb+srv://ojeshshri208:5xC7iUqZAW4EshV2@cluster0.zonvcv8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "plantation_management"

def connect_to_mongodb():
    """Connect to MongoDB"""
    try:
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        return db
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return None

def add_projects(db):
    """Add sample projects"""
    projects = [
        {
            "project_id": "MMT_2024",
            "project_name": "MakeMyTrip Sustainability Initiative",
            "client": "MakeMyTrip",
            "start_date": datetime(2024, 1, 15),
            "end_date": datetime(2024, 12, 31),
            "target_area": 500.0,
            "target_trees": 25000,
            "status": "Active",
            "location": "Maharashtra, India",
            "project_manager": "Rajesh Kumar",
            "budget": 2500000,
            "created_date": datetime(2024, 1, 10)
        },
        {
            "project_id": "ABS_2024",
            "project_name": "Absolute Carbon Offset Program",
            "client": "Absolute Solutions",
            "start_date": datetime(2024, 2, 1),
            "end_date": datetime(2025, 1, 31),
            "target_area": 750.0,
            "target_trees": 37500,
            "status": "Active",
            "location": "Karnataka, India",
            "project_manager": "Priya Sharma",
            "budget": 3750000,
            "created_date": datetime(2024, 1, 25)
        },
        {
            "project_id": "ECO_2024",
            "project_name": "EcoTech Reforestation Drive",
            "client": "EcoTech Industries",
            "start_date": datetime(2024, 3, 1),
            "end_date": datetime(2024, 11, 30),
            "target_area": 300.0,
            "target_trees": 15000,
            "status": "Planning",
            "location": "Tamil Nadu, India",
            "project_manager": "Amit Patel",
            "budget": 1500000,
            "created_date": datetime(2024, 2, 15)
        }
    ]
    
    try:
        db.projects.delete_many({})  # Clear existing data
        result = db.projects.insert_many(projects)
        print(f"✅ Added {len(result.inserted_ids)} projects")
        return True
    except Exception as e:
        print(f"❌ Error adding projects: {e}")
        return False

def add_kml_data(db):
    """Add sample KML data"""
    kml_records = []
    
    # Generate 45 days of KML data for multiple projects
    start_date = datetime.now() - timedelta(days=45)
    
    for i in range(45):
        current_date = start_date + timedelta(days=i)
        
        # MakeMyTrip project data
        if i < 40:  # Active for 40 days
            kml_records.append({
                "project_id": "MMT_2024",
                "submission_date": current_date,
                "area_submitted": round(random.uniform(8, 15), 2),
                "area_approved": round(random.uniform(6, 12), 2),
                "coordinates": f"19.{random.randint(1000, 9999)}, 73.{random.randint(1000, 9999)}",
                "status": random.choice(["Approved", "Pending", "Approved", "Approved"]),
                "surveyor": random.choice(["Rahul Singh", "Deepak Yadav", "Suresh Patil"]),
                "remarks": random.choice(["Good quality land", "Suitable for plantation", "Excellent soil condition", "Ready for planting"])
            })
        
        # Absolute project data
        if i < 35:  # Active for 35 days
            kml_records.append({
                "project_id": "ABS_2024",
                "submission_date": current_date,
                "area_submitted": round(random.uniform(12, 20), 2),
                "area_approved": round(random.uniform(10, 18), 2),
                "coordinates": f"12.{random.randint(1000, 9999)}, 77.{random.randint(1000, 9999)}",
                "status": random.choice(["Approved", "Approved", "Pending", "Approved"]),
                "surveyor": random.choice(["Anita Desai", "Ravi Kumar", "Meera Joshi"]),
                "remarks": random.choice(["Prime location", "High fertility soil", "Water source nearby", "Ideal for afforestation"])
            })
        
        # EcoTech project data (less frequent)
        if i < 20 and i % 3 == 0:  # Every 3rd day for 20 days
            kml_records.append({
                "project_id": "ECO_2024",
                "submission_date": current_date,
                "area_submitted": round(random.uniform(5, 12), 2),
                "area_approved": round(random.uniform(4, 10), 2),
                "coordinates": f"11.{random.randint(1000, 9999)}, 78.{random.randint(1000, 9999)}",
                "status": random.choice(["Approved", "Pending", "Approved"]),
                "surveyor": random.choice(["Karthik Raj", "Lakshmi Devi"]),
                "remarks": random.choice(["Moderate soil quality", "Requires soil treatment", "Good drainage"])
            })
    
    try:
        db.kml_data.delete_many({})  # Clear existing data
        result = db.kml_data.insert_many(kml_records)
        print(f"✅ Added {len(result.inserted_ids)} KML records")
        return True
    except Exception as e:
        print(f"❌ Error adding KML data: {e}")
        return False

def add_plantation_data(db):
    """Add sample plantation data"""
    plantation_records = []
    
    # Generate plantation data based on approved KML data
    start_date = datetime.now() - timedelta(days=40)
    
    for i in range(40):
        current_date = start_date + timedelta(days=i)
        
        # MakeMyTrip plantation data
        if i < 35:
            plantation_records.append({
                "project_id": "MMT_2024",
                "plantation_date": current_date,
                "area_planted": round(random.uniform(5, 10), 2),
                "trees_planted": random.randint(250, 500),
                "tree_species": random.choice(["Neem", "Banyan", "Peepal", "Mango", "Teak", "Eucalyptus"]),
                "survival_rate": round(random.uniform(85, 95), 1),
                "plantation_team": random.choice(["Team Alpha", "Team Beta", "Team Gamma"]),
                "weather_condition": random.choice(["Sunny", "Cloudy", "Light Rain", "Overcast"]),
                "soil_preparation": random.choice(["Complete", "Partial", "Complete"]),
                "irrigation_setup": random.choice(["Drip", "Sprinkler", "Manual", "Drip"]),
                "location_details": f"Plot {random.randint(1, 50)}, Sector {random.randint(1, 10)}"
            })
        
        # Absolute plantation data
        if i < 30:
            plantation_records.append({
                "project_id": "ABS_2024",
                "plantation_date": current_date,
                "area_planted": round(random.uniform(8, 15), 2),
                "trees_planted": random.randint(400, 750),
                "tree_species": random.choice(["Sandalwood", "Rosewood", "Mahogany", "Bamboo", "Neem", "Gulmohar"]),
                "survival_rate": round(random.uniform(88, 96), 1),
                "plantation_team": random.choice(["Team Delta", "Team Echo", "Team Foxtrot"]),
                "weather_condition": random.choice(["Sunny", "Humid", "Cloudy", "Perfect"]),
                "soil_preparation": "Complete",
                "irrigation_setup": random.choice(["Drip", "Smart Irrigation", "Drip"]),
                "location_details": f"Zone {random.randint(1, 20)}, Block {random.randint(1, 5)}"
            })
        
        # EcoTech plantation data (less frequent)
        if i < 15 and i % 2 == 0:
            plantation_records.append({
                "project_id": "ECO_2024",
                "plantation_date": current_date,
                "area_planted": round(random.uniform(3, 8), 2),
                "trees_planted": random.randint(150, 400),
                "tree_species": random.choice(["Coconut", "Areca", "Jackfruit", "Cashew", "Mango"]),
                "survival_rate": round(random.uniform(80, 90), 1),
                "plantation_team": "Team Golf",
                "weather_condition": random.choice(["Monsoon", "Humid", "Cloudy"]),
                "soil_preparation": random.choice(["Complete", "Partial"]),
                "irrigation_setup": "Manual",
                "location_details": f"Hill {random.randint(1, 10)}, Terrace {random.randint(1, 3)}"
            })
    
    try:
        db.plantation_data.delete_many({})  # Clear existing data
        result = db.plantation_data.insert_many(plantation_records)
        print(f"✅ Added {len(result.inserted_ids)} plantation records")
        return True
    except Exception as e:
        print(f"❌ Error adding plantation data: {e}")
        return False

def add_users(db):
    """Add sample users"""
    users = [
        {
            "username": "admin",
            "password": "admin123",  # In production, this should be hashed
            "role": "admin",
            "full_name": "System Administrator",
            "email": "admin@navchetna.com",
            "created_date": datetime.now() - timedelta(days=60),
            "last_login": datetime.now() - timedelta(hours=2)
        },
        {
            "username": "rajesh.kumar",
            "password": "manager123",
            "role": "project_manager",
            "full_name": "Rajesh Kumar",
            "email": "rajesh@navchetna.com",
            "created_date": datetime.now() - timedelta(days=45),
            "last_login": datetime.now() - timedelta(hours=6)
        },
        {
            "username": "priya.sharma",
            "password": "manager123",
            "role": "project_manager",
            "full_name": "Priya Sharma",
            "email": "priya@navchetna.com",
            "created_date": datetime.now() - timedelta(days=40),
            "last_login": datetime.now() - timedelta(days=1)
        },
        {
            "username": "viewer.demo",
            "password": "viewer123",
            "role": "viewer",
            "full_name": "Demo Viewer",
            "email": "viewer@navchetna.com",
            "created_date": datetime.now() - timedelta(days=30),
            "last_login": datetime.now() - timedelta(hours=12)
        }
    ]
    
    try:
        # Only add users if they don't exist
        for user in users:
            existing = db.users.find_one({"username": user["username"]})
            if not existing:
                db.users.insert_one(user)
        print(f"✅ Added/verified {len(users)} users")
        return True
    except Exception as e:
        print(f"❌ Error adding users: {e}")
        return False

def main():
    """Main function to add all sample data"""
    print("🚀 Adding comprehensive sample data to MongoDB...")
    print("=" * 50)
    
    # Connect to MongoDB
    db = connect_to_mongodb()
    if not db:
        return
    
    # Add all data
    success = True
    success &= add_users(db)
    success &= add_projects(db)
    success &= add_kml_data(db)
    success &= add_plantation_data(db)
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 ALL SAMPLE DATA ADDED SUCCESSFULLY!")
        print("\nYour dashboard now has:")
        print("• 3 Active projects with realistic data")
        print("• 45 days of KML submission history")
        print("• 40 days of plantation activity")
        print("• Multiple user accounts for testing")
        print("• Rich charts and visualizations")
        print("\nLogin credentials:")
        print("• Admin: admin / admin123")
        print("• Manager: rajesh.kumar / manager123")
        print("• Viewer: viewer.demo / viewer123")
        print("\n🚀 Your app is now ready for client presentations!")
    else:
        print("\n❌ Some errors occurred while adding data")

if __name__ == "__main__":
    main() 