"""
ENHANCED AI TRADING DASHBOARD v2.0
Professional trading analysis platform dengan deteksi oversold & signal strength
Designed for traders yang mencari entry point di bottom dengan rebound signal kuat
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from database import get_engine
import sqlalchemy
import ta
from advanced_analysis import AdvancedAnalyzer, IndicatorExplainer
from recommendation import StockRecommender
from datetime import datetime, timedelta
import json

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="AI Trading Dashboard Professional v2.0",
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

def get_signal_strength(rsi, macd, supertrend_trend, volume_ratio, ma_alignment):
    """Calculate signal strength (0-100 scale)"""
    score = 0
    
    # RSI oversold = strong buy signal
    if rsi < 30:
        score += 35
    elif rsi < 40:
        score += 20
    elif rsi > 70:
        score -= 20
    
    # MACD bullish
    if macd > 0:
        score += 20
    
    # SuperTrend confirmation
    if supertrend_trend == 'UPTREND':
        score += 20
    elif supertrend_trend == 'DOWNTREND':
        score -= 25
    
    # Volume confirmation
    if volume_ratio > 1.5:
        score += 15
    elif volume_ratio < 0.7:
        score -= 10
    
    # MA alignment
    if ma_alignment == 'BULLISH':
        score += 15
    elif ma_alignment == 'BEARISH':
        score -= 20
    
    return max(0, min(100, score))

def classify_signal(strength):
    """Classify signal strength dengan emoji"""
    if strength >= 75:
        return "🟢 SANGAT KUAT", "strong-buy"
    elif strength >= 55:
        return "🟡 KUAT", "moderate-buy"
    elif strength >= 35:
        return "🔵 CUKUP", "moderate-buy"
    else:
        return "🔴 LEMAH", "weak-signal"

def detect_oversold_rebound(rsi, price, ma20, support_level):
    """Deteksi saham oversold siap rebound - profil: suka bottom-fishing"""
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
# INITIALIZE SESSION
# ============================================
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None
if 'show_recommendations' not in st.session_state:
    st.session_state.show_recommendations = False

# ============================================
# SIDEBAR - MAIN NAVIGATION
# ============================================
with st.sidebar:
    st.markdown("## 🎯 TRADING DASHBOARD PRO")
    st.markdown("---")
    
    stats, engine = get_database_stats()
    if not stats:
        st.stop()
    
    # Section 1: Database info
    st.markdown("### 📊 DATABASE & PROFILE")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Stocks", stats['total_stocks'])
    with col2:
        st.metric("Coverage", f"{stats['total_stocks']/957*100:.0f}%")
    
    # Section 2: Trader profile
    st.markdown("### 👤 PROFIL TRADER")
    profile = st.radio(
        "Pilih profil Anda:",
        options=['conservative', 'moderate', 'beginner_growth', 'aggressive'],
        format_func=lambda x: {
            'conservative': '🟢 Conservative',
            'moderate': '🔵 Moderate',
            'beginner_growth': '🟠 Growth',
            'aggressive': '🔴 Aggressive'
        }[x]
    )
    st.divider()
    
    # Section 3: Filters
    st.markdown("### 🔍 FILTER SAHAM")
    st.markdown("**Harga (IDR):**")
    col1, col2 = st.columns(2)
    with col1:
        min_price = st.number_input("Min", value=50, min_value=1)
    with col2:
        max_price = st.number_input("Max", value=2000, min_value=50)
    
    st.markdown("**Signal Strength:**")
    min_signal = st.slider("Minimum %", 0, 100, 50, step=10)
    
    st.divider()
    
    # Section 4: Actions
    st.markdown("### 📈 AKSI")
    if st.button("🔄 UPDATE RECOMMENDATIONS", use_container_width=True):
        st.session_state.show_recommendations = True
    
    st.divider()
    
    # Section 5: Stock selection
    st.markdown("### 💬 PILIH SAHAM")
    selected = st.selectbox(
        "Cari saham:",
        options=sorted(stats['stocks']),
        format_func=lambda x: x.replace('.JK', '')
    )
    if selected:
        st.session_state.selected_ticker = selected
    
    st.divider()
    
    # Section 6: Chart settings
    st.markdown("### 🎨 CHART")
    show_ma = st.checkbox("Moving Averages", value=True)
    show_rsi = st.checkbox("RSI & Fibonacci", value=True)
    show_macd = st.checkbox("MACD", value=True)
    show_volume = st.checkbox("Volume", value=True)
    show_st = st.checkbox("SuperTrend", value=True)
    
    st.divider()
    
    # Section 7: Options
    st.markdown("### ⚙️ OPTIONS")
    show_explain = st.checkbox("Penjelasan Indikator")
    show_raw = st.checkbox("Raw Data")

# ============================================
# MAIN PAGE
# ============================================
st.title("📈 AI TRADING DASHBOARD PROFESSIONAL v2.0")
st.markdown("**Analisis Teknikal Professional dengan Entry Signal Jelas**")
st.markdown("---")

# TAB 1: RECOMMENDATIONS
if st.session_state.show_recommendations:
    st.markdown("### 🎯 TOP 10 REKOMENDASI (dengan Signal Strength)")
    
    try:
        analyzer = AdvancedAnalyzer()
        recommendations_list = []
        
        for ticker in stats['stocks'][:150]:
            try:
                df = load_stock_data(ticker, engine)
                if df is None or len(df) < 50:
                    continue
                
                df_calc = analyzer.calculate_all_indicators(df)
                latest = df_calc.iloc[-1]
                
                price = float(latest['Close'])
                if price < min_price or price > max_price:
                    continue
                
                rsi = float(latest.get('RSI', 50))
                macd = float(latest.get('MACD', 0))
                ma20 = float(latest.get('MA20', price))
                volume_ratio = float(latest.get('Volume_Ratio', 1.0))
                
                # MA alignment
                if latest['MA5'] > latest['MA10'] > latest['MA20']:
                    ma_align = 'BULLISH'
                elif latest['MA5'] < latest['MA10'] < latest['MA20']:
                    ma_align = 'BEARISH'
                else:
                    ma_align = 'NEUTRAL'
                
                # SuperTrend
                st_trend = 'UPTREND' if price > latest.get('ST_Basic_Upper', price) else 'DOWNTREND'
                
                # Signal strength
                signal = get_signal_strength(rsi, macd, st_trend, volume_ratio, ma_align)
                if signal < min_signal:
                    continue
                
                # Oversold detection
                support = df_calc['Close'].rolling(20).min().iloc[-1]
                oversold = detect_oversold_rebound(rsi, price, ma20, support)
                
                recommendations_list.append({
                    'ticker': ticker.replace('.JK', ''),
                    'price': price,
                    'rsi': rsi,
                    'signal': signal,
                    'oversold': oversold['is_oversold'],
                    'rebound_prob': oversold['rebound_probability'],
                    'volume_ratio': volume_ratio
                })
            except:
                continue
        
        rec_df = pd.DataFrame(recommendations_list)
        rec_df = rec_df.sort_values('signal', ascending=False).head(10)
        
        if len(rec_df) == 0:
            st.warning("⚠️ Tidak ada saham sesuai filter")
        else:
            for idx, row in rec_df.iterrows():
                signal_label, css = classify_signal(row['signal'])
                oversold_mark = "🔴 OVERSOLD" if row['oversold'] else ""
                rebound = f"🚀 REBOUND {row['rebound_prob']:.0f}%" if row['rebound_prob'] > 70 else ""
                
                col1, col2, col3, col4, col5, col6 = st.columns([1, 1.5, 1.2, 1.3, 1.5, 1])
                with col1:
                    st.markdown(f"**{row['ticker']}**")
                with col2:
                    st.markdown(format_idr(row['price']))
                with col3:
                    st.markdown(f"RSI: {row['rsi']:.1f}")
                with col4:
                    st.markdown(signal_label)
                with col5:
                    st.markdown(f"{oversold_mark} {rebound}")
                with col6:
                    st.markdown(f"{row['signal']:.0f}%")
            
            # Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", len(rec_df))
            with col2:
                st.metric("Oversold", int(rec_df['oversold'].sum()))
            with col3:
                st.metric("Rebound", int((rec_df['rebound_prob'] > 70).sum()))
            with col4:
                st.metric("Avg Signal", f"{rec_df['signal'].mean():.0f}%")
    
    except Exception as e:
        st.error(f"Error: {e}")

st.markdown("---")

# TAB 2: DETAILED ANALYSIS
if st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    st.markdown(f"### 📊 ANALISIS: {ticker.replace('.JK', '')}")
    
    df = load_stock_data(ticker, engine)
    if df is not None:
        analyzer = AdvancedAnalyzer()
        df_calc = analyzer.calculate_all_indicators(df)
        latest = df_calc.iloc[-1]
        
        # === STRATEGY SECTION ===
        st.markdown("#### 🎯 STRATEGI TRADING")
        
        strategy = analyzer.generate_trading_strategy(df_calc, ticker, profile)
        strat = strategy['strategy']
        action = strat.get('action', 'WAIT')
        confidence = strategy.get('confidence_level', 0)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if action == 'BUY':
                st.markdown(f"### 🟢 AKSI: **BUY**")
            elif action == 'SELL':
                st.markdown(f"### 🔴 AKSI: **SELL**")
            else:
                st.markdown(f"### ⚫ AKSI: **WAIT**")
        with col2:
            st.metric("Confidence", f"{confidence:.0f}%")
        with col3:
            st.metric("Trend", strategy.get('trend', 'N/A'))
        
        # Professional narrative
        narrative = f"""
**ANALISIS PROFESIONAL** (30+ tahun pengalaman trading)

Berdasarkan technical analysis terhadap {ticker.replace('.JK', '')}, setup berikut ini identified:

**ENTRY STRATEGY:**
• Entry Zone: {format_idr(strat.get('entry_zone_min', 0))} - {format_idr(strat.get('entry_zone_max', 0))}
• Current Price: {format_idr(latest['Close'])}
• Risk per trade: {((strat.get('entry_zone_max', 0) - strat.get('cut_loss', 0)) / strat.get('entry_zone_max', 1) * 100):.2f}%

**PROFIT TARGET (Risk Management):**
1. **TP Level 1** (Quick Profit): {format_idr(strat.get('take_profit_1', 0))} → Ambil 50%
2. **TP Level 2** (Intermediate): {format_idr(strat.get('take_profit_2', 0))} → Ambil 30%
3. **TP Level 3** (Trend Riding): {format_idr(strat.get('take_profit_3', 0))} → Keep 20%

**RISK MANAGEMENT:**
• Stop Loss: {format_idr(strat.get('cut_loss', 0))}
• Risk/Reward Ratio: 1:{((strat.get('take_profit_3', 0) - strat.get('entry_zone_min', 0)) / abs(strat.get('entry_zone_min', 1) - strat.get('cut_loss', 1))):.2f}

**ACCUMULATION ZONE (DCA):**
• Trigger: {strat.get('accumulation_zone', 'N/A')}
• Action: {strat.get('accumulation_action', 'N/A')}

**KEY SIGNALS:**
• RSI: {latest.get('RSI', 'N/A'):.2f} {'🔴 OVERSOLD' if float(latest.get('RSI', 0)) < 30 else '🟡 NORMAL' if float(latest.get('RSI', 0)) < 70 else '🔴 OVERBOUGHT'}
• MACD: {'🟢 BULLISH' if latest.get('MACD', 0) > latest.get('MACD_Signal', 0) else '🔴 BEARISH'}
• SuperTrend: {strategy.get('trend', 'NEUTRAL')}
• Volume: {latest.get('Volume_Ratio', 1):.2f}x

**TRADER NOTES:**
Signal ini valid untuk profile **{profile.upper()}**.
Selalu manage risk dengan ketat dan never fight the trend.
"""
        st.markdown(narrative)
        
        st.divider()
        
        # === CHART ===
        st.markdown("#### 📈 CHART TEKNIKAL")
        
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
        
        st.divider()
        
        # === INDICATORS SUMMARY ===
        st.markdown("#### 📊 RINGKASAN INDIKATOR")
        
        ind_cols = st.columns(5)
        with ind_cols[0]:
            st.metric("MA5", f"{latest.get('MA5', 0):.0f}")
        with ind_cols[1]:
            st.metric("MA20", f"{latest.get('MA20', 0):.0f}")
        with ind_cols[2]:
            st.metric("RSI", f"{latest.get('RSI', 0):.1f}")
        with ind_cols[3]:
            st.metric("MACD", f"{latest.get('MACD', 0):.3f}")
        with ind_cols[4]:
            st.metric("Volume", f"{latest.get('Volume_Ratio', 0):.2f}x")
        
        # === EXPLANATIONS ===
        if show_explain:
            st.divider()
            st.markdown("#### 📚 PENJELASAN INDIKATOR")
            exp_select = st.selectbox("Pilih indikator:", ['MA20', 'RSI', 'MACD', 'SuperTrend', 'Volume'])
            explainer = IndicatorExplainer()
            exp = explainer.get_explanation(exp_select)
            if exp:
                st.markdown(f"**{exp.get('name', exp_select)}**")
                st.markdown(exp.get('description', ''))
        
        # === RAW DATA ===
        if show_raw:
            st.divider()
            st.markdown("#### 📋 RAW DATA")
            st.dataframe(df_calc.tail(50), use_container_width=True)
    else:
        st.error("❌ Data tidak tersedia")
else:
    st.info("💡 Pilih saham dari sidebar untuk melihat analisis")

st.markdown("---")
st.markdown("**Professional Trading Dashboard v2.0** | Disclaimer: Bukan investment advice | Trading memiliki risiko")
