from data_sources.yahoo_data import YahooDataSource
from data_sources.idx_data import IDXDataSource
from data_sources.stockbit_data import StockbitDataSource
from data_sources.premium_data import PremiumDataSource
from database import get_engine
import pandas as pd
from datetime import datetime
import time

class DataManager:
    """Central coordinator for all data sources"""

    def __init__(self, db_engine=None):
        self.engine = db_engine or get_engine()

        # Initialize data sources
        self.yahoo = YahooDataSource()
        self.idx = IDXDataSource()
        self.stockbit = StockbitDataSource()  # Will work without API key for basic structure

        # Premium sources (require API keys)
        self.premium_sources = {}

    def add_premium_source(self, provider, api_key):
        """Add premium data source with API key"""
        if provider.lower() in ['polygon', 'tiingo', 'refinitiv', 'bloomberg']:
            self.premium_sources[provider.lower()] = PremiumDataSource(provider, api_key)
            print(f"✅ Added {provider} premium data source")
        else:
            print(f"❌ Unsupported premium provider: {provider}")

    def get_all_tickers(self):
        """Get comprehensive ticker list from IDX"""
        return self.idx.get_all_tickers()

    def collect_comprehensive_data(self, tickers=None, data_types=None, max_tickers=None):
        """
        Collect comprehensive data from all available sources

        Args:
            tickers (list): List of tickers to process (None = all IDX tickers)
            data_types (list): Types of data to collect ['price', 'fundamental', 'corporate_actions']
            max_tickers (int): Maximum number of tickers to process (for testing)
        """
        if tickers is None:
            tickers = self.get_all_tickers()

        if max_tickers:
            tickers = tickers[:max_tickers]

        if data_types is None:
            data_types = ['price', 'fundamental', 'corporate_actions']

        print(f"🎯 Starting comprehensive data collection for {len(tickers)} tickers")
        print(f"📊 Data types: {', '.join(data_types)}")
        print("=" * 80)

        results = {
            'price_data': {},
            'fundamental_data': {},
            'corporate_actions': pd.DataFrame(),
            'metadata': {
                'total_tickers': len(tickers),
                'data_types': data_types,
                'timestamp': datetime.now().isoformat(),
                'sources_used': []
            }
        }

        # 1. Collect price data from Yahoo Finance
        if 'price' in data_types:
            print("\n💰 COLLECTING PRICE DATA (Yahoo Finance)")
            results['price_data'] = self.yahoo.download_batch(tickers)
            results['metadata']['sources_used'].append('Yahoo Finance')

        # 2. Collect fundamental data from Stockbit
        if 'fundamental' in data_types:
            print("\n📊 COLLECTING FUNDAMENTAL DATA (Stockbit)")
            results['fundamental_data'] = self.stockbit.get_batch_fundamentals(tickers)
            results['metadata']['sources_used'].append('Stockbit')

        # 3. Collect corporate actions from IDX
        if 'corporate_actions' in data_types:
            print("\n🏢 COLLECTING CORPORATE ACTIONS (IDX)")
            # Get corporate actions for all tickers (last 365 days)
            results['corporate_actions'] = self.idx.get_corporate_actions()
            results['metadata']['sources_used'].append('IDX')

        # 4. Collect premium data if available
        premium_data = {}
        for provider, source in self.premium_sources.items():
            print(f"\n💎 COLLECTING PREMIUM DATA ({provider.upper()})")
            premium_results = source.get_batch_data(tickers, data_type='price')
            if premium_results:
                premium_data[provider] = premium_results
                results['metadata']['sources_used'].append(provider.title())

        results['premium_data'] = premium_data

        # Save all data to database
        self._save_to_database(results)

        print("\n" + "=" * 80)
        print("🎉 COMPREHENSIVE DATA COLLECTION COMPLETE!")
        print(f"✅ Sources used: {', '.join(results['metadata']['sources_used'])}")
        print(f"✅ Tickers processed: {len(tickers)}")
        print(f"✅ Price data points: {sum(len(df) for df in results['price_data'].values()) if results['price_data'] else 0}")
        print(f"✅ Fundamental data points: {len(results['fundamental_data'])}")
        print(f"✅ Corporate actions: {len(results['corporate_actions'])}")

        return results

    def _save_to_database(self, results):
        """Save collected data to database"""
        try:
            print("\n💾 SAVING DATA TO DATABASE...")

            # Save price data
            price_saved = 0
            for ticker, df in results['price_data'].items():
                if df is not None and not df.empty:
                    table_name = ticker.replace('.JK', '')
                    df.to_sql(table_name, self.engine, if_exists='replace', index=True)
                    price_saved += 1

            # Save fundamental data
            fundamental_saved = 0
            for ticker, data in results['fundamental_data'].items():
                if data:
                    table_name = f"{ticker.replace('.JK', '')}_fundamentals"
                    # Convert dict to DataFrame for storage, flatten nested dicts
                    flat_data = {
                        'ticker': data.get('ticker'),
                        'data_source': data.get('data_source'),
                        'data_type': data.get('data_type'),
                        'timestamp': data.get('timestamp'),
                        'financials': str(data.get('financials', {})),  # Convert to string
                        'ratios': str(data.get('ratios', {})),
                        'profile': str(data.get('profile', {}))
                    }
                    df_fund = pd.DataFrame([flat_data])
                    df_fund.to_sql(table_name, self.engine, if_exists='replace', index=False)
                    fundamental_saved += 1

            # Save corporate actions
            if not results['corporate_actions'].empty:
                results['corporate_actions'].to_sql('corporate_actions', self.engine, if_exists='replace', index=False)

            # Save metadata
            metadata_df = pd.DataFrame([{
                'total_tickers': results['metadata']['total_tickers'],
                'data_types': ','.join(results['metadata']['data_types']),  # Convert list to string
                'timestamp': results['metadata']['timestamp'],
                'sources_used': ','.join(results['metadata']['sources_used'])  # Convert list to string
            }])
            metadata_df.to_sql('data_collection_metadata', self.engine, if_exists='append', index=False)

            print(f"✅ Saved {price_saved} price tables, {fundamental_saved} fundamental tables, {len(results['corporate_actions'])} corporate actions")

        except Exception as e:
            print(f"❌ Error saving to database: {e}")

    def update_ticker_data(self, ticker, data_types=None):
        """
        Update data for a specific ticker

        Args:
            ticker (str): Ticker symbol
            data_types (list): Types of data to update
        """
        if data_types is None:
            data_types = ['price', 'fundamental']

        print(f"🔄 Updating data for {ticker}")

        results = {}

        if 'price' in data_types:
            price_data = self.yahoo.download_ticker_data(ticker)
            if price_data is not None:
                table_name = ticker.replace('.JK', '')
                price_data.to_sql(table_name, self.engine, if_exists='replace', index=True)
                results['price'] = True
                print(f"✅ Updated price data for {ticker}")

        if 'fundamental' in data_types:
            fundamental_data = self.stockbit.get_fundamental_data(ticker)
            if fundamental_data:
                table_name = f"{ticker.replace('.JK', '')}_fundamentals"
                df_fund = pd.DataFrame([fundamental_data])
                df_fund.to_sql(table_name, self.engine, if_exists='replace', index=False)
                results['fundamental'] = True
                print(f"✅ Updated fundamental data for {ticker}")

        return results

    def get_data_quality_report(self):
        """Generate data quality report"""
        try:
            # This would analyze the database and provide quality metrics
            # For now, return basic structure
            return {
                'total_tickers': 0,
                'price_data_coverage': 0,
                'fundamental_data_coverage': 0,
                'corporate_actions_count': 0,
                'data_freshness': 'Unknown',
                'quality_score': 0
            }
        except Exception as e:
            print(f"Error generating quality report: {e}")
            return {}