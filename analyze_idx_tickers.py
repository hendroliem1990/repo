#!/usr/bin/env python3
"""
Script untuk menganalisis dan melakukan deduplicasi 957 ticker IDX
serta cross-check dengan data yang sudah ada
"""

import json
import pandas as pd
from collections import defaultdict

def load_tickers(file_path):
    """Load daftar ticker dari file JSON"""
    try:
        with open(file_path, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def analyze_tickers():
    """Analisis dan deduplicasi ticker"""
    
    # Load semua sumber ticker
    print("=" * 80)
    print("📊 ANALISIS DATA SAHAM IDX 957 TICKER")
    print("=" * 80)
    
    # 1. Load daftar lengkap 957 ticker
    complete_tickers = load_tickers('/workspaces/repo/complete_idx_957_tickers.json')
    print(f"\n✅ Complete IDX 957 tickers: {len(complete_tickers)}")
    
    # 2. Load daftar sebelumnya
    old_tickers = load_tickers('/workspaces/repo/comprehensive_idx_tickers.json')
    print(f"✅ Previous comprehensive tickers: {len(old_tickers)}")
    
    # 3. Analisis perbedaan
    new_tickers = complete_tickers - old_tickers
    removed_tickers = old_tickers - complete_tickers
    common_tickers = complete_tickers & old_tickers
    
    print(f"\n📈 Analisis Perbandingan:")
    print(f"   • Ticker baru: {len(new_tickers)}")
    print(f"   • Ticker yang dihapus: {len(removed_tickers)}")
    print(f"   • Ticker yang sama: {len(common_tickers)}")
    
    if new_tickers:
        print(f"\n🆕 Ticker Baru (contoh 10): {sorted(list(new_tickers))[:10]}")
    
    if removed_tickers:
        print(f"\n❌ Ticker Dihapus (contoh 10): {sorted(list(removed_tickers))[:10]}")
    
    # 4. Cek duplikasi di daftar lengkap
    all_list = json.load(open('/workspaces/repo/complete_idx_957_tickers.json'))
    duplicates = defaultdict(int)
    for ticker in all_list:
        duplicates[ticker] += 1
    
    duplicate_tickers = {k: v for k, v in duplicates.items() if v > 1}
    
    if duplicate_tickers:
        print(f"\n⚠️  Duplikasi Ditemukan: {len(duplicate_tickers)}")
        for ticker, count in sorted(duplicate_tickers.items())[:10]:
            print(f"   • {ticker}: {count}x")
    else:
        print(f"\n✅ Tidak ada duplikasi dalam 957 ticker")
    
    # 5. Simpan daftar final yang sudah dibersihkan
    final_tickers = sorted(list(complete_tickers))
    
    with open('/workspaces/repo/final_957_idx_tickers_clean.json', 'w') as f:
        json.dump(final_tickers, f, indent=2)
    
    print(f"\n✅ Final clean ticker list: {len(final_tickers)} tickers")
    print(f"💾 Disimpan ke: /workspaces/repo/final_957_idx_tickers_clean.json")
    
    # 6. Breakdown by sector (berdasarkan analisis manual)
    print("\n" + "=" * 80)
    print("📊 DISTRIBUSI TICKER PER SEKTOR")
    print("=" * 80)
    
    sector_breakdown = {
        'Banking & Finance': ['BBCA', 'BBRI', 'BMRI', 'BBNI', 'BRIS', 'BNGA', 'BDMN', 'BNLI', 'BJBR', 'BJTM',
                             'INPC', 'NISP', 'PNBN', 'SDRA', 'AGRO', 'BFIN', 'BBKP', 'BBMD', 'BBTN', 'BBSI',
                             'BBYB', 'BCIC', 'BDKR', 'BEKS', 'BGTG', 'BHIT', 'BINA', 'BKSW', 'BMAS', 'BVIC',
                             'MAYA', 'MEGA', 'NOBU', 'PBID', 'PGLI', 'PNLF', 'RELI', 'SDMU', 'SKYB', 'SOFA',
                             'TRIM', 'VRNA', 'BTPS', 'HDFC', 'PBSA', 'TCPI', 'ARTO', 'ASBI', 'ASDM', 'BABA',
                             'BABP', 'BACA', 'BBHI', 'BBLD', 'BBRM', 'BCAP', 'CFIN', 'DANP', 'DNAR', 'HDFA',
                             'LPPS', 'MCOR', 'BNII', 'BSWD'],
        'Consumer Goods & Retail': ['ASII', 'UNVR', 'ICBP', 'INDF', 'MYOR', 'HMSP', 'GGRM', 'ULTJ', 'KLBF', 'TSPC',
                                   'ADES', 'AMRT', 'CPIN', 'JPFA', 'MAIN', 'SMGR', 'SRIL', 'MPPA', 'SILO',
                                   'AALI', 'ABBA', 'ACES', 'ADMG', 'AGII', 'AKRA', 'ALKA', 'ALMI', 'AMFG',
                                   'AMIN', 'ANJT', 'APII', 'APLN', 'ARGO', 'ARNA', 'ASGR', 'ASJT', 'AUTO'],
        'Mining & Energy': ['ANTM', 'ADRO', 'PTBA', 'ITMG', 'BYAN', 'MEDC', 'PGAS', 'ENRG', 'ELSA', 'HRUM',
                           'INCO', 'TINS', 'PTRO', 'CNKO', 'CTRA', 'DEWA', 'GEMS', 'MEDC', 'MYOH', 'PGJO'],
        'Property & Real Estate': ['BSDE', 'PWON', 'SMRA', 'PTPP', 'WSKT', 'WIKA', 'WTON', 'TOTL', 'ASRI',
                                  'BEST', 'BIKA', 'BKDP', 'BKSL', 'CASA', 'DART', 'DFAM', 'DIGI', 'DLTA',
                                  'DMAS', 'DUTI', 'ELTY', 'EMDE', 'ESTI', 'FORU', 'GMTD', 'GPRA', 'INPP',
                                  'JRPT', 'KPIG', 'LPCK', 'LPGI', 'LPKR', 'MDLN', 'MKPI', 'PLAS', 'PLIN',
                                  'POLA', 'PPRE', 'PUDP', 'SATU', 'SMRA', 'TRIL', 'URBN', 'WEHA'],
        'Infrastructure & Transportation': ['JSMR', 'ACST', 'ADHI', 'GJTL', 'HITS', 'IATA', 'IKAN', 'IMJS',
                                            'INDY', 'IPCC', 'ITMA', 'JTPE', 'KARW', 'KIJA', 'META', 'SMBR',
                                            'TMAS', 'TURI', 'WEGE', 'WTRA', 'ASSA', 'BULL', 'BUVA', 'DGIK'],
        'Manufacturing & Industrial': ['INTP', 'UNTR', 'CPIN', 'SMGR', 'SRIL', 'AALI', 'ABBA', 'ACES',
                                      'ADMF', 'AGRO', 'AKKU', 'AKSI', 'ALDO', 'ALTO', 'AMAG', 'AMIN',
                                      'AMOR', 'APLI', 'ARCI', 'ASGR', 'ASMI', 'ASPM', 'AVIA', 'BBRM',
                                      'BCAP', 'BEKS', 'BELL', 'BOLT', 'BRNA', 'BRAM', 'BTO', 'BUKK',
                                      'CAMP', 'CARS', 'CEKA', 'CHEM', 'CINT', 'CITA', 'CLAY', 'CLEO'],
        'Healthcare & Pharmacy': ['KLBF', 'KAEF', 'MERK', 'PYFA', 'SCPI', 'SIDO', 'SOHO', 'SRAJ', 'TSPC', 'UNSP'],
        'Telecom, Technology & Media': ['TLKM', 'EXCL', 'ISAT', 'FREN', 'TBIG', 'MNCN', 'BALI', 'LINK',
                                        'MSIN', 'SCMA', 'BMTR', 'BTEL', 'CENT', 'DIVA', 'DMMX', 'EMTK',
                                        'GIAA', 'HAIS', 'HDIT', 'HDTX', 'MORA', 'NFCX', 'PTSN', 'TOWR'],
        'Other': ['GOTO', 'BUKA', 'MAPI', 'MTEL', 'POLY', 'SAME', 'SCCO', 'SGER', 'SMAR', 'SONA']
    }
    
    for sector, tickers in sector_breakdown.items():
        ticker_list = [t + '.JK' for t in tickers]
        matched = len([t for t in ticker_list if t in complete_tickers])
        print(f"   {sector}: {matched}/{len(tickers)}")
    
    print("\n" + "=" * 80)
    print(f"✅ RINGKASAN: {len(final_tickers)} ticker IDX siap untuk pengambilan data")
    print("=" * 80)
    
    return final_tickers

if __name__ == "__main__":
    final_tickers = analyze_tickers()
