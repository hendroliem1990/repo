#!/usr/bin/env python3
"""
Script to get comprehensive IDX ticker list
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import json

def get_idx_tickers_comprehensive():
    """
    Get comprehensive list of IDX tickers from multiple sources
    """
    tickers = set()

    print("🔍 Gathering IDX tickers from multiple sources...")

    # Source 1: Try IDX CSV (with different headers)
    try:
        url = "https://www.idx.co.id/Portals/0/StaticData/ListedCompanies/StockCode.csv"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/csv,application/csv,text/plain',
            'Referer': 'https://www.idx.co.id/'
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            df = pd.read_csv(pd.io.common.StringIO(response.text))
            if 'Kode Saham' in df.columns:
                csv_tickers = [f"{ticker}.JK" for ticker in df['Kode Saham'].dropna().unique() if ticker]
                tickers.update(csv_tickers)
                print(f"✅ CSV Source: {len(csv_tickers)} tickers")
    except Exception as e:
        print(f"⚠ CSV source failed: {e}")

    # Source 2: Scrape from IDX stock list page
    try:
        url = "https://www.idx.co.id/en/market-data/stocks-data/stock-list/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for ticker symbols in various formats
        ticker_patterns = soup.find_all(['td', 'div', 'span'], class_=lambda x: x and ('ticker' in x.lower() or 'symbol' in x.lower()))

        for element in ticker_patterns:
            text = element.get_text().strip()
            if text and len(text) <= 4 and text.replace('.', '').isalnum():
                tickers.add(f"{text}.JK")

        # Also look for tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cells = row.find_all('td')
                if cells:
                    ticker_cell = cells[0].get_text().strip()
                    if ticker_cell and len(ticker_cell) <= 4:
                        tickers.add(f"{ticker_cell}.JK")

        print(f"✅ Web scraping: {len(tickers)} tickers so far")
    except Exception as e:
        print(f"⚠ Web scraping failed: {e}")

    # Source 3: Use Yahoo Finance to get all Indonesian stocks
    try:
        yahoo_tickers = get_yahoo_indonesian_tickers()
        tickers.update(yahoo_tickers)
        print(f"✅ Yahoo Finance: {len(yahoo_tickers)} tickers added")
    except Exception as e:
        print(f"⚠ Yahoo Finance failed: {e}")

    # Source 4: Load from local comprehensive list
    try:
        comprehensive_list = load_comprehensive_ticker_list()
        tickers.update(comprehensive_list)
        print(f"✅ Comprehensive list: {len(comprehensive_list)} tickers added")
    except Exception as e:
        print(f"⚠ Comprehensive list failed: {e}")

    # Clean and validate tickers
    valid_tickers = []
    for ticker in tickers:
        ticker = ticker.strip().upper()
        if ticker.endswith('.JK') and len(ticker) <= 8:  # .JK + 4 chars max
            valid_tickers.append(ticker)

    valid_tickers = sorted(list(set(valid_tickers)))

    print(f"🎯 Final ticker count: {len(valid_tickers)}")
    return valid_tickers

def get_yahoo_indonesian_tickers():
    """
    Get all Indonesian tickers from Yahoo Finance
    """
    import yfinance as yf
    import time

    # List of known Indonesian exchanges/codes
    exchanges = ['JK']  # Jakarta exchange

    all_tickers = set()

    # Method 1: Try to get tickers by downloading in batches
    # We'll try downloading some known tickers first to see what works
    test_tickers = [
        'BBCA.JK', 'BBRI.JK', 'ASII.JK', 'TLKM.JK', 'UNVR.JK', 'ICBP.JK', 'INDF.JK', 'ANTM.JK', 'ADRO.JK'
    ]

    working_tickers = []
    for ticker in test_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if info and 'symbol' in info:
                working_tickers.append(ticker)
                time.sleep(0.1)  # Be respectful
        except:
            continue

    print(f"Found {len(working_tickers)} working tickers from test list")

    # Method 2: Generate potential ticker combinations
    # Indonesian tickers are typically 4 characters or less
    import string
    potential_tickers = []

    # Common prefixes and patterns
    prefixes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    suffixes = ['', 'A', 'B', 'C', 'D', 'I', 'J', 'N', 'O', 'P', 'R', 'S', 'T']

    for prefix in prefixes:
        for i in range(1, 5):  # 1-4 characters
            for suffix in suffixes:
                ticker = prefix + str(i) + suffix
                if len(ticker) <= 4:
                    potential_tickers.append(f"{ticker}.JK")

    # Also add some known longer tickers
    known_tickers = [
        'GOTO.JK', 'BUKA.JK', 'MAPI.JK', 'MTEL.JK', 'POLY.JK', 'SAME.JK', 'SCCO.JK', 'SGER.JK', 'SMAR.JK', 'SONA.JK',
        'SQMI.JK', 'SRTG.JK', 'SSMS.JK', 'TAMA.JK', 'TAMU.JK', 'TAXI.JK', 'TELE.JK', 'TFCO.JK', 'TGKA.JK', 'TINS.JK',
        'TIRA.JK', 'TKIM.JK', 'TMPO.JK', 'TNCA.JK', 'TOBA.JK', 'TOPS.JK', 'TOTO.JK', 'TPMA.JK', 'TRAM.JK', 'TRIO.JK',
        'TRIS.JK', 'TRJA.JK', 'TRST.JK', 'TRUK.JK', 'TUGU.JK', 'ULTJ.JK', 'UNIC.JK', 'URBN.JK', 'UVCR.JK', 'VICO.JK',
        'VINS.JK', 'VIVA.JK', 'VOKS.JK', 'WAPO.JK', 'WEGE.JK', 'WGSH.JK', 'WIIM.JK', 'WINS.JK', 'WOMF.JK', 'WONN.JK',
        'WSBP.JK', 'YELO.JK', 'YPAS.JK', 'YULE.JK', 'ZBRA.JK', 'ZONE.JK', 'ZYRX.JK', 'NFCX.JK', 'CASH.JK', 'DAYA.JK'
    ]

    potential_tickers.extend(known_tickers)

    # Test a sample of potential tickers (to avoid too many requests)
    sample_size = min(2000, len(potential_tickers))  # Test up to 2000
    import random
    test_sample = random.sample(potential_tickers, sample_size)

    print(f"Testing {len(test_sample)} potential tickers...")

    for i, ticker in enumerate(test_sample):
        try:
            if i % 100 == 0:
                print(f"Tested {i}/{len(test_sample)} tickers...")

            stock = yf.Ticker(ticker)
            # Try to get basic info
            hist = stock.history(period="1d")
            if not hist.empty:
                all_tickers.add(ticker)
                time.sleep(0.05)  # Small delay
        except:
            time.sleep(0.05)
            continue

    print(f"Found {len(all_tickers)} valid tickers from Yahoo Finance")
    return list(all_tickers)
    """
    Load a comprehensive list of IDX tickers
    This is an extended version of the fallback list
    """
    return [
        # Banking & Finance (50+)
        'BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'BBNI.JK', 'BRIS.JK', 'BNGA.JK', 'BDMN.JK', 'BNLI.JK', 'BJBR.JK', 'BJTM.JK',
        'INPC.JK', 'NISP.JK', 'PNBN.JK', 'SDRA.JK', 'AGRO.JK', 'BFIN.JK', 'BBKP.JK', 'BBMD.JK', 'BBTN.JK', 'BBSI.JK',
        'BBYB.JK', 'BCIC.JK', 'BDKR.JK', 'BEKS.JK', 'BGTG.JK', 'BHIT.JK', 'BINA.JK', 'BKSW.JK', 'BMAS.JK', 'BVIC.JK',
        'CFIN.JK', 'DANP.JK', 'HDFA.JK', 'LPPS.JK', 'MAYA.JK', 'MEGA.JK', 'NOBU.JK', 'PBID.JK', 'PGLI.JK', 'PNLF.JK',
        'RELI.JK', 'SDMU.JK', 'SKYB.JK', 'SOFA.JK', 'TRIM.JK', 'VRNA.JK', 'BTPS.JK', 'HDFC.JK', 'PBSA.JK', 'TCPI.JK',

        # Consumer Goods & Retail (80+)
        'ASII.JK', 'UNVR.JK', 'ICBP.JK', 'INDF.JK', 'MYOR.JK', 'HMSP.JK', 'GGRM.JK', 'ULTJ.JK', 'KLBF.JK', 'TSPC.JK',
        'ADES.JK', 'ADMG.JK', 'AGII.JK', 'AKRA.JK', 'ALKA.JK', 'ALMI.JK', 'AMFG.JK', 'AMRT.JK', 'APEX.JK', 'APII.JK',
        'APLN.JK', 'ARGO.JK', 'ARNA.JK', 'ASSA.JK', 'AUTO.JK', 'BAPA.JK', 'BATA.JK', 'BAYU.JK', 'BEER.JK', 'BIMA.JK',
        'BINO.JK', 'BJTM.JK', 'BKSL.JK', 'BLTA.JK', 'BLUE.JK', 'BMTR.JK', 'BOGA.JK', 'BRAM.JK', 'BRNA.JK', 'BRPT.JK',
        'BSIM.JK', 'BTON.JK', 'BUDI.JK', 'BUKK.JK', 'CAMP.JK', 'CARS.JK', 'CEKA.JK', 'CENT.JK', 'CHEM.JK', 'CINT.JK',
        'CITA.JK', 'CLAY.JK', 'CLEO.JK', 'CLPI.JK', 'CMNP.JK', 'CNMA.JK', 'COCO.JK', 'CPRO.JK', 'CSAP.JK', 'CTBN.JK',
        'DART.JK', 'DEPO.JK', 'DFAM.JK', 'DIGI.JK', 'DLTA.JK', 'DMND.JK', 'DPNS.JK', 'DSFI.JK', 'DSNG.JK', 'DUTI.JK',
        'DVLA.JK', 'DYAN.JK', 'ECII.JK', 'EKAD.JK', 'ELSA.JK', 'ELTY.JK', 'EMDE.JK', 'EMTK.JK', 'ENZO.JK', 'EPAC.JK',
        'ERAA.JK', 'ERTX.JK', 'ESTI.JK', 'ETWA.JK', 'EXCL.JK', 'FAST.JK', 'FISH.JK', 'FMII.JK', 'FORU.JK', 'FPNI.JK',

        # Telecom, Technology & Media (30+)
        'TLKM.JK', 'EXCL.JK', 'ISAT.JK', 'FREN.JK', 'TBIG.JK', 'MNCN.JK', 'BALI.JK', 'LINK.JK', 'MSIN.JK', 'SCMA.JK',
        'BMTR.JK', 'BTEL.JK', 'CENT.JK', 'DIVA.JK', 'DMMX.JK', 'EMTK.JK', 'GIAA.JK', 'HAIS.JK', 'HDIT.JK', 'HDTX.JK',
        'MORA.JK', 'NFCX.JK', 'PTSN.JK', 'SUPR.JK', 'TOWR.JK', 'TRON.JK', 'WIFI.JK', 'ZYRX.JK', 'MLPT.JK', 'INET.JK',

        # Mining & Energy (60+)
        'ANTM.JK', 'ADRO.JK', 'PTBA.JK', 'ITMG.JK', 'BYAN.JK', 'MEDC.JK', 'PGAS.JK', 'ENRG.JK', 'ELSA.JK', 'HRUM.JK',
        'ABMM.JK', 'AKPI.JK', 'APIC.JK', 'ARII.JK', 'BANG.JK', 'BIPI.JK', 'BOSS.JK', 'BRMS.JK', 'BSSR.JK', 'BUMI.JK',
        'CNKO.JK', 'CTRA.JK', 'DEWA.JK', 'DOID.JK', 'DSSA.JK', 'DWGL.JK', 'DYAN.JK', 'EKAD.JK', 'EMKR.JK', 'ENAK.JK',
        'GEMS.JK', 'GTBO.JK', 'HERO.JK', 'ITMA.JK', 'KKGI.JK', 'MBAP.JK', 'MITI.JK', 'MYOH.JK', 'PGJO.JK', 'PTRO.JK',
        'SAME.JK', 'SCCO.JK', 'SMMT.JK', 'SOCI.JK', 'TINS.JK', 'TOBA.JK', 'UNTR.JK', 'WOWS.JK', 'ZINC.JK', 'BORN.JK',

        # Property & Real Estate (70+)
        'BSDE.JK', 'PWON.JK', 'SMRA.JK', 'PTPP.JK', 'WSKT.JK', 'WIKA.JK', 'WTON.JK', 'TOTL.JK', 'SSIA.JK', 'ASRI.JK',
        'BEST.JK', 'BIKA.JK', 'BKDP.JK', 'BKSL.JK', 'CASA.JK', 'DART.JK', 'DFAM.JK', 'DIGI.JK', 'DMAS.JK', 'DUTI.JK',
        'ELTY.JK', 'EMDE.JK', 'ESTI.JK', 'FORU.JK', 'GMTD.JK', 'GPRA.JK', 'INPP.JK', 'JRPT.JK', 'KPIG.JK', 'LPCK.JK',
        'LPSG.JK', 'MDRN.JK', 'MKPI.JK', 'PLIN.JK', 'POLA.JK', 'PPRE.JK', 'PUDP.JK', 'RBMS.JK', 'RDTX.JK', 'RMBA.JK',
        'ROTI.JK', 'SATU.JK', 'TIRT.JK', 'TRIL.JK', 'URBN.JK', 'WEHA.JK', 'WICO.JK', 'WTON.JK', 'YELO.JK', 'APLII.JK',
        'BIPP.JK', 'COWL.JK', 'DILD.JK', 'FMII.JK', 'GPRA.JK', 'HOME.JK', 'INDO.JK', 'JRPT.JK', 'KIOS.JK', 'LIFE.JK',
        'LPCK.JK', 'MKPI.JK', 'PLAS.JK', 'POLA.JK', 'PPRE.JK', 'RBMS.JK', 'RDTX.JK', 'RMBA.JK', 'ROTI.JK', 'SATU.JK',

        # Infrastructure & Transportation (40+)
        'JSMR.JK', 'ACST.JK', 'ADHI.JK', 'ASSA.JK', 'BULL.JK', 'BUVA.JK', 'DGIK.JK', 'GJTL.JK', 'HITS.JK', 'IATA.JK',
        'IKAN.JK', 'IMJS.JK', 'INDY.JK', 'IPCC.JK', 'ITMA.JK', 'JTPE.JK', 'KARW.JK', 'KIJA.JK', 'META.JK', 'SMBR.JK',
        'TMAS.JK', 'TURI.JK', 'WEGE.JK', 'WTRA.JK', 'AKSI.JK', 'APII.JK', 'BIMA.JK', 'BPTR.JK', 'CMPP.JK', 'DEAL.JK',
        'FAST.JK', 'HEXA.JK', 'INDX.JK', 'IPCM.JK', 'JAYA.JK', 'KPAL.JK', 'LRNA.JK', 'MIRA.JK', 'NELY.JK', 'PORT.JK',

        # Manufacturing & Industrial (100+)
        'INTP.JK', 'UNTR.JK', 'CPIN.JK', 'JPFA.JK', 'MAIN.JK', 'SMGR.JK', 'SRIL.JK', 'AMRT.JK', 'MPPA.JK', 'SILO.JK',
        'AALI.JK', 'ABBA.JK', 'ACES.JK', 'ADMF.JK', 'AGRO.JK', 'AKKU.JK', 'AKSI.JK', 'ALDO.JK', 'ALTO.JK', 'AMAG.JK',
        'AMIN.JK', 'AMOR.JK', 'ANJT.JK', 'APLI.JK', 'ARCI.JK', 'ASGR.JK', 'ASMI.JK', 'ASPM.JK', 'ASRI.JK', 'AVIA.JK',
        'BBRM.JK', 'BCAP.JK', 'BEKS.JK', 'BELL.JK', 'BOLT.JK', 'BRNA.JK', 'BTON.JK', 'BUKK.JK', 'CAMP.JK', 'CARS.JK',
        'CEKA.JK', 'CHEM.JK', 'CINT.JK', 'CITA.JK', 'CLAY.JK', 'CLEO.JK', 'CLPI.JK', 'CNMA.JK', 'COCO.JK', 'CPRO.JK',
        'CSAP.JK', 'CTBN.JK', 'CTRA.JK', 'DEPO.JK', 'DFAM.JK', 'DIGI.JK', 'DLTA.JK', 'DMND.JK', 'DPNS.JK', 'DSFI.JK',
        'DSNG.JK', 'DVLA.JK', 'EKAD.JK', 'ELSA.JK', 'EMTK.JK', 'ENRG.JK', 'ENZO.JK', 'EPAC.JK', 'ERAA.JK', 'ERTX.JK',
        'ETWA.JK', 'FAST.JK', 'FISH.JK', 'FMII.JK', 'FORU.JK', 'FPNI.JK', 'GDST.JK', 'GDYR.JK', 'GEMA.JK', 'GEMS.JK',
        'GIAA.JK', 'GJTL.JK', 'GMTD.JK', 'GOLD.JK', 'GPRA.JK', 'GSMF.JK', 'GTBO.JK', 'GWSA.JK', 'HAIS.JK', 'HDFA.JK',
        'HDIT.JK', 'HDTX.JK', 'HEAL.JK', 'HELI.JK', 'HERO.JK', 'HEXA.JK', 'HITS.JK', 'HKMU.JK', 'HMSP.JK', 'HOKI.JK',
        'HOME.JK', 'HOTL.JK', 'HRTA.JK', 'HRUM.JK', 'IATA.JK', 'IBFN.JK', 'IBST.JK', 'ICON.JK', 'IDPR.JK', 'IFSH.JK',

        # Healthcare & Pharmacy (20+)
        'KLBF.JK', 'KAEF.JK', 'MERK.JK', 'PYFA.JK', 'SCPI.JK', 'SIDO.JK', 'SOHO.JK', 'SRAJ.JK', 'TSPC.JK', 'UNSP.JK',
        'DVLA.JK', 'HEAL.JK', 'INAF.JK', 'IRRA.JK', 'ITIC.JK', 'KEJU.JK', 'MEDS.JK', 'MIKA.JK', 'PEHA.JK', 'PRIM.JK',

        # Miscellaneous & Other Sectors (100+)
        'GOTO.JK', 'BUKA.JK', 'MAPI.JK', 'MTEL.JK', 'POLY.JK', 'SAME.JK', 'SCCO.JK', 'SGER.JK', 'SMAR.JK', 'SONA.JK',
        'SQMI.JK', 'SRTG.JK', 'SSMS.JK', 'TAMA.JK', 'TAMU.JK', 'TAXI.JK', 'TELE.JK', 'TFCO.JK', 'TGKA.JK', 'TINS.JK',
        'TIRA.JK', 'TKIM.JK', 'TMPO.JK', 'TNCA.JK', 'TOBA.JK', 'TOPS.JK', 'TOTO.JK', 'TPMA.JK', 'TRAM.JK', 'TRIO.JK',
        'TRIS.JK', 'TRJA.JK', 'TRST.JK', 'TRUK.JK', 'TUGU.JK', 'ULTJ.JK', 'UNIC.JK', 'URBN.JK', 'UVCR.JK', 'VICO.JK',
        'VINS.JK', 'VIVA.JK', 'VOKS.JK', 'WAPO.JK', 'WEGE.JK', 'WGSH.JK', 'WIIM.JK', 'WINS.JK', 'WOMF.JK', 'WONN.JK',
        'WSBP.JK', 'YELO.JK', 'YPAS.JK', 'YULE.JK', 'ZBRA.JK', 'ZONE.JK', 'ZYRX.JK', 'NFCX.JK', 'CASH.JK', 'DAYA.JK',
        'DEWA.JK', 'DOID.JK', 'DSSA.JK', 'DWGL.JK', 'EKAD.JK', 'EMKR.JK', 'ENAK.JK', 'GEMS.JK', 'GTBO.JK', 'HERO.JK',
        'ITMA.JK', 'KKGI.JK', 'MBAP.JK', 'MITI.JK', 'MYOH.JK', 'PGJO.JK', 'PTRO.JK', 'SAME.JK', 'SCCO.JK', 'SMMT.JK',
        'SOCI.JK', 'TINS.JK', 'TOBA.JK', 'UNTR.JK', 'WOWS.JK', 'ZINC.JK', 'BORN.JK', 'ABMM.JK', 'AKPI.JK', 'APIC.JK',
        'ARII.JK', 'BANG.JK', 'BIPI.JK', 'BOSS.JK', 'BRMS.JK', 'BSSR.JK', 'BUMI.JK', 'CNKO.JK', 'CTRA.JK', 'DEWA.JK'
    ]

if __name__ == "__main__":
    tickers = get_idx_tickers_comprehensive()
    print(f"Total tickers found: {len(tickers)}")

    # Save to file
    with open('/workspaces/repo/comprehensive_idx_tickers.json', 'w') as f:
        json.dump(tickers, f, indent=2)

    print("Saved to comprehensive_idx_tickers.json")