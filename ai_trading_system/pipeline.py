import pandas as pd
from data_sources import DataManager
from config import START_DATE
import time
import sys

def run_pipeline(max_tickers=None, data_types=None):
    """
    Enhanced pipeline using comprehensive data sources

    Args:
        max_tickers (int): Maximum number of tickers to process (for testing)
        data_types (list): Types of data to collect ['price', 'fundamental', 'corporate_actions']
    """
    try:
        print("🚀 AI TRADING SYSTEM - COMPREHENSIVE DATA PIPELINE")
        print("=" * 80)

        # Initialize data manager
        dm = DataManager()

        # Configure data types to collect
        if data_types is None:
            data_types = ['price', 'fundamental', 'corporate_actions']

        print(f"📊 Data sources to use:")
        print("   • Yahoo Finance → Price data with technical indicators")
        print("   • IDX → Ticker lists and corporate actions")
        print("   • Stockbit → Fundamental data")
        print(f"   • Data types: {', '.join(data_types)}")

        # Optional: Add premium data sources if API keys are available
        # Uncomment and add your API keys:
        # dm.add_premium_source('polygon', 'your_polygon_api_key')
        # dm.add_premium_source('tiingo', 'your_tiingo_api_key')

        # Collect comprehensive data
        results = dm.collect_comprehensive_data(
            tickers=None,  # None = all IDX tickers
            data_types=data_types,
            max_tickers=max_tickers
        )

        print("\n" + "=" * 80)
        print("🎯 PIPELINE EXECUTION SUMMARY")
        print("=" * 80)
        print(f"✅ Data sources used: {', '.join(results['metadata']['sources_used'])}")
        print(f"✅ Tickers processed: {results['metadata']['total_tickers']}")
        print(f"✅ Price data tables: {len(results['price_data'])}")
        print(f"✅ Fundamental data tables: {len(results['fundamental_data'])}")
        print(f"✅ Corporate actions: {len(results['corporate_actions'])}")

        # Calculate some statistics
        if results['price_data']:
            total_price_rows = sum(len(df) for df in results['price_data'].values() if df is not None)
            print(f"✅ Total price data points: {total_price_rows:,}")

        print(f"⏱️  Execution time: Complete")
        print("=" * 80)

        return results

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_quick_test():
    """Run a quick test with limited tickers"""
    print("🧪 QUICK TEST MODE - Limited tickers for testing")
    return run_pipeline(max_tickers=5, data_types=['price'])

def run_full_fundamentals():
    """Run full pipeline with fundamentals"""
    return run_pipeline(data_types=['price', 'fundamental', 'corporate_actions'])

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            run_quick_test()
        elif sys.argv[1] == "full":
            run_full_fundamentals()
        elif sys.argv[1] == "price-only":
            run_pipeline(data_types=['price'])
        else:
            print("Usage: python pipeline.py [test|full|price-only]")
            print("  test: Quick test with 5 tickers")
            print("  full: Full pipeline with all data types")
            print("  price-only: Price data only")
    else:
        # Default: run full pipeline
        run_full_fundamentals()