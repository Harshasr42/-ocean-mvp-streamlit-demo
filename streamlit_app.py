"""
Streamlit App for Ocean MVP - Main Entry Point
This is the main file that Streamlit Cloud will use to deploy the application.
"""

import streamlit as st
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the mobile app
from mobile_app import main

if __name__ == "__main__":
    main()
