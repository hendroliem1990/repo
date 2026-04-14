import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from config import START_DATE
import time

class YahooDataSource:
    """Yahoo Finance data source for price data"""

    def __init__(self):
        self.name = "Yahoo Finance"
        self.data_type = "price"

    def add_technical_indicators(self, df):
        """Add technical indicators to price data"""
        try:
            df['RSI'] = RSIIndicator(df['Close']).rsi()
            macd = MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_signal'] = macd.macd_signal()
            return df
        except Exception as e:
            print(f"⚠ Error adding indicators: {e}")
            return df

    def download_ticker_data(self, ticker, start_date=None):
        """
        Download price data for a single ticker from Yahoo Finance

        Args:
            ticker (str): Ticker symbol (e.g., 'BBCA.JK')
            start_date (str): Start date in YYYY-MM-DD format

        Returns:
            pd.DataFrame: Price data with technical indicators
        """
        if start_date is None:
            start_date = START_DATE

        try:
            print(f"  📥 {ticker} (Yahoo)...", end=" ")

            # Download data
            df = yf.download(ticker, start=start_date, progress=False)

            if df.empty:
                print("❌ No data")
                return None

            # Handle multi-index columns from yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Ensure we have required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_cols):
                print("❌ Missing columns")
                return None

            # Add technical indicators
            df = self.add_technical_indicators(df)

            # Add metadata
            df['ticker'] = ticker
            df['data_source'] = self.name
            df['data_type'] = self.data_type

            print(f"✅ {len(df)} rows")
            return df

        except Exception as e:
            print(f"❌ {str(e)[:30]}...")
            return None

    def download_batch(self, tickers, batch_size=20, delay=0.1):
        """
        Download price data for multiple tickers in batches

        Args:
            tickers (list): List of ticker symbols
            batch_size (int): Number of tickers per batch
            delay (float): Delay between requests in seconds

        Returns:
            dict: Dictionary of ticker -> DataFrame
        """
        results = {}
        successful_downloads = 0
        failed_downloads = 0

        print(f"🚀 Starting Yahoo Finance download (batch size: {batch_size})")
        print("=" * 60)

        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(tickers) + batch_size - 1) // batch_size

            print(f"📦 Batch {batch_num}/{total_batches} ({len(batch)} tickers)")

            for ticker in batch:
                df = self.download_ticker_data(ticker)
                if df is not None:
                    results[ticker] = df
                    successful_downloads += 1
                else:
                    failed_downloads += 1

                # Small delay to be respectful to Yahoo Finance
                time.sleep(delay)

            print(f"📊 Batch {batch_num} complete: {successful_downloads} success, {failed_downloads} failed")
            print("-" * 40)

            # Larger delay between batches
            if batch_num < total_batches:
                time.sleep(1.0)

        print("=" * 60)
        print(f"🎉 Yahoo Finance download complete!")
        print(f"✅ Successful: {successful_downloads}")
        print(f"❌ Failed: {failed_downloads}")
        print(f"📊 Success rate: {(successful_downloads/(successful_downloads+failed_downloads)*100):.1f}%")

        return results