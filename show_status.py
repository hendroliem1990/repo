#!/usr/bin/env python3
"""
Real-time Status Dashboard untuk Pengumpulan Data 957 Saham IDX
Memberikan update progress, success rate, dan estimated completion time
"""

import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

def parse_log_for_stats(log_file):
    """Parse log file untuk mendapatkan statistik real-time"""
    
    stats = {
        'total_tickers': 0,
        'successful_downloads': 0,
        'failed_downloads': 0,
        'current_batch': 0,
        'total_batches': 48,
        'start_time': None,
        'current_time': None,
        'rows_collected': 0,
        'batches_completed': 0
    }
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find start time
        for line in lines:
            if 'Start time:' in line:
                stats['start_time'] = line.split('Start time:')[1].strip()
            
            # Count successful downloads
            if '✅' in line and 'rows' in line:
                try:
                    rows = int(re.search(r'(\d+) rows', line).group(1))
                    stats['rows_collected'] += rows
                    stats['successful_downloads'] += 1
                except:
                    pass
            
            # Count failed
            if '❌' in line and 'rows' not in line:
                stats['failed_downloads'] += 1
            
            # Get batch info
            if 'Batch' in line and 'complete:' in line:
                match = re.search(r'Batch (\d+)/(\d+)', line)
                if match:
                    stats['batches_completed'] = int(match.group(1))
                    stats['total_batches'] = int(match.group(2))
        
        stats['current_time'] = datetime.now()
        stats['total_tickers'] = stats['successful_downloads'] + stats['failed_downloads']
        
    except Exception as e:
        stats['error'] = str(e)
    
    return stats

def get_completion_estimate(stats):
    """Estimate waktu completion berdasarkan progress"""
    
    if not stats['start_time'] or stats['total_tickers'] == 0:
        return None
    
    try:
        # Assume 2 minutes per batch (based on configuration)
        time_per_batch = 2  # minutes (dari config: batch_delay=1.0 + processing time)
        
        remaining_batches = stats['total_batches'] - stats['batches_completed']
        estimated_remaining_time = remaining_batches * time_per_batch
        
        return {
            'remaining_time_minutes': estimated_remaining_time,
            'estimated_completion': (datetime.now() + timedelta(minutes=estimated_remaining_time)).strftime('%H:%M:%S'),
            'progress_percent': (stats['batches_completed'] / stats['total_batches']) * 100
        }
    except:
        return None

def display_status():
    """Display current status"""
    
    log_dir = Path('/workspaces/repo')
    log_files = sorted(log_dir.glob('collection_log_*.log'))
    
    if not log_files:
        print("❌ No collection log files found")
        return
    
    latest_log = log_files[-1]
    
    print("\n" + "=" * 100)
    print("📊 REAL-TIME STATUS: PENGUMPULAN DATA 957 SAHAM IDX")
    print("=" * 100)
    
    stats = parse_log_for_stats(str(latest_log))
    
    if 'error' in stats:
        print(f"❌ Error parsing log: {stats['error']}")
        return
    
    # Display main stats
    print(f"\n📍 Status Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Log file: {latest_log.name}")
    print(f"\n🎯 Progress:")
    print(f"   • Batches completed: {stats['batches_completed']}/{stats['total_batches']}")
    print(f"   • Tickers processed: {stats['total_tickers']}/957")
    print(f"   • Successful: {stats['successful_downloads']} ✅")
    print(f"   • Failed: {stats['failed_downloads']} ❌")
    
    if stats['total_tickers'] > 0:
        success_rate = (stats['successful_downloads'] / stats['total_tickers']) * 100
        print(f"   • Success rate: {success_rate:.1f}%")
    
    print(f"\n📈 Data Collected:")
    print(f"   • Price data rows: {stats['rows_collected']:,}")
    
    # Estimate completion
    estimate = get_completion_estimate(stats)
    if estimate:
        print(f"\n⏱️  Estimated Completion:")
        print(f"   • Progress: {estimate['progress_percent']:.1f}%")
        print(f"   • Remaining time: ~{estimate['remaining_time_minutes']:.0f} minutes")
        print(f"   • Est. completion: {estimate['estimated_completion']}")
    
    print(f"\n📋 System Information:")
    print(f"   • Start time: {stats['start_time']}")
    print(f"   • Current time: {stats['current_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 100)
    print("💡 Tips:")
    print("   • Monitor: tail -f collection_log_*.log")
    print("   • Verify: python verify_collection_integrity.py (after collection)")
    print("   • Dashboard: streamlit run ai_trading_system/app.py")
    print("=" * 100 + "\n")

if __name__ == "__main__":
    display_status()
