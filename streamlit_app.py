#!/usr/bin/env python3
"""
AI TRADING DASHBOARD v3.0 - Streamlit Cloud Deployment Entry Point
This wrapper properly imports and runs the main trading dashboard
"""

import sys
import os
from pathlib import Path

# Setup Python path
root_dir = Path(__file__).parent
ai_trading_dir = root_dir / "ai_trading_system"
sys.path.insert(0, str(ai_trading_dir))
sys.path.insert(0, str(root_dir))

# Now execute the main app
if __name__ == "__main__":
    # Import required modules
    import importlib.util
    
    # Load app_advanced_v3.py as a module
    app_path = ai_trading_dir / "app_advanced_v3.py"
    spec = importlib.util.spec_from_file_location("app_advanced_v3", app_path)
    app_module = importlib.util.module_from_spec(spec)
    sys.modules["app_advanced_v3"] = app_module
    spec.loader.exec_module(app_module)
"""
Main Streamlit app entry point - AI Trading Dashboard v3.0
Deployment wrapper for Streamlit Cloud
"""

import sys
import os
from pathlib import Path

# Add ai_trading_system directory to Python path
ai_trading_path = Path(__file__).parent / "ai_trading_system"
sys.path.insert(0, str(ai_trading_path))

# Now run app_advanced_v3 with proper context
if __name__ == "__main__":
    import streamlit as st
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from database import get_engine
    import sqlalchemy
    import ta
    from advanced_analysis import AdvancedAnalyzer
    from recommendation import StockRecommender
    from datetime import datetime, timedelta
    import json
    
    # Execute app_advanced_v3.py content inline
    exec(open(str(ai_trading_path / "app_advanced_v3.py")).read())

