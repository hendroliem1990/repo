import os

START_DATE = "2000-01-01"

# Dynamic database path based on current working directory
current_dir = os.getcwd()
if 'ai_trading_system' in current_dir:
    # Running from ai_trading_system directory
    DB_PATH = "sqlite:///market.db"
else:
    # Running from root directory (Streamlit Cloud)
    DB_PATH = "sqlite:///ai_trading_system/market.db"