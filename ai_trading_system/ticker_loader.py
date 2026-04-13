import pandas as pd

def get_all_idx_tickers():
    url = "https://www.idx.co.id/Portals/0/StaticData/ListedCompanies/StockCode.csv"
    df = pd.read_csv(url)
    return [t + ".JK" for t in df['Kode Saham']]