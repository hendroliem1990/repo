#!/usr/bin/env python3
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
sys.path.insert(0, str(Path(__file__).parent))

# Now run app_advanced_v3 with proper context
if __name__ == "__main__":
    import streamlit as st
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import sqlalchemy
    import ta
    from datetime import datetime, timedelta
    import json
    
    # Import from ai_trading_system modules
    from ai_trading_system.database import get_engine
    from ai_trading_system.advanced_analysis import AdvancedAnalyzer
    from ai_trading_system.recommendation import StockRecommender
    
    # Execute app_advanced_v3.py content inline
    exec(open(str(ai_trading_path / "app_advanced_v3.py")).read())

