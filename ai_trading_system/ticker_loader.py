import pandas as pd
import requests

def get_all_idx_tickers():
    """
    Get IDX tickers with fallback options
    """
    try:
        # Try to get from IDX official source
        url = "https://www.idx.co.id/Portals/0/StaticData/ListedCompanies/StockCode.csv"
        df = pd.read_csv(url)
        tickers = [t + ".JK" for t in df['Kode Saham']]
        print(f"✓ Loaded {len(tickers)} tickers from IDX")
        return tickers[:10]  # Limit to first 10 for demo
    except Exception as e:
        print(f"⚠ IDX source failed: {str(e)[:50]}")
        print("Using fallback ticker list...")

        # Fallback: Major IDX stocks
        fallback_tickers = [
            'BBCA.JK',  # BCA
            'BBRI.JK',  # BRI
            'BMRI.JK',  # Mandiri
            'ASII.JK',  # Astra
            'TLKM.JK',  # Telkom
            'UNVR.JK',  # Unilever
            'ICBP.JK',  # Indofood
            'ANTM.JK',  # Antam
            'GOTO.JK',  # GoTo
            'ADRO.JK'   # Adaro
        ]
        print(f"✓ Using {len(fallback_tickers)} fallback tickers")
        return fallback_tickers