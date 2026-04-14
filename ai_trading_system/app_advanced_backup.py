"""
Enhanced AI Trading Dashboard dengan Advanced Analysis
Menampilkan semua indikator teknikal yang diminta dengan penjelasan detail
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
    page_title="AI Trading Dashboard Advanced",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# HELPER FUNCTIONS
# ============================================
def format_idr(value):
    """Format nilai ke IDR"""
    if isinstance(value, (int, float)):
        return f"Rp {value:,.0f}"
    return str(value)

def get_database_stats():
    """Get database statistics"""
    try:
        engine = get_engine()
        inspector = sqlalchemy.inspect(engine)
        
        all_tables = inspector.get_table_names()
        stock_tables = [
            t for t in all_tables 
            if not t.endswith('_fundamentals') 
            and t not in ['corporate_actions', 'data_collection_metadata', 'test_table']
        ]
        
        stats = {
            'total_stocks': len(stock_tables),
            'stocks': stock_tables,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': '✅ READY' if stock_tables else '❌ NO DATA'
        }
        
        return stats, engine
    except Exception as e:
        return None, None

def load_stock_data(ticker, engine):
    """Load stock data from database"""
    try:
        df = pd.read_sql(f"SELECT * FROM '{ticker}' ORDER BY Date DESC LIMIT 500", engine)
        if df.empty:
            return None
        
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        df = df.set_index('Date')
        return df
    except Exception as e:
        st.error(f"Error loading {ticker}: {e}")
        return None

# ============================================
# MAIN APP
# ============================================
st.title("📈 AI TRADING DASHBOARD ADVANCED")
st.markdown("**Analisis Teknikal Komprehensif dengan Sinyal Trading Jelas**")

# ============================================
# SIDEBAR - SETTINGS
# ============================================
with st.sidebar:
    st.header("⚙️ PENGATURAN")
    
    # Database check
    st.subheader("📊 Status Database")
    stats, engine = get_database_stats()
    
    if stats:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Stocks", stats['total_stocks'])
        with col2:
            st.write(f"Status: {stats['status']}")
        
        if not stats['stocks']:
            st.error("❌ Tidak ada data. Jalankan pipeline terlebih dahulu.")
            st.stop()
    
    st.divider()
    
    # SECTION 1: PROFILE & RECOMMENDATIONS
    st.subheader("👤 Profil Trader")
    
    trader_profile = st.selectbox(
        "Pilih Profil",
        options=['conservative', 'moderate', 'beginner_growth', 'aggressive'],
        help="Profil akan menentukan rekomendasi yang diberikan"
    )
    
    profile_descriptions = {
        'conservative': '🛡️ Konservatif - Rendah risiko, stabil',
        'moderate': '⚖️  Moderat - Balanced risk/reward',
        'beginner_growth': '📈 Pemula Growth - High growth untuk modal kecil',
        'aggressive': '🚀 Agresif - High risk, high reward',
    }
    
    st.caption(profile_descriptions[trader_profile])
    
    num_recommendations = st.slider(
        "Jumlah Rekomendasi",
        min_value=5,
        max_value=20,
        value=10,
        step=5
    )
    
    st.divider()
    
    # SECTION 2: STOCK SELECTION
    st.subheader("📍 Pilih Saham")
    available_tickers = stats['stocks'] if stats else []
    
    ticker = st.selectbox(
        "Saham",
        options=available_tickers,
        index=0 if available_tickers else 0
    )
    
    st.divider()
    
    # SECTION 3: CHART SETTINGS
    st.subheader("🎨 Pengaturan Chart")
    
    col1, col2 = st.columns(2)
    with col1:
        show_ma5 = st.checkbox("✓ MA 5", value=True)
        show_ma10 = st.checkbox("✓ MA 10", value=True)
        show_ma20 = st.checkbox("✓ MA 20", value=True)
        show_ma50 = st.checkbox("✓ MA 50", value=True)
    
    with col2:
        show_rsi = st.checkbox("✓ RSI", value=True)
        show_volume = st.checkbox("✓ Volume", value=True)
        show_macd = st.checkbox("✓ MACD", value=True)
        show_supertrend = st.checkbox("✓ SuperTrend", value=True)
    
    st.divider()
    
    # SECTION 4: SETTINGS
    st.subheader("⚙️ Opsi Lanjutan")
    
    initial_capital = st.number_input(
        "Modal Awal (IDR)",
        min_value=1000000,
        value=10000000,
        step=1000000
    )
    
    show_explanations = st.checkbox(
        "📚 Tampilkan Penjelasan Indikator",
        value=True,
        help="Tampilkan penjelasan detail untuk setiap indikator"
    )

# ============================================
# MAIN CONTENT
# ============================================

if not engine or not stats:
    st.error("❌ Error connecting to database")
    st.stop()

# PAGE 1: RECOMMENDATIONS
st.header("🎯 1. REKOMENDASI SAHAM BERDASARKAN PROFIL")

try:
    recommender = StockRecommender(engine)
    
    with st.spinner("Menganalisis saham..."):
        recommendations = recommender.get_stock_recommendations(
            trader_profile,
            num_recommendations,
            avoid_retail=True
        )
    
    if not recommendations.empty:
        # Profile description
        profile_info = recommender.get_profile_description(trader_profile)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.subheader(f"{profile_info['name']}")
        with col2:
            st.write(f"**{profile_info['description']}**")
        with col3:
            if st.button("🔄 Refresh", key="refresh_recommendations"):
                st.rerun()
        
        # Display recommendations table
        st.subheader(f"Top {len(recommendations)} Rekomendasi")
        
        display_df = recommendations[['ticker', 'combined_score', 'technical_score', 
                                      'fundamental_score', 'latest_price', 'price_change_pct',
                                      'avg_volume']].copy()
        
        # Color coding
        def style_score(val):
            try:
                score = float(val)
                if score >= 80:
                    return 'color: green; font-weight: bold'
                elif score >= 60:
                    return 'color: orange; font-weight: bold'
                else:
                    return 'color: red'
            except:
                return ''
        
        st.dataframe(
            display_df.style.applymap(style_score, subset=['combined_score']),
            use_container_width=True,
            height=400
        )
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Score", f"{recommendations['combined_score'].mean():.1f}")
        with col2:
            st.metric("Top Score", f"{recommendations['combined_score'].max():.1f}")
        with col3:
            st.metric("Worst Score", f"{recommendations['combined_score'].min():.1f}")
        with col4:
            st.metric("Stocks Analyzed", len(recommendations))
    else:
        st.warning("⚠️ Tidak ada rekomendasi tersedia")

except Exception as e:
    st.error(f"Error: {e}")

st.divider()

# PAGE 2: DETAILED ANALYSIS
st.header("📊 2. ANALISIS DETAIL SAHAM TERPILIH")

try:
    df = load_stock_data(ticker, engine)
    
    if df is None or df.empty:
        st.error(f"❌ Tidak ada data untuk {ticker}")
        st.stop()
    
    # Initialize analyzer
    analyzer = AdvancedAnalyzer()
    
    # Calculate all indicators
    with st.spinner("Menghitung indikator..."):
        df = analyzer.calculate_all_indicators(df)
    
    # Generate strategy
    strategy = analyzer.generate_trading_strategy(df, ticker, trader_profile)
    
    # ============================================
    # SECTION 1: CURRENT PRICE & STATUS
    # ============================================
    st.subheader("💰 Status Harga Saat Ini")
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    current_price = float(latest['Close'])
    prev_price = float(prev['Close'])
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price * 100) if prev_price != 0 else 0
    
    # Price metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Harga Saat Ini",
            format_idr(current_price),
            f"{price_change_pct:+.2f}%"
        )
    
    with col2:
        high_52w = df['High'].tail(252).max() if len(df) >= 252 else df['High'].max()
        st.metric("52W High", format_idr(high_52w))
    
    with col3:
        low_52w = df['Low'].tail(252).min() if len(df) >= 252 else df['Low'].min()
        st.metric("52W Low", format_idr(low_52w))
    
    with col4:
        volume_avg = df['Volume'].tail(20).mean() if len(df) >= 20 else df['Volume'].mean()
        current_volume = float(latest['Volume'])
        vol_ratio = current_volume / volume_avg if volume_avg > 0 else 0
        st.metric("Volume", format_idr(current_volume), f"{vol_ratio:.1f}x avg")
    
    with col5:
        st.metric("Trend", strategy['trend'], delta_color="off")
    
    st.divider()
    
    # ============================================
    # SECTION 2: TRADING STRATEGY
    # ============================================
    st.subheader("🎯 STRATEGI TRADING")
    
    strat = strategy['strategy']
    
    # Main action
    action = strat['action']
    action_color = "🟢" if action == "BUY" else "🔴" if action == "SELL / WAIT" else "🟡"
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("AKSI TRADING", action)
    with col2:
        st.info(f"**{strat['rationale']}**")
    
    # Strategy in columns
    if strat['action'] != 'WAIT':
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            ### 📍 ZONA ENTRY
            **Min:** {format_idr(strat['entry_zone_min'])}
            **Max:** {format_idr(strat['entry_zone_max'])}
            """)
        
        with col2:
            st.markdown(f"""
            ### 🎯 TAKE PROFIT
            **TP 1:** {format_idr(strat['take_profit_1'])}
            **TP 2:** {format_idr(strat['take_profit_2'])}
            **TP 3:** {format_idr(strat['take_profit_3'])}
            """)
        
        with col3:
            st.markdown(f"""
            ### ⛔ CUT LOSS
            **SL:** {format_idr(strat['cut_loss'])}
            """)
        
        with col4:
            acc = strat.get('accumulation_zone', {})
            if acc:
                st.markdown(f"""
                ### 📊 AKUMULASI
                **Trigger:** {format_idr(acc.get('trigger', 0))}
                **Aksi:** {acc.get('action', 'N/A')}
                """)
    
    # Confidence level
    confidence = strategy['confidence_level']
    confidence_color = "🟢" if confidence >= 70 else "🟡" if confidence >= 50 else "🔴"
    
    st.progress(min(confidence / 100, 1.0))
    st.caption(f"{confidence_color} Confidence Level: {confidence:.0f}%")
    
    st.divider()
    
    # ============================================
    # SECTION 3: TECHNICAL INDICATORS
    # ============================================
    st.subheader("📈 RINGKASAN INDIKATOR TEKNIKAL")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**MOVING AVERAGES**")
        if 'MA5' in latest:
            st.write(f"MA5: {format_idr(latest['MA5'])}")
        if 'MA10' in latest:
            st.write(f"MA10: {format_idr(latest['MA10'])}")
        if 'MA20' in latest:
            st.write(f"MA20: {format_idr(latest['MA20'])}")
        if 'MA50' in latest:
            st.write(f"MA50: {format_idr(latest['MA50'])}")
    
    with col2:
        st.write("**MOMENTUM**")
        if 'RSI' in latest:
            rsi = latest['RSI']
            rsi_status = "🔴 Oversold" if rsi < 30 else "🟡 Neutral" if rsi < 70 else "🔴 Overbought"
            st.write(f"RSI (14): {rsi:.1f} {rsi_status}")
        
        if 'MACD' in latest and 'MACD_Signal' in latest:
            macd_status = "🟢 Bullish" if latest['MACD'] > latest['MACD_Signal'] else "🔴 Bearish"
            st.write(f"MACD: {latest['MACD']:.4f} {macd_status}")
    
    with col3:
        st.write("**TREND**")
        if 'SuperTrend_Trend' in latest:
            trend_status = "🟢 UPTREND" if latest['SuperTrend_Trend'] == 1 else "🔴 DOWNTREND"
            st.write(f"SuperTrend: {trend_status}")
        
        if 'Volume_Ratio' in latest:
            vol_strength = "💪 STRONG" if latest['Volume_Ratio'] > 1.2 else "⚡ NORMAL" if latest['Volume_Ratio'] > 0.8 else "📉 WEAK"
            st.write(f"Volume: {latest['Volume_Ratio']:.2f}x {vol_strength}")
    
    st.divider()
    
    # ============================================
    # SECTION 4: DETAILED CHART
    # ============================================
    st.subheader("📊 CHART DENGAN SEMUA INDIKATOR")
    
    # Create figure with subplots
    subplot_count = 3 if show_volume else 2  # Add RSI subplot
    if show_macd:
        subplot_count += 1
    
    spec = [
        {"secondary_y": False},  # Main price chart
        {"secondary_y": False},  # RSI
    ]
    
    if show_macd:
        spec.append({"secondary_y": False})  # MACD
    
    if show_volume:
        spec.append({"secondary_y": False})  # Volume
    
    fig = make_subplots(
        rows=len(spec),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=tuple(f"{s}" for s in ["Price", "RSI", "MACD", "Volume"][:len(spec)]),
        specs=[[{"secondary_y": False}]] + [[{"secondary_y": False}] for _ in range(len(spec)-1)]
    )
    
    # 1. CANDLESTICK
    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    )
    fig.add_trace(candlestick, row=1, col=1)
    
    # 2. MOVING AVERAGES
    ma_settings = [
        ('MA5', 'blue', show_ma5),
        ('MA10', 'orange', show_ma10),
        ('MA20', 'green', show_ma20),
        ('MA50', 'red', show_ma50),
    ]
    
    for ma_name, color, show in ma_settings:
        if show and ma_name in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[ma_name],
                    mode='lines',
                    name=ma_name,
                    line=dict(color=color, width=1)
                ),
                row=1, col=1
            )
    
    # 3. SUPERTREND
    if show_supertrend and 'SuperTrend' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['SuperTrend'],
                mode='lines',
                name='SuperTrend',
                line=dict(color='purple', width=2, dash='dash')
            ),
            row=1, col=1
        )
    
    # 4. RSI
    row_num = 2
    if show_rsi and 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=1)
            ),
            row=row_num, col=1
        )
        
        # Add RSI levels
        fig.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="30", row=row_num, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="70", row=row_num, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="50", row=row_num, col=1)
    
    # 5. MACD
    row_num = 3 if show_rsi else 2
    if show_macd and 'MACD' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['MACD'],
                mode='lines',
                name='MACD',
                line=dict(color='blue', width=1)
            ),
            row=row_num, col=1
        )
        
        if 'MACD_Signal' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['MACD_Signal'],
                    mode='lines',
                    name='Signal',
                    line=dict(color='red', width=1)
                ),
                row=row_num, col=1
            )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=row_num, col=1)
    
    # 6. VOLUME
    row_num = 4 if (show_rsi and show_macd) else 3 if (show_rsi or show_macd) else 2
    if show_volume and 'Volume' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color='rgba(0,100,255,0.5)',
                showlegend=True
            ),
            row=row_num, col=1
        )
    
    # Update layout
    fig.update_layout(
        title=f'{ticker} - Complete Technical Analysis',
        height=1000,
        hovermode='x unified',
        showlegend=True
    )
    
    fig.update_xaxes(title_text="Date", row=len(spec), col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # ============================================
    # SECTION 5: INDICATOR EXPLANATIONS
    # ============================================
    if show_explanations:
        st.subheader("📚 PENJELASAN INDIKATOR")
        
        explainer = IndicatorExplainer()
        indicators = ['MA5', 'MA10', 'MA20', 'MA50', 'RSI', 'RSI_Fibonacci', 'Volume', 'Momentum', 'SuperTrend']
        
        selected_indicator = st.selectbox(
            "Pilih indikator untuk penjelasan detail",
            options=indicators,
            format_func=lambda x: x.replace('_', ' ')
        )
        
        explanation = explainer.get_explanation(selected_indicator)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### {explanation.get('name', selected_indicator)}")
            st.write(f"**Deskripsi:** {explanation.get('description', 'N/A')}")
        
        with col2:
            if 'usage' in explanation:
                st.markdown("**Cara Penggunaan:**")
                st.write(explanation['usage'])
            
            if 'interpretation' in explanation:
                st.markdown("**Interpretasi:**")
                for key, value in explanation['interpretation'].items():
                    st.write(f"- {key}: {value}")
        
        if 'trading_rules' in explanation:
            st.markdown("**Trading Rules:**")
            for rule in explanation['trading_rules']:
                st.write(f"✓ {rule}")
    
    st.divider()
    
    # ============================================
    # SECTION 6: RAW DATA
    # ============================================
    with st.expander("📋 RAW DATA (50 Baris Terakhir)"):
        display_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'MA20', 'MA50', 'RSI', 'MACD', 'SuperTrend']
        available_cols = [col for col in display_cols if col in df.columns]
        
        st.dataframe(
            df[available_cols].tail(50),
            use_container_width=True,
            height=500
        )

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
