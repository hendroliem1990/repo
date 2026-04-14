import pandas as pd
from datetime import datetime
import time

class PremiumDataSource:
    """Premium data sources (Refinitiv, Bloomberg, Polygon, Tiingo)"""

    def __init__(self, provider='polygon', api_key=None):
        self.provider = provider.lower()
        self.api_key = api_key
        self.name = f"{provider.title()} (Premium)"
        self.data_type = "premium"

        # Configure provider-specific settings
        self._configure_provider()

    def _configure_provider(self):
        """Configure provider-specific API settings"""
        if self.provider == 'polygon':
            self.base_url = "https://api.polygon.io"
            self.headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}

        elif self.provider == 'tiingo':
            self.base_url = "https://api.tiingo.com"
            self.headers = {'Authorization': f'Token {self.api_key}'} if self.api_key else {}

        elif self.provider == 'refinitiv':
            self.base_url = "https://api.refinitiv.com"
            # Refinitiv uses OAuth2, more complex setup needed
            self.headers = {}

        elif self.provider == 'bloomberg':
            self.base_url = "https://api.bloomberg.com"
            self.headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def get_price_data(self, ticker, start_date=None, end_date=None):
        """
        Get high-quality price data from premium provider

        Args:
            ticker (str): Ticker symbol
            start_date (str): Start date YYYY-MM-DD
            end_date (str): End date YYYY-MM-DD

        Returns:
            pd.DataFrame: Price data
        """
        try:
            print(f"  💎 {ticker} ({self.provider})...", end=" ")

            if not self.api_key:
                print("❌ No API key")
                return None

            # Provider-specific implementation
            if self.provider == 'polygon':
                return self._get_polygon_data(ticker, start_date, end_date)
            elif self.provider == 'tiingo':
                return self._get_tiingo_data(ticker, start_date, end_date)
            elif self.provider == 'refinitiv':
                return self._get_refinitiv_data(ticker, start_date, end_date)
            elif self.provider == 'bloomberg':
                return self._get_bloomberg_data(ticker, start_date, end_date)
            else:
                print("❌ Unsupported provider")
                return None

        except Exception as e:
            print(f"❌ {str(e)[:30]}...")
            return None

    def _get_polygon_data(self, ticker, start_date, end_date):
        """Get data from Polygon.io"""
        try:
            import requests

            # Convert dates to timestamps
            start_ts = pd.Timestamp(start_date).timestamp() * 1000
            end_ts = pd.Timestamp(end_date).timestamp() * 1000

            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_ts}/{end_ts}"
            params = {'apiKey': self.api_key}

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()

            if 'results' not in data:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data['results'])
            df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
            df = df.set_index('timestamp')

            # Rename columns to standard format
            column_mapping = {
                'o': 'Open',
                'h': 'High',
                'l': 'Low',
                'c': 'Close',
                'v': 'Volume'
            }
            df = df.rename(columns=column_mapping)

            # Add metadata
            df['ticker'] = ticker
            df['data_source'] = self.name

            return df[['Open', 'High', 'Low', 'Close', 'Volume', 'ticker', 'data_source']]

        except Exception as e:
            print(f"Polygon error: {e}")
            return None

    def _get_tiingo_data(self, ticker, start_date, end_date):
        """Get data from Tiingo"""
        try:
            import requests

            url = f"{self.base_url}/tiingo/daily/{ticker}/prices"
            params = {
                'startDate': start_date,
                'endDate': end_date,
                'token': self.api_key
            }

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()

            if not data:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

            # Rename columns
            column_mapping = {
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }
            df = df.rename(columns=column_mapping)

            # Add metadata
            df['ticker'] = ticker
            df['data_source'] = self.name

            return df[['Open', 'High', 'Low', 'Close', 'Volume', 'ticker', 'data_source']]

        except Exception as e:
            print(f"Tiingo error: {e}")
            return None

    def _get_refinitiv_data(self, ticker, start_date, end_date):
        """Get data from Refinitiv (placeholder - requires complex OAuth setup)"""
        print("⚠ Refinitiv integration requires OAuth2 setup")
        return None

    def _get_bloomberg_data(self, ticker, start_date, end_date):
        """Get data from Bloomberg (placeholder)"""
        print("⚠ Bloomberg integration requires enterprise license")
        return None

    def get_fundamental_data(self, ticker):
        """
        Get fundamental data from premium provider

        Args:
            ticker (str): Ticker symbol

        Returns:
            dict: Fundamental data
        """
        try:
            if self.provider == 'polygon':
                return self._get_polygon_fundamentals(ticker)
            elif self.provider == 'tiingo':
                return self._get_tiingo_fundamentals(ticker)
            else:
                return {}

        except Exception as e:
            print(f"Error getting fundamentals: {e}")
            return {}

    def _get_polygon_fundamentals(self, ticker):
        """Get fundamentals from Polygon"""
        try:
            import requests

            # Get basic financials
            url = f"{self.base_url}/vX/reference/financials"
            params = {'ticker': ticker, 'apiKey': self.api_key}

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            return {}

    def _get_tiingo_fundamentals(self, ticker):
        """Get fundamentals from Tiingo"""
        try:
            import requests

            url = f"{self.base_url}/tiingo/fundamentals/{ticker}/daily"
            params = {'token': self.api_key}

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            return {}

    def get_batch_data(self, tickers, data_type='price', batch_size=10, delay=0.1):
        """
        Get batch data from premium provider

        Args:
            tickers (list): List of tickers
            data_type (str): 'price' or 'fundamental'
            batch_size (int): Batch size
            delay (float): Delay between requests

        Returns:
            dict: Results dictionary
        """
        results = {}
        successful_downloads = 0
        failed_downloads = 0

        print(f"🚀 Starting {self.provider} {data_type} download (batch size: {batch_size})")
        print("=" * 60)

        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(tickers) + batch_size - 1) // batch_size

            print(f"📦 Batch {batch_num}/{total_batches} ({len(batch)} tickers)")

            for ticker in batch:
                if data_type == 'price':
                    # Use default date range (last 2 years)
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - pd.DateOffset(years=2)).strftime('%Y-%m-%d')

                    data = self.get_price_data(ticker, start_date, end_date)
                else:
                    data = self.get_fundamental_data(ticker)

                if data is not None and len(data) > 0:
                    results[ticker] = data
                    successful_downloads += 1
                    print(f"  ✅ {ticker}")
                else:
                    failed_downloads += 1
                    print(f"  ❌ {ticker}")

                time.sleep(delay)

            print(f"📊 Batch {batch_num} complete: {successful_downloads} success, {failed_downloads} failed")
            print("-" * 40)

            # Larger delay between batches for premium APIs
            if batch_num < total_batches:
                time.sleep(1.0)

        print("=" * 60)
        print(f"🎉 {self.provider} download complete!")
        print(f"✅ Successful: {successful_downloads}")
        print(f"❌ Failed: {failed_downloads}")
        if successful_downloads + failed_downloads > 0:
            print(f"📊 Success rate: {(successful_downloads/(successful_downloads+failed_downloads)*100):.1f}%")

        return results