# AI Trading System Indonesia

Sistem perdagangan saham otomatis dengan AI untuk pasar Indonesia (IDX/IHSG) yang menggunakan berbagai sumber data untuk analisis komprehensif.

## 🚀 Fitur Utama

- **Data Lengkap IDX**: Harga, fundamental, corporate actions dari berbagai sumber
- **AI Prediction**: Machine learning untuk prediksi harga saham
- **Smart Money Detection**: Deteksi pola institusi dan smart money
- **Dashboard Interaktif**: Streamlit dashboard untuk visualisasi
- **Backtesting Engine**: Uji strategi perdagangan historis
- **API REST**: FastAPI untuk integrasi eksternal

## 📊 Sumber Data

### ✅ Yahoo Finance
- **Data**: Harga historis (OHLCV) dengan interval harian
- **Indikator**: RSI, MACD, MACD Signal
- **Cakupan**: Semua saham IDX sejak 2000
- **Status**: ✅ Aktif

### ✅ IDX (Indonesia Stock Exchange)
- **Data**: Daftar ticker lengkap, corporate actions
- **Cakupan**: Semua saham yang terdaftar di IDX
- **Status**: ✅ Aktif (fallback comprehensive)

### ✅ Stockbit
- **Data**: Fundamental (financial statements, ratios, company profile)
- **Cakupan**: Financial ratios, valuation metrics, company info
- **Status**: ✅ Aktif (struktur data siap, perlu API key untuk data real)

### 🔄 Premium Data Sources (Future)
- **Refinitiv**: Data real-time dan fundamental premium
- **Bloomberg**: Data institusional dan analisis
- **Polygon.io**: API data harga high-frequency
- **Tiingo**: Data harga historis dengan kualitas tinggi

## 🏗️ Arsitektur Sistem

```
data_sources/
├── yahoo_data.py      # Yahoo Finance integration
├── idx_data.py        # IDX ticker & corporate actions
├── stockbit_data.py   # Fundamental data
├── premium_data.py    # Premium sources (Polygon, Tiingo, etc.)
└── data_manager.py    # Coordinator untuk semua sumber data

pipeline.py            # Main data collection pipeline
app.py                 # Streamlit dashboard
api.py                 # FastAPI REST API
database.py            # Database utilities
recommendation.py      # AI stock recommendation system
```

## 🎯 AI Stock Recommendations

Sistem rekomendasi saham berbasis AI dengan 4 profile trader yang disesuaikan dengan kebutuhan dan pengalaman trading:

### 📊 **Conservative Trader**
- **Target**: Investor konservatif yang mengutamakan stabilitas
- **Fokus**: Saham blue-chip dengan fundamental kuat
- **Risiko**: Rendah, cocok untuk jangka panjang
- **Karakteristik**: Market cap besar, volume tinggi, volatilitas rendah

### 📈 **Moderate Trader**
- **Target**: Trader seimbang risk/reward
- **Fokus**: Pertumbuhan moderat dengan volatilitas reasonable
- **Risiko**: Sedang, cocok untuk swing trading
- **Karakteristik**: Market cap sedang, momentum balanced

### 🚀 **Beginner Growth Trader** ⭐ **NEW!**
- **Target**: Trader pemula dengan modal kecil
- **Fokus**: Saham murah (50-2000 IDR) dengan potensi rebound besar
- **Risiko**: Tinggi untuk reward maksimal
- **Karakteristik**:
  - 💰 **Harga**: 50-2000 rupiah per saham
  - 📉 **Oversold Focus**: Prioritas saham dengan RSI < 30
  - 📊 **Volume**: Medium-low (hindari saham retail berat)
  - 📈 **Growth Potential**: Volatilitas tinggi untuk keuntungan besar
  - 🚫 **Avoid**: Saham populer di broker summary (XL, XC, PD, IF, KK)

### ⚡ **Aggressive Trader**
- **Target**: Trader berisiko tinggi
- **Fokus**: Momentum tinggi dan peluang emerging
- **Risiko**: Sangat tinggi, cocok untuk day trading
- **Karakteristik**: Volatilitas tinggi, volume besar, momentum kuat

## 🚀 Instalasi & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
# Untuk development
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Jalankan Pipeline Data
```bash
# Test dengan 5 ticker
python pipeline.py test

# Full pipeline (price + fundamental)
python pipeline.py full

# Price data only
python pipeline.py price-only
```

### 4. Jalankan Dashboard
```bash
streamlit run app.py
```

### 5. Pilih Profile Trader
Setelah dashboard terbuka, pilih profile yang sesuai dengan gaya trading Anda:

- **Beginner Growth Trader**: Untuk trader pemula dengan modal kecil yang mencari pertumbuhan signifikan melalui saham murah dengan potensi rebound
- **Conservative Trader**: Untuk investor jangka panjang yang mengutamakan stabilitas
- **Moderate Trader**: Untuk trader seimbang risk/reward
- **Aggressive Trader**: Untuk trader berisiko tinggi yang suka momentum

### 6. Jalankan API Server
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

## 📈 Cara Penggunaan

### Data Collection Pipeline

```python
from data_sources import DataManager

# Initialize data manager
dm = DataManager()

# Collect comprehensive data
results = dm.collect_comprehensive_data(
    max_tickers=50,  # Limit untuk testing
    data_types=['price', 'fundamental', 'corporate_actions']
)

# Update specific ticker
dm.update_ticker_data('BBCA.JK', data_types=['price', 'fundamental'])
```

### Menggunakan Premium Data Sources

```python
from data_sources import PremiumDataSource

# Add premium data source dengan API key
dm.add_premium_source('polygon', 'your_polygon_api_key')
dm.add_premium_source('tiingo', 'your_tiingo_api_key')

# Collect premium data
results = dm.collect_comprehensive_data(
    data_types=['price', 'fundamental']
)
```

## 🔧 Konfigurasi

### Environment Variables
```bash
# API Keys untuk premium data sources
POLYGON_API_KEY=your_key_here
TIINGO_API_KEY=your_key_here
STOCKBIT_API_KEY=your_key_here
```

### Database Configuration
- **Engine**: SQLite (default)
- **Path**: `market.db` (dapat dikonfigurasi di `config.py`)
- **Tables**:
  - `{TICKER}`: Price data per ticker
  - `{TICKER}_fundamentals`: Fundamental data
  - `corporate_actions`: Corporate actions data
  - `data_collection_metadata`: Pipeline metadata

## 📊 Dashboard Features

### AI Stock Recommendations ⭐ **NEW!**
- **4 Trader Profiles**: Conservative, Moderate, Beginner Growth, Aggressive
- **Personalized Scoring**: Algoritma AI yang disesuaikan dengan profile trader
- **Real-time Updates**: Rekomendasi diperbarui berdasarkan data terbaru
- **Technical Analysis**: RSI, MACD, Volume analysis untuk setiap rekomendasi
- **Beginner Growth Focus**: Khusus untuk trader pemula dengan modal kecil

### Enhanced Chart Analysis
- **Candlestick Charts**: Interactive price charts dengan OHLC data
- **Moving Averages**: MA 5, MA 10, MA 20, MA 50 dengan toggle on/off
- **Fibonacci Levels**: Support/resistance levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)
- **Volume Analysis**: Volume bars di bawah chart utama
- **Technical Indicators**: RSI, MACD dengan real-time status

### Price Information
- **Current Price**: Harga terakhir dengan perubahan harian
- **52-Week High/Low**: Historical price extremes
- **Average Volume**: 30-day average trading volume
- **Support/Resistance**: Recent market levels

### Trading Signals
- **AI Signals**: Buy/Sell/Hold recommendations
- **Signal History**: Recent trading signals table
- **Signal Statistics**: Count of each signal type

### Performance Analysis
- **Backtesting Results**: Strategy vs market performance
- **Cumulative Returns**: Visual comparison charts
- **Return Metrics**: Strategy and market returns

### Interactive Controls
- **Ticker Selection**: Dropdown untuk semua saham IDX
- **Chart Customization**: Toggle untuk MA, Fibonacci, Volume
- **Responsive Design**: Layout yang menyesuaikan ukuran layar

## 🔌 API Endpoints

```
GET /signal/{ticker}     # AI trading signals
GET /tables              # Available data tables
GET /fundamentals/{ticker} # Fundamental data
GET /corporate-actions   # Corporate actions data
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Data Quality Check
```python
from data_sources import DataManager
dm = DataManager()
report = dm.get_data_quality_report()
print(report)
```

## 🔮 Future Enhancements

- [ ] Real-time data streaming
- [ ] Premium data source integration
- [ ] Advanced ML models (LSTM, Transformer)
- [ ] Risk management module
- [ ] Portfolio optimization
- [ ] Alert system (Telegram, Email)
- [ ] Multi-asset support (crypto, forex)

## 📝 License

MIT License - bebas digunakan untuk keperluan edukasi dan non-komersial.

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## ⚠️ Disclaimer

Sistem ini untuk keperluan edukasi dan riset. Tidak untuk digunakan sebagai saran investasi. Selalu lakukan riset sendiri sebelum berinvestasi.