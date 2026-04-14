"""
Data Sources Package

This package provides modular access to various financial data sources:
- Yahoo Finance: Price data with technical indicators
- IDX: Ticker lists and corporate actions
- Stockbit: Fundamental data
- Premium sources: Refinitiv, Bloomberg, Polygon, Tiingo
"""

from .yahoo_data import YahooDataSource
from .idx_data import IDXDataSource
from .stockbit_data import StockbitDataSource
from .premium_data import PremiumDataSource
from .data_manager import DataManager

__all__ = [
    'YahooDataSource',
    'IDXDataSource',
    'StockbitDataSource',
    'PremiumDataSource',
    'DataManager'
]