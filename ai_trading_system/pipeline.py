import yfinance as yf
import pandas as pd
from database import get_engine
from ticker_loader import get_all_idx_tickers
from ta.momentum import RSIIndicator
from ta.trend import MACD
from config import START_DATE
import time

engine = get_engine()

def add_indicators(df):
    df['RSI'] = RSIIndicator(df['Close']).rsi()
    macd = MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    return df

def run_pipeline():
    try:
        tickers = get_all_idx_tickers()
    except Exception as e:
        print(f"Error loading tickers: {e}")
        print("Using fallback ticker list...")
        # Fallback tickers jika download gagal
        tickers = ['BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'ASII.JK']

    for ticker in tickers:
        try:
            print(f"Downloading {ticker}...")
            df = yf.download(ticker, start=START_DATE, progress=False)

            if df.empty:
                print(f"No data for {ticker}")
                continue

            df = add_indicators(df)
            table_name = ticker.replace(".JK","")
            df.to_sql(table_name, engine, if_exists='replace', index=True)

            print(f"✓ Saved: {ticker} ({len(df)} rows)")
            time.sleep(0.5)

        except Exception as e:
            print(f"✗ Error {ticker}: {str(e)[:100]}")

if __name__ == "__main__":
    run_pipeline()