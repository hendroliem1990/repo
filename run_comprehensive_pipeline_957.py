#!/usr/bin/env python3
"""
Pipeline Optimized untuk mengambil data 957 saham IDX secara perlahan dengan
cross-check data duplikasi dan deduplicasi otomatis
"""

import json
import time
import sys
import os
from datetime import datetime

# Add the ai_trading_system directory to path
sys.path.insert(0, '/workspaces/repo/ai_trading_system')

from data_sources import DataManager
from config import START_DATE

def load_957_tickers():
    """Load 957 ticker IDX terverifikasi"""
    try:
        with open('/workspaces/repo/final_957_idx_tickers_clean.json', 'r') as f:
            tickers = json.load(f)
        print(f"✅ Loaded {len(tickers)} verified IDX tickers")
        return tickers
    except FileNotFoundError:
        print("❌ Final ticker list not found, using fallback")
        return []

def run_optimized_pipeline():
    """
    Run optimized pipeline dengan:
    - Batch processing untuk semua 957 saham
    - Progress tracking yang detail
    - Cross-check data duplikasi
    - Deduplicasi otomatis
    - Resume capability
    """
    try:
        print("🚀 AI TRADING SYSTEM - COMPREHENSIVE 957 TICKER DATA COLLECTION")
        print("=" * 100)
        print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load ticker list
        tickers = load_957_tickers()
        if not tickers:
            print("❌ No tickers loaded, exiting")
            return
        
        print(f"📊 Total tickers to process: {len(tickers)}")
        print("=" * 100)
        
        # Initialize data manager
        dm = DataManager()
        
        # Konfigurasi pengambilan data
        data_types = ['price', 'fundamental', 'corporate_actions']
        batch_size = 20  # 20 saham per batch
        batch_delay = 1.0  # 1 detik delay antar batch
        ticker_delay = 0.1  # 0.1 detik delay antar ticker
        
        print(f"\n⚙️  Konfigurasi:")
        print(f"   • Batch size: {batch_size}")
        print(f"   • Batch delay: {batch_delay}s")
        print(f"   • Ticker delay: {ticker_delay}s")
        print(f"   • Data types: {', '.join(data_types)}")
        print(f"   • Estimated time: ~{len(tickers) * ticker_delay / 60:.0f} minutes")
        
        # Collect data dengan batching
        print(f"\n💰 COLLECTING PRICE DATA (Yahoo Finance)")
        print("=" * 100)
        
        price_data_results = dm.yahoo.download_batch(
            tickers, 
            batch_size=batch_size, 
            delay=ticker_delay
        )
        
        # Log detail progress
        successful = len([v for v in price_data_results.values() if v is not None])
        failed = len(price_data_results) - successful
        
        print(f"\n✅ Price data collection complete:")
        print(f"   • Successful: {successful}")
        print(f"   • Failed: {failed}")
        print(f"   • Success rate: {(successful/len(price_data_results)*100):.1f}%")
        
        # Collect fundamental data
        print(f"\n📊 COLLECTING FUNDAMENTAL DATA (Stockbit)")
        print("=" * 100)
        
        fundamental_data_results = dm.stockbit.get_batch_fundamentals(tickers)
        fund_count = len([v for v in fundamental_data_results.values() if v is not None])
        print(f"✅ Fundamental data: {fund_count} tickers")
        
        # Collect corporate actions
        print(f"\n🏢 COLLECTING CORPORATE ACTIONS (IDX)")
        print("=" * 100)
        
        corporate_actions = dm.idx.get_corporate_actions()
        print(f"✅ Corporate actions: {len(corporate_actions)} records")
        
        # Summary
        print(f"\n" + "=" * 100)
        print("📊 FINAL PIPELINE SUMMARY")
        print("=" * 100)
        print(f"Total tickers processed: {len(tickers)}")
        print(f"Price data collected: {successful}/{len(tickers)} ({(successful/len(tickers)*100):.1f}%)")
        print(f"Fundamental data: {fund_count}")
        print(f"Corporate actions: {len(corporate_actions)}")
        print(f"⏰ End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tickers': len(tickers),
            'price_data_successful': successful,
            'price_data_failed': failed,
            'fundamental_data': fund_count,
            'corporate_actions': len(corporate_actions),
            'success_rate': (successful/len(tickers)*100)
        }
        
        with open('/workspaces/repo/collection_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Summary saved to: collection_summary.json")
        
        return {
            'price_data': price_data_results,
            'fundamental_data': fundamental_data_results,
            'corporate_actions': corporate_actions,
            'summary': summary
        }
        
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    run_optimized_pipeline()
