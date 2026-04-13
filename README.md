# AI Trading System Indonesia

Sistem trading otomatis dengan AI untuk pasar saham Indonesia (IDX/IHSG).

## 🚀 Fitur

- **Dashboard Interaktif** - Interface Streamlit untuk monitoring trading
- **AI Prediction** - Model machine learning untuk prediksi harga saham
- **Smart Money Detection** - Deteksi pola smart money di pasar
- **Technical Analysis** - Indikator RSI, MACD, dan analisis teknikal lainnya
- **Backtesting Engine** - Simulasi historis performa trading strategy
- **REST API** - FastAPI backend untuk integrasi eksternal
- **Database SQLite** - Penyimpanan data saham dan hasil analisis

## 📊 Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/hendroliem1990/repo/main)

## 🛠️ Teknologi

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: SQLite + SQLAlchemy
- **Data**: Yahoo Finance (yfinance)
- **Analysis**: TA-Lib, Pandas, NumPy
- **ML**: Scikit-learn

## 🚀 Menjalankan Lokal

```bash
# Clone repository
git clone https://github.com/hendroliem1990/repo.git
cd repo

# Install dependencies
pip install -r requirements.txt

# Jalankan Streamlit dashboard
cd ai_trading_system
streamlit run app.py

# Atau jalankan API server
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

## 📁 Struktur Project

```
repo/
├── ai_trading_system/          # Main application
│   ├── app.py                 # Streamlit dashboard
│   ├── api.py                 # FastAPI backend
│   ├── pipeline.py            # Data pipeline
│   ├── strategy.py            # Trading strategies
│   ├── backtest.py            # Backtesting engine
│   ├── database.py            # Database utilities
│   └── ...
├── requirements.txt           # Python dependencies
├── packages.txt              # System dependencies
└── .streamlit/               # Streamlit configuration
    └── config.toml
```

## 🔧 Deployment

### Streamlit Cloud
1. Fork repository ini
2. Kunjungi [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub account
4. Pilih repository dan branch `main`
5. Deploy!

### Local Development
```bash
# Jalankan data pipeline
cd ai_trading_system
python pipeline.py

# Jalankan dashboard
streamlit run app.py

# Jalankan API
uvicorn api:app --reload
```

## 📈 API Endpoints

- `GET /` - Status API
- `GET /tables` - List available tickers
- `GET /signal/{ticker}` - Get trading signal for ticker

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact

Hendro Liem - [@hendroliem1990](https://github.com/hendroliem1990)

Project Link: [https://github.com/hendroliem1990/repo](https://github.com/hendroliem1990/repo)