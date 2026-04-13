#!/usr/bin/env python3
"""
AI Trading System - Main Streamlit App
This file serves as the entry point for Streamlit Cloud deployment.
"""

import sys
import os

# Add ai_trading_system to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_trading_system'))

# Import and run the main app
from app import *