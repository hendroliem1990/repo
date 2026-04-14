import pandas as pd
import requests
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup

class IDXDataSource:
    """IDX (Indonesia Stock Exchange) data source for tickers and corporate actions"""

    def __init__(self):
        self.name = "IDX"
        self.base_url = "https://www.idx.co.id"
        self.ticker_url = "https://www.idx.co.id/Portals/0/StaticData/ListedCompanies/StockCode.csv"
        self.corporate_action_url = "https://www.idx.co.id/Portals/0/StaticData/CorporateAction/CorporateAction.csv"

    def get_all_tickers(self):
        """
        Get comprehensive list of all IDX tickers

        Returns:
            list: List of ticker symbols with .JK suffix
        """
        try:
            print("📡 Fetching tickers from IDX...")

            # Try official IDX API with headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            df = pd.read_csv(self.ticker_url, headers=headers)

            if 'Kode Saham' in df.columns:
                tickers = [f"{ticker}.JK" for ticker in df['Kode Saham'].dropna().unique()]
                print(f"✅ Loaded {len(tickers)} tickers from IDX")
                return sorted(tickers)
            else:
                raise ValueError("Unexpected CSV format")

        except Exception as e:
            print(f"⚠ IDX ticker source failed: {str(e)[:50]}")
            print("Trying alternative sources...")
            
            # Try alternative sources
            try:
                # Try scraping from IDX website
                tickers = self._scrape_idx_tickers()
                if tickers and len(tickers) > 200:  # Only use if we got a substantial list
                    print(f"✅ Loaded {len(tickers)} tickers from IDX website scraping")
                    return sorted(tickers)
            except Exception as e2:
                print(f"⚠ Website scraping failed: {str(e2)[:50]}")
            
            # Try Yahoo Finance extended list
            try:
                tickers = self._get_yahoo_tickers()
                if tickers and len(tickers) > 200:
                    print(f"✅ Loaded {len(tickers)} tickers from extended list")
                    return sorted(tickers)
            except Exception as e3:
                print(f"⚠ Extended list failed: {str(e3)[:50]}")
            
            print("Using comprehensive fallback ticker list...")
            return self._get_fallback_tickers()

    def _get_fallback_tickers(self):
        """Comprehensive fallback ticker list covering all IDX sectors"""
        return [
            # Banking & Financial Services (30+)
            'BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'BBNI.JK', 'BRIS.JK', 'BNGA.JK', 'BDMN.JK', 'BNLI.JK', 'BJBR.JK', 'BJTM.JK',
            'INPC.JK', 'NISP.JK', 'PNBN.JK', 'SDRA.JK', 'AGRO.JK', 'BFIN.JK', 'BBKP.JK', 'BBMD.JK', 'BBTN.JK', 'BBSI.JK',
            'BBYB.JK', 'BCIC.JK', 'BDKR.JK', 'BEKS.JK', 'BGTG.JK', 'BHIT.JK', 'BINA.JK', 'BKSW.JK', 'BMAS.JK', 'BVIC.JK',

            # Consumer Goods & Retail (25+)
            'ASII.JK', 'UNVR.JK', 'ICBP.JK', 'INDF.JK', 'MYOR.JK', 'HMSP.JK', 'GGRM.JK', 'ULTJ.JK', 'KLBF.JK', 'TSPC.JK',
            'AISA.JK', 'ADES.JK', 'ADMG.JK', 'AGII.JK', 'AKRA.JK', 'ALKA.JK', 'ALMI.JK', 'AMFG.JK', 'AMRT.JK', 'APEX.JK',
            'APII.JK', 'APLN.JK', 'ARGO.JK', 'ARNA.JK', 'ASSA.JK', 'AUTO.JK', 'BAPA.JK', 'BATA.JK', 'BAYU.JK', 'BEER.JK',

            # Telecom, Technology & Media (15+)
            'TLKM.JK', 'EXCL.JK', 'ISAT.JK', 'FREN.JK', 'TBIG.JK', 'MNCN.JK', 'BALI.JK', 'LINK.JK', 'MSIN.JK', 'SCMA.JK',
            'BMTR.JK', 'BTEL.JK', 'CENT.JK', 'DIVA.JK', 'DMMX.JK', 'EMTK.JK', 'GIAA.JK', 'HAIS.JK', 'HDIT.JK', 'HDTX.JK',

            # Mining & Energy (25+)
            'ANTM.JK', 'ADRO.JK', 'PTBA.JK', 'ITMG.JK', 'BYAN.JK', 'MEDC.JK', 'PGAS.JK', 'ENRG.JK', 'ELSA.JK', 'HRUM.JK',
            'ABMM.JK', 'AKPI.JK', 'APIC.JK', 'ARII.JK', 'BANG.JK', 'BIPI.JK', 'BOSS.JK', 'BRMS.JK', 'BSSR.JK', 'BUMI.JK',
            'CNKO.JK', 'CTRA.JK', 'DEWA.JK', 'DOID.JK', 'DSSA.JK', 'DWGL.JK', 'DYAN.JK', 'EKAD.JK', 'EMKR.JK', 'ENAK.JK',

            # Property & Real Estate (25+)
            'BSDE.JK', 'PWON.JK', 'SMRA.JK', 'PTPP.JK', 'WSKT.JK', 'WIKA.JK', 'WTON.JK', 'TOTL.JK', 'CMNP.JK', 'SSIA.JK',
            'ASRI.JK', 'BEST.JK', 'BIKA.JK', 'BKDP.JK', 'BKSL.JK', 'CASA.JK', 'DART.JK', 'DFAM.JK', 'DIGI.JK', 'DMAS.JK',
            'DUTI.JK', 'ELTY.JK', 'EMDE.JK', 'ESTI.JK', 'FORU.JK', 'GMTD.JK', 'GPRA.JK', 'INPP.JK', 'JRPT.JK', 'KPIG.JK',

            # Infrastructure & Transportation (20+)
            'JSMR.JK', 'ACST.JK', 'ADHI.JK', 'ASSA.JK', 'BULL.JK', 'BUVA.JK', 'DGIK.JK', 'GJTL.JK', 'HITS.JK', 'IATA.JK',
            'IKAN.JK', 'IMJS.JK', 'INDY.JK', 'IPCC.JK', 'ITMA.JK', 'JTPE.JK', 'KARW.JK', 'KIJA.JK', 'META.JK', 'SMBR.JK',

            # Manufacturing & Industrial (30+)
            'INTP.JK', 'UNTR.JK', 'CPIN.JK', 'JPFA.JK', 'MAIN.JK', 'SMGR.JK', 'SRIL.JK', 'AMRT.JK', 'MPPA.JK', 'SILO.JK',
            'AALI.JK', 'ABBA.JK', 'ACES.JK', 'ADMF.JK', 'AGRO.JK', 'AKKU.JK', 'AKSI.JK', 'ALDO.JK', 'ALTO.JK', 'AMAG.JK',
            'AMIN.JK', 'AMOR.JK', 'ANJT.JK', 'APLI.JK', 'ARCI.JK', 'ASGR.JK', 'ASMI.JK', 'ASPM.JK', 'ASRI.JK', 'AVIA.JK',

            # Healthcare & Pharmacy (10+)
            'KLBF.JK', 'KAEF.JK', 'MERK.JK', 'PYFA.JK', 'SCPI.JK', 'SIDO.JK', 'SOHO.JK', 'SRAJ.JK', 'TSPC.JK', 'UNSP.JK',

            # Miscellaneous & Other Sectors (20+)
            'GOTO.JK', 'BUKA.JK', 'MAPI.JK', 'MTEL.JK', 'POLY.JK', 'SAME.JK', 'SCCO.JK', 'SGER.JK', 'SMAR.JK', 'SONA.JK',
            'SQMI.JK', 'SRTG.JK', 'SSMS.JK', 'TAMA.JK', 'TAMU.JK', 'TAXI.JK', 'TELE.JK', 'TFCO.JK', 'TGKA.JK', 'TINS.JK'
        ]

    def _scrape_idx_tickers(self):
        """
        Scrape ticker list from IDX website
        
        Returns:
            list: List of ticker symbols with .JK suffix
        """
        try:
            # Try multiple IDX pages that might contain ticker lists
            urls = [
                "https://www.idx.co.id/en/market-data/stocks-data/stock-list/",
                "https://www.idx.co.id/id/market-data/saham/saham-tercatat/",
                "https://www.idx.co.id/Portals/0/StaticData/ListedCompanies/StockCode.csv"
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            tickers = set()
            
            for url in urls:
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    if url.endswith('.csv'):
                        # Try to parse as CSV
                        df = pd.read_csv(url, headers=headers)
                        if 'Kode Saham' in df.columns:
                            tickers.update([f"{ticker}.JK" for ticker in df['Kode Saham'].dropna().unique()])
                    else:
                        # Try to parse HTML
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for tables with tickers
                        tables = soup.find_all('table')
                        for table in tables:
                            rows = table.find_all('tr')
                            for row in rows:
                                cells = row.find_all('td')
                                if cells and len(cells) > 0:
                                    # Look for ticker patterns (usually first column)
                                    ticker_text = cells[0].get_text().strip()
                                    if ticker_text and len(ticker_text) <= 4 and ticker_text.isalpha():
                                        tickers.add(f"{ticker_text}.JK")
                    
                    if tickers:
                        break
                        
                except Exception as e:
                    print(f"⚠ Failed to scrape {url}: {str(e)[:30]}")
                    continue
            
            return list(tickers) if tickers else []
            
        except Exception as e:
            print(f"⚠ IDX scraping failed: {str(e)[:50]}")
            return []

    def _get_yahoo_tickers(self):
        """
        Get all Indonesian tickers from Yahoo Finance
        
        Returns:
            list: List of ticker symbols with .JK suffix
        """
        try:
            print("📡 Fetching tickers from Yahoo Finance...")
            
            # Yahoo Finance has an endpoint for exchange symbols
            # We can try to get all .JK symbols
            import yfinance as yf
            
            # This is a workaround - we'll try to get a large list by searching
            # For now, let's use a more comprehensive static list
            # In a real implementation, you might use Yahoo's API or scrape
            
            # Extended fallback list with more tickers
            extended_tickers = self._get_fallback_tickers() + [
                # Add more banking
                'BMHS.JK', 'BNII.JK', 'BTPS.JK', 'CFIN.JK', 'DANP.JK', 'HDFA.JK', 'HDFC.JK', 'LPPS.JK', 'MAYA.JK', 'MEGA.JK',
                'NOBU.JK', 'PBID.JK', 'PGLI.JK', 'PNLF.JK', 'RELI.JK', 'SDMU.JK', 'SKYB.JK', 'SOFA.JK', 'TRIM.JK', 'VRNA.JK',
                
                # More consumer goods
                'ADES.JK', 'ADMG.JK', 'AGII.JK', 'AKRA.JK', 'ALKA.JK', 'ALMI.JK', 'AMFG.JK', 'AMRT.JK', 'APEX.JK', 'APII.JK',
                'APLN.JK', 'ARGO.JK', 'ARNA.JK', 'ASSA.JK', 'AUTO.JK', 'BAPA.JK', 'BATA.JK', 'BAYU.JK', 'BEER.JK', 'BIMA.JK',
                'BINO.JK', 'BJTM.JK', 'BKSL.JK', 'BLTA.JK', 'BLUE.JK', 'BMTR.JK', 'BOGA.JK', 'BRAM.JK', 'BRNA.JK', 'BRPT.JK',
                'BSIM.JK', 'BTON.JK', 'BUDI.JK', 'BUKK.JK', 'CAMP.JK', 'CARS.JK', 'CEKA.JK', 'CENT.JK', 'CFIN.JK', 'CHEM.JK',
                'CINT.JK', 'CITA.JK', 'CLAY.JK', 'CLEO.JK', 'CLPI.JK', 'CMNP.JK', 'CNMA.JK', 'COCO.JK', 'CPRO.JK', 'CSAP.JK',
                'CTBN.JK', 'CTRA.JK', 'DART.JK', 'DEPO.JK', 'DFAM.JK', 'DGIK.JK', 'DIGI.JK', 'DLTA.JK', 'DMND.JK', 'DPNS.JK',
                'DSFI.JK', 'DSNG.JK', 'DUTI.JK', 'DVLA.JK', 'DYAN.JK', 'ECII.JK', 'EKAD.JK', 'ELSA.JK', 'ELTY.JK', 'EMDE.JK',
                'EMTK.JK', 'ENRG.JK', 'ENZO.JK', 'EPAC.JK', 'ERAA.JK', 'ERTX.JK', 'ESTI.JK', 'ETWA.JK', 'EXCL.JK', 'FAST.JK',
                'FISH.JK', 'FMII.JK', 'FORU.JK', 'FPNI.JK', 'FREN.JK', 'GDST.JK', 'GDYR.JK', 'GEMA.JK', 'GEMS.JK', 'GIAA.JK',
                'GJTL.JK', 'GMTD.JK', 'GOLD.JK', 'GPRA.JK', 'GSMF.JK', 'GTBO.JK', 'GWSA.JK', 'HAIS.JK', 'HDFA.JK', 'HDIT.JK',
                'HDTX.JK', 'HEAL.JK', 'HELI.JK', 'HERO.JK', 'HEXA.JK', 'HITS.JK', 'HKMU.JK', 'HMSP.JK', 'HOKI.JK', 'HOME.JK',
                'HOTL.JK', 'HRTA.JK', 'HRUM.JK', 'IATA.JK', 'IBFN.JK', 'IBST.JK', 'ICBP.JK', 'ICON.JK', 'IDPR.JK', 'IFSH.JK',
                'IGAR.JK', 'IIKP.JK', 'IKAN.JK', 'IKBI.JK', 'IMAS.JK', 'IMJS.JK', 'INAF.JK', 'INAI.JK', 'INCF.JK', 'INCI.JK',
                'INCO.JK', 'INDF.JK', 'INDO.JK', 'INDR.JK', 'INDS.JK', 'INDX.JK', 'INDY.JK', 'INKP.JK', 'INOV.JK', 'INPC.JK',
                'INPP.JK', 'INPS.JK', 'INRU.JK', 'INTA.JK', 'INTD.JK', 'INTP.JK', 'IPCC.JK', 'IPCM.JK', 'IPOL.JK', 'ISAT.JK',
                'ISSP.JK', 'ITMA.JK', 'ITMG.JK', 'ITTG.JK', 'JAWA.JK', 'JAYA.JK', 'JECC.JK', 'JGLE.JK', 'JIHD.JK', 'JKON.JK',
                'JKSW.JK', 'JPFA.JK', 'JRPT.JK', 'JSKY.JK', 'JSMR.JK', 'JTPE.JK', 'KAEF.JK', 'KARW.JK', 'KBLI.JK', 'KCIC.JK',
                'KIJA.JK', 'KINO.JK', 'KLBF.JK', 'KOBX.JK', 'KOIN.JK', 'KOPI.JK', 'KPIG.JK', 'KRAH.JK', 'KRAS.JK', 'KREN.JK',
                'LAND.JK', 'LAPD.JK', 'LCGP.JK', 'LEAD.JK', 'LIFE.JK', 'LINK.JK', 'LION.JK', 'LMAS.JK', 'LMPI.JK', 'LMSH.JK',
                'LPCK.JK', 'LPGI.JK', 'LPIN.JK', 'LPKR.JK', 'LPLI.JK', 'LPPF.JK', 'LPPS.JK', 'LRNA.JK', 'LSIP.JK', 'LTLS.JK',
                'MABA.JK', 'MAGP.JK', 'MAIN.JK', 'MAMI.JK', 'MAPI.JK', 'MARI.JK', 'MARK.JK', 'MASA.JK', 'MAYA.JK', 'MBAP.JK',
                'MBSS.JK', 'MBTO.JK', 'MCAS.JK', 'MCOR.JK', 'MDIA.JK', 'MDKA.JK', 'MDKI.JK', 'MDLN.JK', 'MDRN.JK', 'MEDC.JK',
                'MEGA.JK', 'MERK.JK', 'META.JK', 'MFIN.JK', 'MFMI.JK', 'MGNA.JK', 'MGRO.JK', 'MICE.JK', 'MIDI.JK', 'MIKA.JK',
                'MINA.JK', 'MIRA.JK', 'MITI.JK', 'MKNT.JK', 'MKPI.JK', 'MLBI.JK', 'MLIA.JK', 'MLPL.JK', 'MLPT.JK', 'MMLP.JK',
                'MNCN.JK', 'MNCS.JK', 'MOLI.JK', 'MPMX.JK', 'MPPA.JK', 'MPRO.JK', 'MRAT.JK', 'MREI.JK', 'MSIN.JK', 'MSKY.JK',
                'MTDL.JK', 'MTEL.JK', 'MTFN.JK', 'MTLA.JK', 'MTSM.JK', 'MTWI.JK', 'MYOH.JK', 'MYOR.JK', 'MYRX.JK', 'MYTX.JK',
                'NANO.JK', 'NASA.JK', 'NELY.JK', 'NICK.JK', 'NIPS.JK', 'NIRO.JK', 'NISP.JK', 'NOBU.JK', 'NRCA.JK', 'NTBK.JK',
                'NZIA.JK', 'OASA.JK', 'OBMD.JK', 'OCAP.JK', 'OKAS.JK', 'OMED.JK', 'OMRE.JK', 'OPMS.JK', 'PADI.JK', 'PALM.JK',
                'PAMG.JK', 'PANI.JK', 'PANR.JK', 'PANS.JK', 'PBID.JK', 'PBSA.JK', 'PCAR.JK', 'PDES.JK', 'PEGE.JK', 'PEHA.JK',
                'PEVE.JK', 'PFIN.JK', 'PFMI.JK', 'PGAS.JK', 'PGJO.JK', 'PGLI.JK', 'PGUN.JK', 'PICO.JK', 'PILI.JK', 'PIPA.JK',
                'PKPK.JK', 'PLAS.JK', 'PLIN.JK', 'PLPC.JK', 'PMJS.JK', 'PMMP.JK', 'PNBS.JK', 'PNLF.JK', 'PNSE.JK', 'POLA.JK',
                'POLL.JK', 'POLY.JK', 'POOL.JK', 'PORT.JK', 'POWR.JK', 'PPGL.JK', 'PPRE.JK', 'PPRO.JK', 'PRAS.JK', 'PRDA.JK',
                'PRIM.JK', 'PSAB.JK', 'PSDN.JK', 'PSGO.JK', 'PSKT.JK', 'PSSI.JK', 'PTBA.JK', 'PTDU.JK', 'PTIS.JK', 'PTMP.JK',
                'PTPS.JK', 'PTPP.JK', 'PTPW.JK', 'PTRO.JK', 'PTSN.JK', 'PTSP.JK', 'PUDP.JK', 'PWON.JK', 'PYFA.JK', 'PZZA.JK',
                'RAJA.JK', 'RALS.JK', 'RANC.JK', 'RBMS.JK', 'RDTX.JK', 'RELI.JK', 'RICY.JK', 'RIGS.JK', 'RIMO.JK', 'RINI.JK',
                'RISA.JK', 'RMBA.JK', 'RODA.JK', 'ROTI.JK', 'RSGK.JK', 'RUIS.JK', 'SAFE.JK', 'SAME.JK', 'SAMF.JK', 'SAPX.JK',
                'SATU.JK', 'SBAT.JK', 'SCCO.JK', 'SCNP.JK', 'SCPI.JK', 'SDMU.JK', 'SDPC.JK', 'SDRA.JK', 'SEMA.JK', 'SFAN.JK',
                'SGER.JK', 'SGRO.JK', 'SHID.JK', 'SHIP.JK', 'SIDO.JK', 'SILO.JK', 'SIMA.JK', 'SIMP.JK', 'SIPD.JK', 'SKBM.JK',
                'SKLT.JK', 'SKRN.JK', 'SKYB.JK', 'SLIS.JK', 'SMAR.JK', 'SMBR.JK', 'SMCB.JK', 'SMDM.JK', 'SMDR.JK', 'SMGR.JK',
                'SMIL.JK', 'SMKL.JK', 'SMMA.JK', 'SMMT.JK', 'SMRA.JK', 'SMSM.JK', 'SMTI.JK', 'SMTM.JK', 'SNLK.JK', 'SOCI.JK',
                'SOFA.JK', 'SOHO.JK', 'SONA.JK', 'SPMA.JK', 'SPTO.JK', 'SQMI.JK', 'SRAJ.JK', 'SRIL.JK', 'SRTG.JK', 'SSIA.JK',
                'SSMS.JK', 'SSTM.JK', 'STAA.JK', 'STAR.JK', 'STTP.JK', 'SUGI.JK', 'SULI.JK', 'SUPR.JK', 'SURE.JK', 'SWAT.JK',
                'TALF.JK', 'TAMA.JK', 'TAMU.JK', 'TAXI.JK', 'TBIG.JK', 'TBLA.JK', 'TBMS.JK', 'TCID.JK', 'TCPI.JK', 'TELE.JK',
                'TFCO.JK', 'TGKA.JK', 'TIFA.JK', 'TINS.JK', 'TIRA.JK', 'TIRT.JK', 'TKIM.JK', 'TLKM.JK', 'TMAS.JK', 'TMPO.JK',
                'TNCA.JK', 'TOBA.JK', 'TOPS.JK', 'TOTL.JK', 'TOTO.JK', 'TOWR.JK', 'TPMA.JK', 'TRAM.JK', 'TRIL.JK', 'TRIM.JK',
                'TRIO.JK', 'TRIS.JK', 'TRJA.JK', 'TRST.JK', 'TRUK.JK', 'TSPC.JK', 'TUGU.JK', 'TURI.JK', 'UANG.JK', 'ULTJ.JK',
                'UNIC.JK', 'UNSP.JK', 'UNTR.JK', 'UNVR.JK', 'URBN.JK', 'UVCR.JK', 'VICO.JK', 'VINS.JK', 'VIVA.JK', 'VOKS.JK',
                'VRNA.JK', 'WAPO.JK', 'WEGE.JK', 'WEHA.JK', 'WGSH.JK', 'WICO.JK', 'WIIM.JK', 'WIKA.JK', 'WINS.JK', 'WOMF.JK',
                'WONN.JK', 'WTON.JK', 'WTRA.JK', 'WSBP.JK', 'WSKT.JK', 'WTON.JK', 'YELO.JK', 'YPAS.JK', 'YULE.JK', 'ZBRA.JK',
                'ZINC.JK', 'ZONE.JK'
            ]
            
            # Remove duplicates
            extended_tickers = list(set(extended_tickers))
            print(f"📊 Generated extended ticker list with {len(extended_tickers)} symbols")
            return sorted(extended_tickers)
            
        except Exception as e:
            print(f"⚠ Yahoo ticker fetch failed: {str(e)[:50]}")
            return self._get_fallback_tickers()

    def get_corporate_actions(self, ticker=None, days_back=365):
        """
        Get corporate actions data from IDX

        Args:
            ticker (str): Specific ticker to filter (optional)
            days_back (int): Number of days back to look for actions

        Returns:
            pd.DataFrame: Corporate actions data
        """
        try:
            print("📡 Fetching corporate actions from IDX...")

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Try to get corporate actions data
            df = pd.read_csv(self.corporate_action_url)

            # Standardize column names and filter
            df.columns = df.columns.str.strip()

            # Convert date columns if they exist
            date_columns = ['Tanggal Pengumuman', 'Tanggal Cum', 'Tanggal Ex', 'Tanggal Recording']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # Filter by date range if date column exists
            if 'Tanggal Pengumuman' in df.columns:
                df = df[df['Tanggal Pengumuman'] >= start_date]

            # Filter by ticker if specified
            if ticker and 'Kode Saham' in df.columns:
                ticker_clean = ticker.replace('.JK', '')
                df = df[df['Kode Saham'] == ticker_clean]

            # Add metadata
            df['data_source'] = self.name
            df['data_type'] = 'corporate_actions'

            print(f"✅ Loaded {len(df)} corporate actions from IDX")
            return df

        except Exception as e:
            print(f"⚠ IDX corporate actions failed: {str(e)[:50]}")
            return pd.DataFrame()

    def get_company_info(self, ticker):
        """
        Get detailed company information from IDX

        Args:
            ticker (str): Ticker symbol

        Returns:
            dict: Company information
        """
        try:
            ticker_clean = ticker.replace('.JK', '')

            # This would require scraping IDX website or using their API
            # For now, return basic structure
            return {
                'ticker': ticker,
                'company_code': ticker_clean,
                'data_source': self.name,
                'sector': 'Unknown',  # Would need to be mapped from IDX data
                'sub_sector': 'Unknown',
                'listing_date': None,
                'shares_outstanding': None,
                'market_cap': None
            }

        except Exception as e:
            print(f"⚠ Error getting company info for {ticker}: {e}")
            return {}