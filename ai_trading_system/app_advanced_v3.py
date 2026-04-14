"""
ENHANCED AI TRADING DASHBOARD v3.0
Professional trading analysis platform dengan Signal Strength, Profile-Matching, dan Price Prediction
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlalchemy
import ta
from datetime import datetime, timedelta
import json

# Import from proper module paths
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import get_engine
from advanced_analysis import AdvancedAnalyzer
from recommendation import StockRecommender

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="AI Trading Dashboard Professional v3.0",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .strong-buy { background-color: #e6ffe6; border-left: 4px solid #00aa00; padding: 10px; border-radius: 4px; }
    .moderate-buy { background-color: #fff3e6; border-left: 4px solid #ff9800; padding: 10px; border-radius: 4px; }
    .weak-signal { background-color: #ffe6e6; border-left: 4px solid #cc0000; padding: 10px; border-radius: 4px; }
    .profile-perfect { background-color: #d4edda; padding: 8px; border-radius: 4px; }
    .profile-good { background-color: #fff3cd; padding: 8px; border-radius: 4px; }
    .profile-fair { background-color: #e2e3e5; padding: 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# HELPER FUNCTIONS
# ============================================
def format_idr(value):
    """Format ke IDR currency"""
    if isinstance(value, (int, float)):
        return f"Rp {value:,.0f}"
    return str(value)

def classify_signal(strength):
    """Classify signal strength dengan emoji"""
    if strength >= 75:
        return "🟢 SANGAT KUAT", "strong-buy", 75
    elif strength >= 60:
        return "🟡 KUAT", "moderate-buy", 60
    elif strength >= 45:
        return "🔵 CUKUP", "moderate-buy", 45
    else:
        return "🔴 LEMAH", "weak-signal", 35

def classify_profile_match(match):
    """Classify profile match"""
    if match == 'Perfect':
        return "✅ PERFECT", "profile-perfect"
    elif match == 'Good':
        return "⭐ GOOD", "profile-good"
    elif match == 'Fair':
        return "⚠️ FAIR", "profile-fair"
    else:
        return "❌ CHECK", "weak-signal"

def detect_oversold_rebound(rsi, price, ma20, support_level):
    """Deteksi saham oversold siap rebound"""
    conditions = []
    score = 0
    
    if rsi < 20:
        conditions.append("🔴 EXTREME OVERSOLD")
        score += 40
    elif rsi < 30:
        conditions.append("🔴 SANGAT OVERSOLD")
        score += 30
    
    if price <= support_level * 1.02:
        conditions.append("📍 NEAR SUPPORT")
        score += 30
    
    if price < ma20 * 0.98:
        conditions.append("⬇️ PULLBACK SETUP")
        score += 20
    
    return {
        'is_oversold': rsi < 30,
        'is_near_support': price <= support_level * 1.02,
        'conditions': conditions,
        'rebound_probability': min(100, score)
    }

def get_database_stats():
    """Get database stats"""
    try:
        engine = get_engine()
        inspector = sqlalchemy.inspect(engine)
        all_tables = inspector.get_table_names()
        stock_tables = [
            t for t in all_tables 
            if not t.endswith('_fundamentals') 
            and t not in ['corporate_actions', 'data_collection_metadata', 'test_table', 'market']
        ]
        return {
            'total_stocks': len(stock_tables),
            'stocks': stock_tables,
            'status': '✅ READY'
        }, engine
    except Exception as e:
        st.error(f"Database error: {e}")
        return None, None

def load_stock_data(ticker, engine):
    """Load stock data"""
    try:
        df = pd.read_sql(f"SELECT * FROM '{ticker}' ORDER BY Date DESC LIMIT 500", engine)
        if df.empty:
            return None
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        df = df.set_index('Date')
        return df
    except:
        return None

# ============================================
# INITIALIZE SESSION & ENGINE
# ============================================
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None
if 'show_recommendations' not in st.session_state:
    st.session_state.show_recommendations = False

stats, engine = get_database_stats()
if not stats:
    st.stop()

# ============================================
# MAIN PAGE
# ============================================
st.title("📈 AI TRADING DASHBOARD PROFESSIONAL v3.0")
st.markdown("**Analisis Teknikal Professional dengan Signal Strength, Profile Matching & Price Prediction**")
st.markdown("---")

# ============================================
# MAIN NAVIGATION
# ============================================
tab1, tab2, tab3, tab4 = st.tabs(["🎯 TOP 10 REKOMENDASI", "📊 ANALISIS DETAIL", "⚙️ PROFIL & FILTER", "📑 INFO"])

# ============================================
# TAB 1: TOP 10 RECOMMENDATIONS WITH SIGNAL STRENGTH
# ============================================
with tab1:
    with st.sidebar:
        st.markdown("## 🎯 REKOMENDASI SETTINGS")
        
        # Trader profile
        profile = st.radio(
            "Pilih Profil Trader:",
            options=['conservative', 'moderate', 'beginner_growth', 'aggressive'],
            format_func=lambda x: {
                'conservative': '🟢 Conservative (Low Risk)',
                'moderate': '🔵 Moderate (Balanced)',
                'beginner_growth': '🟠 Growth (High Growth)',
                'aggressive': '🔴 Aggressive (High Risk)'
            }[x]
        )
        
        st.divider()
        
        # Filters
        st.markdown("**FILTER:**")
        min_signal = st.slider("Min Signal Strength %", 0, 100, 50, step=5)
        show_only_perfect = st.checkbox("Hanya Perfect Match", value=False)
        
        st.divider()
        
        # Update button
        if st.button("🔄 UPDATE RECOMMENDATIONS", use_container_width=True, type="primary"):
            st.session_state.show_recommendations = True
            st.rerun()
    
    st.markdown(f"### 🎯 TOP 10 REKOMENDASI ({profile.upper()})")
    
    try:
        recommender = StockRecommender()
        
        # Get recommendations with signals
        with st.spinner(f"Menganalisa {stats['total_stocks']} saham..."):
            recommendations_df = recommender.get_recommendations_with_signals(
                profile=profile,
                top_n=10,
                avoid_retail=(profile != 'conservative')
            )
        
        if recommendations_df.empty:
            st.warning("⚠️ Tidak ada rekomendasi sesuai filter. Coba ubah profil atau filter.")
        else:
            # Filter by signal strength
            recommendations_df = recommendations_df[recommendations_df['signal_strength'] >= min_signal]
            
            if show_only_perfect:
                recommendations_df = recommendations_df[recommendations_df['profile_match'] == 'Perfect']
            
            if len(recommendations_df) == 0:
                st.warning("⚠️ Tidak ada saham yang cocok dengan filter yang dipilih.")
            else:
                # Display as nice table with key metrics
                st.markdown(f"**Ditemukan: {len(recommendations_df)} Rekomendasi**")
                st.divider()
                
                for idx, row in recommendations_df.iterrows():
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1.2, 1, 1.2, 1.2, 1.2, 1.5])
                    
                    # Ticker
                    with col1:
                        ticker_clean = row['ticker'].replace('.JK', '')
                        st.markdown(f"**{ticker_clean}**")
                    
                    # Price
                    with col2:
                        price = row['latest_price']
                        change_pct = row['price_change_pct']
                        change_color = "🟢" if change_pct >= 0 else "🔴"
                        st.markdown(f"{format_idr(price)}\n{change_color} {change_pct:+.2f}%")
                    
                    # Signal Strength
                    with col3:
                        signal = row['signal_strength']
                        signal_label, css, _ = classify_signal(signal)
                        st.markdown(f"**{signal_label}**\n{signal:.0f}%")
                    
                    # Profile Match
                    with col4:
                        profile_match = row['profile_match']
                        match_label, match_css = classify_profile_match(profile_match)
                        st.markdown(f"{match_label}")
                    
                    # 1M Prediction
                    with col5:
                        pred_return_1m = row.get('pred_1M_return', 0)
                        pred_conf_1m = row.get('pred_1M_conf', 0)
                        color_pred = "🟢" if pred_return_1m >= 0 else "🔴"
                        st.markdown(f"{color_pred} **{pred_return_1m:+.1f}%**\n(Conf: {pred_conf_1m:.0f}%)")
                    
                    # Combined Score
                    with col6:
                        combined = row['combined_score']
                        st.metric("Score", f"{combined:.1f}")
                    
                    # Action button
                    with col7:
                        if st.button(f"📊 Lihat Detail", key=f"detail_{idx}", use_container_width=True):
                            st.session_state.selected_ticker = row['ticker']
                            st.session_state.show_detailed = True
                    
                    st.divider()
                
                # Summary statistics
                st.markdown("### 📊 SUMMARY STATISTIK")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Total", len(recommendations_df))
                with col2:
                    St_avg_signal = recommendations_df['signal_strength'].mean()
                    st.metric("Avg Signal", f"{St_avg_signal:.0f}%")
                with col3:
                    perfect_match = (recommendations_df['profile_match'] == 'Perfect').sum()
                    st.metric("Perfect Match", perfect_match)
                with col4:
                    avg_1m_return = recommendations_df['pred_1M_return'].mean()
                    st.metric("Avg 1M Return", f"{avg_1m_return:+.1f}%")
                with col5:
                    bullish_count = (recommendations_df['pred_1M_return'] > 0).sum()
                    st.metric("Bullish (1M)", bullish_count)
                
                # Detailed predictions table
                st.markdown("### 📈 PREDIKSI HARGA")
                pred_cols = st.columns(4)
                for idx, period in enumerate(['1W', '2W', '3W', '1M']):
                    with pred_cols[idx]:
                        st.markdown(f"**{period} PREDICTION**")
                        display_df = recommendations_df[[
                            'ticker', 
                            f'pred_{period}_price',
                            f'pred_{period}_return',
                            f'pred_{period}_conf'
                        ]].copy()
                        display_df.columns = ['Ticker', 'Target Price', 'Return %', 'Confidence %']
                        display_df['Ticker'] = display_df['Ticker'].str.replace('.JK', '')
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.write(f"Details: {e}")

# ============================================
# TAB 2: DETAILED STOCK ANALYSIS
# ============================================
with tab2:
    st.markdown("### 📊 ANALISIS DETAIL SAHAM")
    
    with st.sidebar:
        st.markdown("## 📊 ANALISIS DETAIL SETTINGS")
        selected_ticker = st.selectbox(
            "Pilih Saham:",
            options=sorted(stats['stocks']),
            format_func=lambda x: x.replace('.JK', '')
        )
        
        st.divider()
        
        st.markdown("**CHART OPTIONS:**")
        show_ma = st.checkbox("Moving Averages", value=True)
        show_rsi = st.checkbox("RSI & Fibonacci", value=True)
        show_macd = st.checkbox("MACD", value=True)
        show_volume = st.checkbox("Volume", value=True)
        show_st = st.checkbox("SuperTrend", value=True)
    
    if selected_ticker:
        df = load_stock_data(selected_ticker, engine)
        if df is not None:
            analyzer = AdvancedAnalyzer()
            df_calc = analyzer.calculate_all_indicators(df)
            latest = df_calc.iloc[-1]
            
            # Get signal metrics
            recommender = StockRecommender()
            signal_strength = recommender.calculate_signal_strength(df_calc)
            predictions = recommender.predict_price_movements(df_calc)
            
            # Header with key metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Price", format_idr(latest['Close']))
            with col2:
                st.metric("Signal Strength", f"{signal_strength:.0f}%")
            with col3:
                st.metric("RSI", f"{latest.get('RSI', 0):.1f}")
            with col4:
                st.metric("MACD", f"{latest.get('MACD', 0):.3f}")
            with col5:
                st.metric("Volume Ratio", f"{latest.get('Volume_Ratio', 0):.2f}x")
            
            st.divider()
            
            # ===== TRADING STRATEGY =====
            st.markdown("#### 🎯 STRATEGI TRADING")
            strategy = analyzer.generate_trading_strategy(df_calc, selected_ticker, 'moderate')
            strat = strategy['strategy']
            action = strat.get('action', 'WAIT')
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if action == 'BUY':
                    st.markdown("### 🟢 AKSI: **BUY**")
                elif action == 'SELL':
                    st.markdown("### 🔴 AKSI: **SELL**")
                else:
                    st.markdown("### ⚫ AKSI: **WAIT**")
            with col2:
                st.metric("Confidence", f"{strategy.get('confidence_level', 0):.0f}%")
            with col3:
                st.metric("Trend", strategy.get('trend', 'N/A'))
            
            st.divider()
            
            # Entry point dan TP/SL
            st.markdown("#### 📍 ENTRY & TARGET")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Entry Zone Min", format_idr(strat.get('entry_zone_min', 0)))
            with col2:
                st.metric("Entry Zone Max", format_idr(strat.get('entry_zone_max', 0)))
            with col3:
                st.metric("TP1 (50%)", format_idr(strat.get('take_profit_1', 0)))
            with col4:
                st.metric("TP3 (All)", format_idr(strat.get('take_profit_3', 0)))
            
            st.divider()
            
            # ACCUMULATION ZONE (DCA) - FIXED
            st.markdown("#### 💰 ACCUMULATION ZONE (DCA)")
            accum_zone = strat.get('accumulation_zone')
            if accum_zone:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if isinstance(accum_zone, dict) and 'trigger' in accum_zone:
                        st.metric("Trigger Price", format_idr(accum_zone.get('trigger', 0)))
                    else:
                        st.metric("Trigger", "N/A")
                with col2:
                    if isinstance(accum_zone, dict) and 'action' in accum_zone:
                        st.metric("Action", accum_zone.get('action', 'N/A'))
                    else:
                        st.metric("Action", "N/A")
                with col3:
                    if isinstance(accum_zone, dict) and 'suggested_quantity' in accum_zone:
                        st.metric("Quantity", accum_zone.get('suggested_quantity', 'N/A'))
                    else:
                        st.metric("Quantity", "N/A")
            else:
                st.info("ℹ️ Tidak ada accumulation zone pada kondisi saat ini")
            
            st.divider()
            
            # PRICE PREDICTIONS (1W, 2W, 3W, 1M)
            st.markdown("#### 📈 PREDIKSI HARGA (1W, 2W, 3W, 1M)")
            if predictions and 'error' not in predictions:
                pred_cols = st.columns(4)
                for idx, period in enumerate(['1W', '2W', '3W', '1M']):
                    with pred_cols[idx]:
                        if period in predictions:
                            pred = predictions[period]
                            expected_ret = pred['expected_return']
                            conf = pred['confidence']
                            target = pred['predicted_price']
                            
                            color = "🟢" if expected_ret >= 0 else "🔴"
                            st.markdown(f"**{period}**")
                            st.metric("Target", format_idr(target))
                            st.metric("Return", f"{color} {expected_ret:+.1f}%")
                            st.metric("Confidence", f"{conf:.0f}%")
            else:
                st.info("ℹ️ Prediksi belum tersedia untuk saham ini")
            
            st.divider()
            
            # ===== CHART =====
            st.markdown("#### 📊 CHART TEKNIKAL")
            
            rows = 4 if show_volume else 3
            row_heights = [2, 1, 1, 0.8] if show_volume else [2, 1, 1]
            
            fig = make_subplots(
                rows=rows, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=row_heights
            )
            
            date_range = df_calc.index
            
            # Candlestick
            fig.add_trace(
                go.Candlestick(
                    x=date_range, open=df_calc['Open'], high=df_calc['High'],
                    low=df_calc['Low'], close=df_calc['Close'], name='Price'
                ),
                row=1, col=1
            )
            
            # MA
            if show_ma:
                fig.add_trace(go.Scatter(x=date_range, y=df_calc['MA5'], name='MA5', 
                                        line=dict(color='blue', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=date_range, y=df_calc['MA10'], name='MA10',
                                        line=dict(color='orange', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=date_range, y=df_calc['MA20'], name='MA20',
                                        line=dict(color='green', width=2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=date_range, y=df_calc['MA50'], name='MA50',
                                        line=dict(color='red', width=2)), row=1, col=1)
            
            # SuperTrend
            if show_st and 'ST_Basic_Upper' in df_calc.columns:
                fig.add_trace(go.Scatter(x=date_range, y=df_calc['ST_Basic_Upper'],
                                        name='SuperTrend', line=dict(color='purple', width=1, dash='dash')),
                             row=1, col=1)
            
            # RSI
            if show_rsi and 'RSI' in df_calc.columns:
                fig.add_trace(go.Scatter(x=date_range, y=df_calc['RSI'], name='RSI',
                                        line=dict(color='darkblue', width=2)), row=2, col=1)
                fig.add_hline(y=30, line_dash="solid", line_color="red", row=2, col=1)
                fig.add_hline(y=70, line_dash="solid", line_color="green", row=2, col=1)
            
            # MACD
            if show_macd and 'MACD' in df_calc.columns:
                fig.add_trace(go.Scatter(x=date_range, y=df_calc['MACD'], name='MACD',
                                        line=dict(color='blue', width=2)), row=3, col=1)
                if 'MACD_Signal' in df_calc.columns:
                    fig.add_trace(go.Scatter(x=date_range, y=df_calc['MACD_Signal'],
                                            name='Signal', line=dict(color='red', width=2)), row=3, col=1)
                fig.add_hline(y=0, line_dash="solid", line_color="gray", row=3, col=1)
            
            # Volume
            if show_volume and 'Volume' in df_calc.columns:
                fig.add_trace(go.Bar(x=date_range, y=df_calc['Volume'], name='Volume',
                                    marker=dict(color='lightblue')), row=4, col=1)
            
            fig.update_layout(height=900, hovermode='x unified', template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 3: PROFILE & FILTER SETTINGS
# ============================================
with tab3:
    st.markdown("### ⚙️ PROFIL TRADER & FILTER")
    
    recommender = StockRecommender()
    
    profiles_info = {
        'conservative': recommender.get_profile_description('conservative'),
        'moderate': recommender.get_profile_description('moderate'),
        'beginner_growth': recommender.get_profile_description('beginner_growth'),
        'aggressive': recommender.get_profile_description('aggressive')
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🟢 CONSERVATIVE")
        info = profiles_info['conservative']
        st.write(f"**{info['name']}**")
        st.write(f"{info['description']}")
        st.write(f"**Focus:** {info['focus']}")
        st.info("Cocok untuk investor yang menghindari risiko dan mencari stabilitas jangka panjang")
    
    with col2:
        st.markdown("#### 🔵 MODERATE")
        info = profiles_info['moderate']
        st.write(f"**{info['name']}**")
        st.write(f"{info['description']}")
        st.write(f"**Focus:** {info['focus']}")
        st.info("Cocok untuk investor yang menginginkan keseimbangan antara pertumbuhan dan keamanan")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🟠 GROWTH")
        info = profiles_info['beginner_growth']
        st.write(f"**{info['name']}**")
        st.write(f"{info['description']}")
        st.write(f"**Focus:** {info['focus']}")
        st.info("Cocok untuk pemula dengan modal kecil yang mencari pertumbuhan cepat")
    
    with col2:
        st.markdown("#### 🔴 AGGRESSIVE")
        info = profiles_info['aggressive']
        st.write(f"**{info['name']}**")
        st.write(f"{info['description']}")
        st.write(f"**Focus:** {info['focus']}")
        st.info("Cocok untuk trader yang berpengalaman dengan risk tolerance tinggi")
    
    st.divider()
    
    st.markdown("### 📊 DATABASE STATUS")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Stocks", stats['total_stocks'])
    with col2:
        coverage = stats['total_stocks'] / 957 * 100
        st.metric("Coverage", f"{coverage:.1f}%")
    with col3:
        st.metric("Status", stats['status'])
    with col4:
        st.metric("Last Update", "Live")

# ============================================
# TAB 4: INFO & DOCUMENTATION
# ============================================
with tab4:
    st.markdown("### ℹ️ INFORMASI SISTEM")
    
    st.markdown("""
    ## AI Trading Dashboard v3.0
    
    ### Fitur Utama:
    - **TOP 10 REKOMENDASI** dengan Signal Strength (0-100)
    - **PROFILE MATCHING** - Rekomendasi sesuai tipe trader
    - **PRICE PREDICTION** - Prediksi harga 1W, 2W, 3W, 1M
    - **ACCUMULATION ZONE (DCA)** - Entry points untuk akumulasi
    - **Technical Analysis** - RSI, MACD, SuperTrend, Moving Averages
    - **Database Lengkap** - Hingga 957 saham IDX
    
    ### Interpretasi Signal Strength:
    - **75-100%**: 🟢 Sangat Kuat - Buy Signal Kuat
    - **60-75%**: 🟡 Kuat - Good Entry Point
    - **45-60%**: 🔵 Cukup - Wait for Confirmation
    - **<45%**: 🔴 Lemah - Avoid atau Jangan Entry
    
    ### Trader Profiles:
    1. **Conservative** - Risk ≈ 10-15%, Fokus Blue-chip
    2. **Moderate** - Risk ≈ 20-25%, Balanced Growth
    3. **Growth** - Risk ≈ 30-50%, High Growth Potential
    4. **Aggressive** - Risk ≈ 40%+, Maximum Upside
    
    ### Price Prediction Timeframes:
    - **1W (7 hari)** - Prediksi jangka pendek
    - **2W (14 hari)** - Prediksi sedang
    - **3W (21 hari)** - Prediksi menengah
    - **1M (30 hari)** - Prediksi jangka panjang
    
    ### Accumulation Zone (DCA):
    Dollar Cost Averaging trigger untuk menambah posisi saat harga menyentuh support level
    
    """)
    
    st.divider()
    
    st.markdown("### 📞 CONTACT & SUPPORT")
    st.info("""
    Untuk pertanyaan atau feedback, silakan hubungi tim development.
    
    **Last Updated:** 2026-04-14  
    **Version:** 3.0.0
    """)
