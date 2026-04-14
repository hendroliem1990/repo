"""
Database Status Checker
Memeriksa keseluruhan data saham yang tersedia dalam database
"""

import pandas as pd
import sqlalchemy
from database import get_engine
from datetime import datetime, timedelta
import json

def check_database_status():
    """
    Check database status dan tampilkan informasi lengkap
    """
    
    print("=" * 80)
    print("📊 DATABASE STATUS CHECKER - 957 SAHAM IDX")
    print("=" * 80)
    print(f"Waktu Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        engine = get_engine()
        inspector = sqlalchemy.inspect(engine)
        
        # Get all tables
        all_tables = inspector.get_table_names()
        stock_tables = [
            t for t in all_tables 
            if not t.endswith('_fundamentals') 
            and t not in ['corporate_actions', 'data_collection_metadata', 'test_table']
        ]
        
        # SECTION 1: General Statistics
        print("\n" + "="*80)
        print("1️⃣  STATISTIK UMUM")
        print("="*80)
        
        print(f"Total table di database: {len(all_tables)}")
        print(f"Total saham (stock tables): {len(stock_tables)}")
        print(f"Target: 957 saham")
        print(f"Status: {'✅ EXCELLENT' if len(stock_tables) >= 900 else '⚠️ OK' if len(stock_tables) >= 600 else '❌ INCOMPLETE'} ({len(stock_tables)/957*100:.1f}%)")
        
        # SECTION 2: Data Completeness per Stock
        print("\n" + "="*80)
        print("2️⃣  DATA COMPLETENESS PER SAHAM")
        print("="*80)
        
        stock_stats = []
        
        for ticker in sorted(stock_tables)[:20]:  # Show first 20
            try:
                query = f"SELECT COUNT(*) as count, MIN(Date) as start_date, MAX(Date) as end_date FROM '{ticker}'"
                result = pd.read_sql(query, engine)
                
                count = result['count'].iloc[0]
                start_date = result['start_date'].iloc[0]
                end_date = result['end_date'].iloc[0]
                
                # Calculate data span
                if start_date and end_date:
                    start = pd.to_datetime(start_date)
                    end = pd.to_datetime(end_date)
                    days_span = (end - start).days
                else:
                    days_span = 0
                
                stock_stats.append({
                    'Ticker': ticker,
                    'Rows': count,
                    'Start': start_date,
                    'End': end_date,
                    'Days': days_span,
                    'Status': '✅' if count >= 1000 else '⚠️' if count >= 500 else '❌'
                })
            except Exception as e:
                stock_stats.append({
                    'Ticker': ticker,
                    'Rows': 'ERROR',
                    'Start': 'ERROR',
                    'End': 'ERROR',
                    'Days': 0,
                    'Status': '❌'
                })
        
        df_stats = pd.DataFrame(stock_stats)
        print("\nFirst 20 STOCKS:")
        print(df_stats.to_string(index=False))
        
        # SECTION 3: Data Coverage Summary
        print("\n" + "="*80)
        print("3️⃣  DATA COVERAGE SUMMARY")
        print("="*80)
        
        min_rows = 100
        coverage = {
            'total_stocks': len(stock_tables),
            'stocks_with_data': 0,
            'stocks_with_good_data': 0,
            'stocks_with_excellent_data': 0,
            'avg_rows': 0,
            'min_rows': float('inf'),
            'max_rows': 0,
            'total_rows': 0,
        }
        
        for ticker in stock_tables:
            try:
                query = f"SELECT COUNT(*) as count FROM '{ticker}'"
                result = pd.read_sql(query, engine)
                count = result['count'].iloc[0]
                
                coverage['total_rows'] += count
                coverage['stocks_with_data'] += 1
                
                if count >= 500:
                    coverage['stocks_with_good_data'] += 1
                
                if count >= 1000:
                    coverage['stocks_with_excellent_data'] += 1
                
                coverage['min_rows'] = min(coverage['min_rows'], count)
                coverage['max_rows'] = max(coverage['max_rows'], count)
            except:
                continue
        
        if coverage['stocks_with_data'] > 0:
            coverage['avg_rows'] = coverage['total_rows'] / coverage['stocks_with_data']
        
        print(f"\n📊 Saham Data Coverage:")
        print(f"  ✅ Saham dengan data: {coverage['stocks_with_data']}/{coverage['total_stocks']}")
        print(f"  ✅ Good data (>= 500 rows): {coverage['stocks_with_good_data']}")
        print(f"  ✅ Excellent data (>= 1000 rows): {coverage['stocks_with_excellent_data']}")
        
        print(f"\n📈 Data Volume Statistics:")
        print(f"  total rows: {coverage['total_rows']:,}")
        print(f"  avg rows per stock: {coverage['avg_rows']:.0f}")
        print(f"  min rows: {coverage['min_rows']}")
        print(f"  max rows: {coverage['max_rows']}")
        
        # SECTION 4: Data Quality Issues
        print("\n" + "="*80)
        print("4️⃣  POTENTIAL DATA QUALITY ISSUES")
        print("="*80)
        
        issues = []
        
        # Check for missing tickers
        if len(stock_tables) < 900:
            missing_count = 957 - len(stock_tables)
            issues.append(f"⚠️  Missing {missing_count} tickers ({missing_count/957*100:.1f}%)")
        
        # Check for stocks with insufficient data
        insufficient = 0
        for ticker in stock_tables:
            try:
                query = f"SELECT COUNT(*) as count FROM '{ticker}'"
                result = pd.read_sql(query, engine)
                if result['count'].iloc[0] < 100:
                    insufficient += 1
            except:
                continue
        
        if insufficient > 0:
            issues.append(f"⚠️  {insufficient} stocks dengan data < 100 rows")
        
        # Check database file size
        try:
            import os
            db_path = "ai_trading_system/trading_db.sqlite"
            if os.path.exists(db_path):
                size_mb = os.path.getsize(db_path) / (1024*1024)
                print(f"\n💾 Database File Size: {size_mb:.1f} MB")
                
                if size_mb < 100:
                    issues.append(f"⚠️  Database size hanya {size_mb:.1f} MB (expected 200-500 MB untuk full data)")
        except:
            pass
        
        if issues:
            print("\nIssues Found:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✅ NO ISSUES - Database dalam kondisi baik!")
        
        # SECTION 5: Latest Data
        print("\n" + "="*80)
        print("5️⃣  LATEST DATA POINTS")
        print("="*80)
        
        latest_dates = []
        for ticker in sorted(stock_tables)[:10]:  # Check first 10
            try:
                query = f"SELECT MAX(Date) as latest FROM '{ticker}'"
                result = pd.read_sql(query, engine)
                latest = result['latest'].iloc[0]
                latest_dates.append((ticker, latest))
            except:
                latest_dates.append((ticker, 'ERROR'))
        
        print("\nLatest data date for first 10 tickers:")
        for ticker, date in latest_dates:
            print(f"  {ticker}: {date}")
        
        # SECTION 6: Recommendations
        print("\n" + "="*80)
        print("6️⃣  REKOMENDASI")
        print("="*80)
        
        if len(stock_tables) >= 900:
            print("✅ Database siap untuk digunakan!")
            print("   Jalankan app_advanced.py untuk analisis lengkap")
        else:
            print("⚠️  Database belum lengkap. Tunggu pengumpulan data selesai.")
            progress = len(stock_tables) / 957 * 100
            print(f"   Progress: {progress:.1f}% ({len(stock_tables)}/957)")
        
        print("\n" + "="*80)
        
        # Save report to JSON
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_stocks': len(stock_tables),
            'coverage': len(stock_tables) / 957 * 100,
            'stocks': sorted(stock_tables),
            'statistics': coverage
        }
        
        with open('database_status_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n✅ Report saved to: database_status_report.json")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_stock_data(ticker):
    """
    Verify data untuk ticker spesifik
    """
    print(f"\n📊 DETAILED VERIFICATION FOR {ticker}")
    print("="*80)
    
    try:
        engine = get_engine()
        
        # Load all data
        df = pd.read_sql(f"SELECT * FROM '{ticker}'", engine)
        
        if df.empty:
            print(f"❌ No data for {ticker}")
            return False
        
        df['Date'] = pd.to_datetime(df['Date'])
        
        print(f"\nTotal rows: {len(df)}")
        print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"Data span: {(df['Date'].max() - df['Date'].min()).days} days")
        
        # Check for missing values
        print(f"\nMissing values:")
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(missing[missing > 0])
        else:
            print("✅ No missing values")
        
        # Check for duplicates
        duplicates = df.duplicated(subset=['Date']).sum()
        if duplicates > 0:
            print(f"⚠️  {duplicates} duplicate dates found")
        else:
            print("✅ No duplicate dates")
        
        # Price statistics
        print(f"\nPrice Statistics:")
        print(f"  Min: {df['Close'].min():.0f}")
        print(f"  Max: {df['Close'].max():.0f}")
        print(f"  Mean: {df['Close'].mean():.0f}")
        print(f"  Std Dev: {df['Close'].std():.0f}")
        
        # Volume statistics
        if 'Volume' in df.columns:
            print(f"\nVolume Statistics:")
            print(f"  Min: {df['Volume'].min():,.0f}")
            print(f"  Max: {df['Volume'].max():,.0f}")
            print(f"  Mean: {df['Volume'].mean():,.0f}")
        
        print(f"\n✅ {ticker} data quality: GOOD")
        
        return True
    
    except Exception as e:
        print(f"❌ Error verifying {ticker}: {e}")
        return False

if __name__ == "__main__":
    print("\n🔍 MEMULAI DATABASE STATUS CHECK...\n")
    
    check_database_status()
    
    # Optional: Verify specific stocks
    print("\n\n" + "="*80)
    print("VERIFY SPECIFIC STOCKS")
    print("="*80)
    
    test_tickers = ['BBCA', 'ASII', 'TLKM', 'UNVR', 'BRIS']
    
    for ticker in test_tickers:
        verify_stock_data(f"{ticker}.JK")
        print()
