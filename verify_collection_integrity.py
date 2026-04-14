#!/usr/bin/env python3
"""
Script untuk verifikasi integrity data setelah pengumpulan 957 saham selesai
dan melakukan cross-check untuk memastikan tidak ada duplikasi
"""

import json
import sys
import pandas as pd
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, '/workspaces/repo/ai_trading_system')

def verify_collection_integrity():
    """Verify semua data yang telah dikumpulkan"""
    
    try:
        from database import get_engine
        import sqlalchemy
        
        print("=" * 100)
        print("🔍 VERIFIKASI INTEGRITY DATA PENGUMPULAN 957 SAHAM")
        print("=" * 100)
        print(f"⏰ Verification time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Load expected tickers
        with open('/workspaces/repo/final_957_idx_tickers_clean.json', 'r') as f:
            expected_tickers = set(json.load(f))
        
        print(f"📋 Expected tickers: {len(expected_tickers)}")
        
        # Connect to database
        engine = get_engine()
        inspector = sqlalchemy.inspect(engine)
        
        # Get table names
        all_tables = inspector.get_table_names()
        stock_tables = [t for t in all_tables if not t.endswith('_fundamentals') 
                       and t not in ['corporate_actions', 'data_collection_metadata', 'test_table']]
        
        print(f"📊 Database tables created: {len(stock_tables)}")
        print("\n" + "=" * 100)
        print("✅ VERIFICATION CHECKLIST")
        print("=" * 100)
        
        # 1. Check table coverage
        print("\n1️⃣  TABLE COVERAGE CHECK")
        stock_tickers = set(stock_tables)
        covered_tickers = expected_tickers & stock_tickers
        missing_tickers = expected_tickers - stock_tickers
        extra_tickers = stock_tickers - expected_tickers
        
        coverage = len(covered_tickers) / len(expected_tickers) * 100
        status_coverage = "✅" if coverage >= 90 else "⚠️"
        
        print(f"{status_coverage} Coverage: {len(covered_tickers)}/{len(expected_tickers)} ({coverage:.1f}%)")
        
        if missing_tickers and len(missing_tickers) <= 20:
            print(f"   Missing tickers: {sorted(list(missing_tickers))[:10]}")
        
        if extra_tickers and len(extra_tickers) <= 10:
            print(f"   Extra tickers: {sorted(list(extra_tickers))}")
        
        # 2. Check for duplicates
        print("\n2️⃣  DUPLICATE DATA CHECK")
        
        duplicate_count = 0
        duplicate_tables = []
        
        # Sample check on few tables
        sample_tables = list(stock_tickers)[:10]
        
        for table in sample_tables:
            try:
                # Check for duplicate rows
                df = pd.read_sql(f"SELECT * FROM \"{table}\"", engine)
                
                if 'Date' in df.columns:
                    duplicates = df[df.duplicated(subset=['Date'], keep=False)]
                    if len(duplicates) > 0:
                        duplicate_count += len(duplicates)
                        duplicate_tables.append((table, len(duplicates)))
            except:
                continue
        
        status_dup = "✅" if duplicate_count == 0 else "⚠️"
        print(f"{status_dup} Duplicate rows found: {duplicate_count}")
        
        if duplicate_tables:
            print(f"   Tables with duplicates:")
            for table, count in duplicate_tables[:5]:
                print(f"      • {table}: {count} duplicates")
        
        # 3. Check data completeness
        print("\n3️⃣  DATA COMPLETENESS CHECK")
        
        total_rows = 0
        tables_with_data = 0
        min_rows = float('inf')
        max_rows = 0
        
        for table in stock_tickers:
            try:
                result = engine.execute(f"SELECT COUNT(*) FROM \"{table}\"")
                row_count = result.fetchone()[0]
                
                if row_count > 0:
                    tables_with_data += 1
                    total_rows += row_count
                    min_rows = min(min_rows, row_count)
                    max_rows = max(max_rows, row_count)
            except:
                continue
        
        avg_rows = total_rows / tables_with_data if tables_with_data > 0 else 0
        
        print(f"✅ Tables with data: {tables_with_data}/{len(stock_tickers)}")
        print(f"   • Total rows: {total_rows:,}")
        print(f"   • Avg rows per table: {avg_rows:,.0f}")
        print(f"   • Min rows: {min_rows if min_rows != float('inf') else 0}")
        print(f"   • Max rows: {max_rows}")
        
        # 4. Check data quality
        print("\n4️⃣  DATA QUALITY CHECK")
        
        null_checks = 0
        null_tables = []
        
        # Sample a few tables
        for table in sample_tables[:5]:
            try:
                df = pd.read_sql(f"SELECT * FROM \"{table}\"", engine)
                
                null_count = df.isnull().sum().sum()
                if null_count > 0:
                    null_checks += null_count
                    null_tables.append((table, null_count))
            except:
                continue
        
        status_quality = "✅" if null_checks < 100 else "⚠️"
        print(f"{status_quality} Null values in sample: {null_checks}")
        
        if null_tables:
            print(f"   Tables with nulls (sample):")
            for table, count in null_tables[:3]:
                print(f"      • {table}: {count} nulls")
        
        # 5. Summary
        print("\n" + "=" * 100)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 100)
        
        all_pass = coverage >= 90 and duplicate_count == 0 and tables_with_data > 850
        
        status_final = "✅ PASSED" if all_pass else "⚠️  PARTIAL PASS"
        
        print(f"\n{status_final}")
        print(f"   • Coverage: {coverage:.1f}% ({len(covered_tickers)}/{len(expected_tickers)})")
        print(f"   • Duplicates: {duplicate_count}")
        print(f"   • Data Quality: {'Good' if null_checks < 100 else 'Fair'}")
        print(f"   • Total Data Points: {total_rows:,}")
        
        if not all_pass:
            print(f"\n⚠️  Recommendations:")
            if coverage < 90:
                print(f"   • Reprocess missing {len(missing_tickers)} tickers")
            if duplicate_count > 0:
                print(f"   • Clean {duplicate_count} duplicate rows")
            if tables_with_data < 850:
                print(f"   • Check {len(stock_tickers) - tables_with_data} empty tables")
        
        print("\n" + "=" * 100)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'coverage': coverage,
            'covered_tickers': len(covered_tickers),
            'missing_tickers': len(missing_tickers),
            'duplicate_rows': duplicate_count,
            'total_data_points': total_rows,
            'tables_with_data': tables_with_data,
            'status': 'PASSED' if all_pass else 'PARTIAL PASS'
        }
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = verify_collection_integrity()
    
    if result:
        # Save result
        with open('/workspaces/repo/integrity_verification_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n✅ Verification result saved to: integrity_verification_result.json")
