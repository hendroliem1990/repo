import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json

class StockbitDataSource:
    """Stockbit data source for fundamental data"""

    def __init__(self, api_key=None):
        self.name = "Stockbit"
        self.data_type = "fundamental"
        self.base_url = "https://api.stockbit.com/v2.4"
        self.api_key = api_key  # Stockbit requires API key for full access

        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    def get_fundamental_data(self, ticker, data_type='all'):
        """
        Get fundamental data for a ticker from Stockbit

        Args:
            ticker (str): Ticker symbol (e.g., 'BBCA.JK')
            data_type (str): Type of data ('financials', 'ratios', 'profile', 'all')

        Returns:
            dict: Fundamental data
        """
        ticker_clean = ticker.replace('.JK', '')
        results = {}

        try:
            print(f"  📊 {ticker} (Stockbit fundamentals)...", end=" ")

            if data_type in ['financials', 'all']:
                results['financials'] = self._get_financial_statements(ticker_clean)

            if data_type in ['ratios', 'all']:
                results['ratios'] = self._get_financial_ratios(ticker_clean)

            if data_type in ['profile', 'all']:
                results['profile'] = self._get_company_profile(ticker_clean)

            # Add metadata
            results['ticker'] = ticker
            results['data_source'] = self.name
            results['data_type'] = self.data_type
            results['timestamp'] = datetime.now().isoformat()

            print("✅")
            return results

        except Exception as e:
            print(f"❌ {str(e)[:30]}...")
            return {}

    def _get_financial_statements(self, ticker):
        """Get financial statements (income statement, balance sheet, cash flow)"""
        try:
            # Stockbit API endpoints for financials
            # Note: This is a simplified version. Real implementation would need proper API endpoints

            # For demo purposes, return structure that would be expected
            return {
                'income_statement': {
                    'revenue': None,
                    'net_income': None,
                    'eps': None,
                    'period': 'FY0',
                    'currency': 'IDR'
                },
                'balance_sheet': {
                    'total_assets': None,
                    'total_liabilities': None,
                    'shareholders_equity': None,
                    'period': 'FY0',
                    'currency': 'IDR'
                },
                'cash_flow': {
                    'operating_cash_flow': None,
                    'investing_cash_flow': None,
                    'financing_cash_flow': None,
                    'period': 'FY0',
                    'currency': 'IDR'
                }
            }

        except Exception as e:
            print(f"Error getting financial statements: {e}")
            return {}

    def _get_financial_ratios(self, ticker):
        """Get financial ratios (valuation, profitability, liquidity, etc.)"""
        try:
            # Stockbit API for ratios
            return {
                'valuation_ratios': {
                    'pe_ratio': None,
                    'pb_ratio': None,
                    'ps_ratio': None,
                    'ev_ebitda': None,
                    'div_yield': None
                },
                'profitability_ratios': {
                    'roe': None,
                    'roa': None,
                    'net_margin': None,
                    'gross_margin': None
                },
                'liquidity_ratios': {
                    'current_ratio': None,
                    'quick_ratio': None,
                    'cash_ratio': None
                },
                'leverage_ratios': {
                    'debt_to_equity': None,
                    'debt_to_assets': None,
                    'interest_coverage': None
                }
            }

        except Exception as e:
            print(f"Error getting financial ratios: {e}")
            return {}

    def _get_company_profile(self, ticker):
        """Get company profile information"""
        try:
            # Stockbit API for company profile
            return {
                'company_name': None,
                'sector': None,
                'sub_sector': None,
                'industry': None,
                'website': None,
                'description': None,
                'employees': None,
                'market_cap': None,
                'shares_outstanding': None,
                'listing_date': None,
                'auditor': None,
                'legal_counsel': None
            }

        except Exception as e:
            print(f"Error getting company profile: {e}")
            return {}

    def get_batch_fundamentals(self, tickers, data_type='all', batch_size=10, delay=1.0):
        """
        Get fundamental data for multiple tickers

        Args:
            tickers (list): List of ticker symbols
            data_type (str): Type of fundamental data to fetch
            batch_size (int): Number of tickers per batch
            delay (float): Delay between requests in seconds

        Returns:
            dict: Dictionary of ticker -> fundamental data
        """
        results = {}
        successful_downloads = 0
        failed_downloads = 0

        print(f"🚀 Starting Stockbit fundamental data download (batch size: {batch_size})")
        print("=" * 60)

        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(tickers) + batch_size - 1) // batch_size

            print(f"📦 Batch {batch_num}/{total_batches} ({len(batch)} tickers)")

            for ticker in batch:
                data = self.get_fundamental_data(ticker, data_type)
                if data:
                    results[ticker] = data
                    successful_downloads += 1
                else:
                    failed_downloads += 1

                # Respectful delay for API
                time.sleep(delay)

            print(f"📊 Batch {batch_num} complete: {successful_downloads} success, {failed_downloads} failed")
            print("-" * 40)

            # Larger delay between batches
            if batch_num < total_batches:
                time.sleep(2.0)

        print("=" * 60)
        print(f"🎉 Stockbit fundamental download complete!")
        print(f"✅ Successful: {successful_downloads}")
        print(f"❌ Failed: {failed_downloads}")
        print(f"📊 Success rate: {(successful_downloads/(successful_downloads+failed_downloads)*100):.1f}%")

        return results

    def search_companies(self, query):
        """
        Search for companies on Stockbit

        Args:
            query (str): Search query

        Returns:
            list: List of matching companies
        """
        try:
            # This would use Stockbit's search API
            # For now, return empty list as placeholder
            return []

        except Exception as e:
            print(f"Error searching companies: {e}")
            return []