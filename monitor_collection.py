#!/usr/bin/env python3
"""
Monitoring Script untuk melacak progress pengambilan data 957 saham IDX
dan memberikan statistik real-time
"""

import json
import os
import time
import subprocess
from datetime import datetime
from pathlib import Path

def get_process_status():
    """Cek status proses pipeline"""
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        
        if 'run_comprehensive_pipeline_957.py' in result.stdout:
            return 'running'
        else:
            return 'stopped'
    except:
        return 'unknown'

def get_database_stats():
    """Ambil statistik dari database"""
    try:
        import sys
        sys.path.insert(0, '/workspaces/repo/ai_trading_system')
        from database import get_engine
        import sqlalchemy
        
        engine = get_engine()
        inspector = sqlalchemy.inspect(engine)
        tables = inspector.get_table_names()
        
        # Filter out system tables
        stock_tables = [t for t in tables if not t.endswith('_fundamentals') 
                       and t not in ['corporate_actions', 'data_collection_metadata', 'test_table']]
        
        return {
            'total_tables': len(stock_tables),
            'tables': sorted(stock_tables)[:10]  # Show first 10
        }
    except Exception as e:
        return {'error': str(e)}

def check_collection_summary():
    """Cek file summary terakhir"""
    summary_file = '/workspaces/repo/collection_summary.json'
    if os.path.exists(summary_file):
        try:
            with open(summary_file, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def monitor_collection():
    """Monitor dan tampilkan status pengumpulan data"""
    
    print("=" * 100)
    print("📊 MONITORING PENGUMPULAN DATA 957 SAHAM IDX")
    print("=" * 100)
    print(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Status Proses
    process_status = get_process_status()
    status_emoji = "🟢" if process_status == "running" else "🔴"
    print(f"{status_emoji} Process Status: {process_status.upper()}")
    
    # 2. Database Stats
    print("\n📁 Database Statistics:")
    db_stats = get_database_stats()
    if 'error' not in db_stats:
        print(f"   • Stock tables: {db_stats['total_tables']}")
        if db_stats['tables']:
            print(f"   • Sample tables: {', '.join(db_stats['tables'][:3])}")
    else:
        print(f"   • Error: {db_stats['error']}")
    
    # 3. Collection Summary
    print("\n📈 Collection Summary:")
    summary = check_collection_summary()
    if summary:
        print(f"   • Last update: {summary.get('timestamp', 'N/A')}")
        print(f"   • Total tickers: {summary.get('total_tickers', 0)}")
        print(f"   • Price data successful: {summary.get('price_data_successful', 0)}")
        print(f"   • Success rate: {summary.get('success_rate', 0):.1f}%")
        print(f"   • Fundamental data: {summary.get('fundamental_data', 0)}")
        print(f"   • Corporate actions: {summary.get('corporate_actions', 0)}")
    else:
        print("   • Tidak ada data summary yet")
    
    # 4. Latest Log Info
    print("\n📋 Log Files:")
    log_dir = Path('/workspaces/repo')
    log_files = sorted(log_dir.glob('collection_log_*.log'))
    if log_files:
        latest_log = log_files[-1]
        print(f"   • Latest log: {latest_log.name}")
        try:
            with open(latest_log, 'r') as f:
                lines = f.readlines()
                print(f"   • Lines: {len(lines)}")
                if lines:
                    print(f"   • Last line: {lines[-1].strip()[:80]}...")
        except:
            pass
    
    # 5. Recommended Actions
    print("\n💡 Recommended Actions:")
    if process_status == "stopped":
        print("   • Pipeline is not running. Start it with:")
        print("     python run_comprehensive_pipeline_957.py &")
    elif process_status == "running":
        print("   • Pipeline is running. Monitor the log file:")
        if log_files:
            print(f"     tail -f {log_files[-1].name}")
        print("   • Check database progress periodically")
    
    print("\n" + "=" * 100)

if __name__ == "__main__":
    while True:
        try:
            monitor_collection()
            print()
            # Auto-refresh setiap 30 detik
            for i in range(30, 0, -1):
                print(f"Next refresh in {i}s...", end='\r')
                time.sleep(1)
            print(" " * 50, end='\r')
        except KeyboardInterrupt:
            print("\n\n❌ Monitoring stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(30)
