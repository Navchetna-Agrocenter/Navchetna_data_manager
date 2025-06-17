@echo off
echo Starting Navchetna Plantation Data Management System - MongoDB Version
echo.
echo Checking requirements...
pip install -r requirements.txt
echo.
echo Starting Streamlit application...
echo Open your browser to: http://localhost:8501
echo.
streamlit run main_mongodb.py 