import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from database import get_engine
from strategy import generate_signal
from smart_money import smart_money_signal
from decision import final_signal
from backtest import backtest
from recommendation import StockRecommender
import sqlalchemy
import ta

engine = get_engine()

st.set_page_config(page_title="AI Trading Dashboard", page_icon="🔥", layout="wide")

st.title("🔥 AI TRADING DASHBOARD - IDX")

# Helpers

def format_idr(value):
    return f"Rp {value:,.0f}"


def calculate_portfolio_metrics(df, initial_capital):
    metrics = {}
    if 'Portfolio_Value' in df.columns and not df.empty:
        metrics['final_value'] = df['Portfolio_Value'].iloc[-1]
        metrics['growth_pct'] = (metrics['final_value'] / initial_capital - 1) * 100
        metrics['market_value'] = df['Market_Value'].iloc[-1]
        metrics['max_drawdown'] = ((df['Portfolio_Value'].cummax() - df['Portfolio_Value']) / df['Portfolio_Value'].cummax()).max() * 100
        metrics['total_trades'] = int(df['Final'].diff().fillna(0).ne(0).sum())
    return metrics

# Initialize recommender
recommender = StockRecommender()

# Get available tables first
try:
    inspector = sqlalchemy.inspect(engine)
    available_tables = [t for t in inspector.get_table_names() if not t.endswith('_fundamentals') and t != 'corporate_actions' and t != 'data_collection_metadata' and t != 'test_table']
except:
    available_tables = ['BBCA', 'BBRI', 'BMRI', 'ASII']

if not available_tables:
    st.error("❌ No data available. Please run pipeline.py first.")
    st.stop()

# Sidebar for settings
with st.sidebar:
    st.header("📊 Settings")

    # Trader profile selection
    trader_profile = st.selectbox(
        "Trader Profile",
        ['conservative', 'moderate', 'beginner_growth', 'aggressive'],
        index=2,  # Default to beginner_growth
        help="Conservative: Low risk, stable stocks\nModerate: Balanced risk/reward\nBeginner Growth: High growth for small capital\nAggressive: High risk, high reward"
    )

    # Number of recommendations
    num_recommendations = st.slider("Number of Recommendations", 5, 20, 10)
    avoid_retail = st.checkbox(
        "Hindari saham retail berat",
        value=True,
        help="Filter saham retail-heavy dengan volume trading sangat tinggi untuk mengurangi paparan crowd trading."
    )
    alert_oversold = st.checkbox(
        "Notifikasi Oversold",
        value=True,
        help="Tampilkan peringatan saat RSI saham terpilih berada di bawah 30."
    )
    starting_capital = st.number_input(
        "Modal Portofolio (IDR)",
        min_value=1000000,
        value=10000000,
        step=1000000,
        help="Modal awal untuk simulasi portofolio berbasis sinyal trading."
    )

    st.divider()

    # Individual stock analysis
    st.header("📈 Stock Analysis")
    ticker = st.selectbox("Select Ticker", available_tables, index=0 if available_tables else 0)

    # Chart settings
    st.subheader("📈 Chart Settings")
    show_ma5 = st.checkbox("MA 5", value=True)
    show_ma10 = st.checkbox("MA 10", value=True)
    show_ma20 = st.checkbox("MA 20", value=True)
    show_ma50 = st.checkbox("MA 50", value=True)
    show_fibonacci = st.checkbox("Fibonacci Levels", value=True)
    show_volume = st.checkbox("Volume", value=True)

# Stock Recommendations Section
st.header("🎯 AI Stock Recommendations")

profile_info = recommender.get_profile_description(trader_profile)
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.subheader(f"📊 {profile_info['name']}")
    st.write(f"**Focus:** {profile_info['focus']}")

with col2:
    st.write(f"**Description:** {profile_info['description']}")

with col3:
    if st.button("🔄 Refresh Recommendations", type="primary"):
        st.rerun()
    broker_note = (
        f"**Broker Summary**\n"
        f"- Retail-heavy filter: {'✅ Aktif' if avoid_retail else '❌ Mati'}\n"
        f"- Volume cap: {recommender.trader_profiles[trader_profile].get('max_volume', 'Tidak ada batas')}\n"
        f"- Oversold alerts: {'✅ Aktif' if alert_oversold else '❌ Mati'}"
    )
    st.markdown(broker_note)

# Get recommendations
with st.spinner(f"Analyzing stocks for {trader_profile} profile..."):
    recommendations_df = recommender.get_stock_recommendations(trader_profile, num_recommendations, avoid_retail=avoid_retail)

if recommendations_df.empty:
    st.warning("⚠️ No recommendations available. Please ensure pipeline has been run with sufficient data.")
else:
    # Display recommendations in a nice table
    st.subheader(f"Top {len(recommendations_df)} Recommended Stocks")

    # Format the dataframe for display
    display_df = recommendations_df.copy()
    display_df['latest_price'] = display_df['latest_price'].apply(lambda x: f"Rp {x:,.0f}")
    display_df['price_change_pct'] = display_df['price_change_pct'].apply(lambda x: f"{x:+.2f}%")
    display_df['avg_volume'] = display_df['avg_volume'].apply(lambda x: f"{x:,.0f}")
    display_df['combined_score'] = display_df['combined_score'].apply(lambda x: f"{x:.1f}")

    # Color coding for scores
    def color_score(val):
        try:
            score = float(val)
            if score >= 80:
                return 'background-color: #d4edda; color: #155724'  # Green
            elif score >= 60:
                return 'background-color: #fff3cd; color: #856404'  # Yellow
            else:
                return 'background-color: #f8d7da; color: #721c24'  # Red
        except:
            return ''

    styled_df = display_df.style.applymap(color_score, subset=['combined_score'])

    st.dataframe(
        styled_df,
        column_config={
            "ticker": st.column_config.TextColumn("Ticker", width="small"),
            "combined_score": st.column_config.TextColumn("Score", width="small"),
            "technical_score": st.column_config.NumberColumn("Technical", format="%.1f"),
            "fundamental_score": st.column_config.NumberColumn("Fundamental", format="%.1f"),
            "latest_price": st.column_config.TextColumn("Price", width="medium"),
            "price_change_pct": st.column_config.TextColumn("Change", width="small"),
            "avg_volume": st.column_config.TextColumn("Avg Volume", width="medium"),
            "data_points": st.column_config.NumberColumn("Data Points", width="small")
        },
        hide_index=True,
        use_container_width=True
    )

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_score = recommendations_df['combined_score'].mean()
        st.metric("Average Score", f"{avg_score:.1f}")

    with col2:
        top_score = recommendations_df['combined_score'].max()
        st.metric("Top Score", f"{top_score:.1f}")

    with col3:
        avg_volume = recommendations_df['avg_volume'].mean()
        st.metric("Avg Volume", f"{avg_volume:,.0f}")

    with col4:
        total_stocks = len(recommendations_df)
        st.metric("Stocks Analyzed", total_stocks)

st.divider()

# Individual Stock Analysis Section
st.header("📈 Individual Stock Analysis")

try:
    df = pd.read_sql(f"SELECT * FROM '{ticker}'", engine)

    if df.empty:
        st.error(f"❌ No data for {ticker}")
        st.stop()

    # Ensure date column is datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date').sort_index()
    elif df.index.name == 'Date' or 'date' in df.columns:
        if 'date' in df.columns:
            df['Date'] = pd.to_datetime(df['date'])
            df = df.set_index('Date').sort_index()

    # Calculate technical indicators first
    if len(df) >= 14:  # Minimum data for RSI
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    if len(df) >= 26:  # Minimum data for MACD
        df['MACD'] = ta.trend.macd(df['Close'])
        df['MACD_signal'] = ta.trend.macd_signal(df['Close'])

    # Generate signals
    df = generate_signal(df)
    df = smart_money_signal(df)
    df = final_signal(df)
    df = backtest(df, initial_capital=starting_capital)

    # Current price display
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        current_price = df['Close'].iloc[-1] if not df.empty else 0
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        price_change = current_price - prev_price
        price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0

        st.metric(
            label="Current Price",
            value=f"Rp {current_price:,.0f}",
            delta=f"{price_change:+,.0f} ({price_change_pct:+.2f}%)"
        )

    with col2:
        high_52w = df['High'].tail(252).max() if len(df) >= 252 else df['High'].max()
        st.metric("52W High", f"Rp {high_52w:,.0f}")

    with col3:
        low_52w = df['Low'].tail(252).min() if len(df) >= 252 else df['Low'].min()
        st.metric("52W Low", f"Rp {low_52w:,.0f}")

    with col4:
        volume_avg = df['Volume'].tail(30).mean() if len(df) >= 30 else df['Volume'].mean()
        st.metric("Avg Volume", f"{volume_avg:,.0f}")

    # Technical Indicators Summary
    st.subheader("📊 Technical Indicators")

    # Calculate current technical levels (ensure they exist)
    current_rsi = None
    current_macd = None
    current_macd_signal = None

    if 'RSI' in df.columns and not df['RSI'].empty:
        current_rsi = df['RSI'].iloc[-1]
    if 'MACD' in df.columns and not df['MACD'].empty:
        current_macd = df['MACD'].iloc[-1]
    if 'MACD_signal' in df.columns and not df['MACD_signal'].empty:
        current_macd_signal = df['MACD_signal'].iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if current_rsi is not None and not pd.isna(current_rsi):
            rsi_status = "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral"
            st.metric("RSI", f"{current_rsi:.1f}", rsi_status)
        else:
            st.metric("RSI", "N/A")

    if alert_oversold and current_rsi is not None and current_rsi < 30:
        st.warning(f"🚨 Oversold Alert: RSI {current_rsi:.1f} untuk {ticker}. Pertimbangkan entry dekat support.")

    with col2:
        if current_macd is not None and current_macd_signal is not None and not pd.isna(current_macd) and not pd.isna(current_macd_signal):
            macd_status = "Bullish" if current_macd > current_macd_signal else "Bearish"
            st.metric("MACD", f"{current_macd:.2f}", macd_status)
        else:
            st.metric("MACD", "N/A")

    with col3:
        # Support/Resistance levels
        recent_low = df['Low'].tail(20).min()
        recent_high = df['High'].tail(20).max()
        st.metric("Recent Support", f"Rp {recent_low:,.0f}")

    with col4:
        st.metric("Recent Resistance", f"Rp {recent_high:,.0f}")

    # Calculate Moving Averages
    if show_ma5 and len(df) >= 5:
        df['MA5'] = df['Close'].rolling(window=5).mean()
    if show_ma10 and len(df) >= 10:
        df['MA10'] = df['Close'].rolling(window=10).mean()
    if show_ma20 and len(df) >= 20:
        df['MA20'] = df['Close'].rolling(window=20).mean()
    if show_ma50 and len(df) >= 50:
        df['MA50'] = df['Close'].rolling(window=50).mean()

    # Calculate Fibonacci Levels
    if show_fibonacci and len(df) >= 50:
        # Get recent high and low for Fibonacci calculation (last 252 trading days ≈ 1 year)
        recent_period = min(252, len(df))
        recent_data = df.tail(recent_period)
        recent_high = recent_data['High'].max()
        recent_low = recent_data['Low'].min()

        # Fibonacci retracement levels
        diff = recent_high - recent_low
        if diff > 0:  # Avoid division by zero
            df['Fib_0.236'] = recent_low + 0.236 * diff
            df['Fib_0.382'] = recent_low + 0.382 * diff
            df['Fib_0.5'] = recent_low + 0.5 * diff
            df['Fib_0.618'] = recent_low + 0.618 * diff
            df['Fib_0.786'] = recent_low + 0.786 * diff  # Additional level

    # Create main chart
    st.subheader(f"📈 {ticker} - Candlestick Chart")

    # Create subplots
    if show_volume:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.03, subplot_titles=(f'{ticker} Price', 'Volume'),
                           row_width=[0.7, 0.3])
    else:
        fig = go.Figure()

    # Candlestick
    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    )

    if show_volume:
        fig.add_trace(candlestick, row=1, col=1)
    else:
        fig.add_trace(candlestick)

    # Moving Averages
    colors = ['blue', 'orange', 'green', 'red']
    ma_names = ['MA5', 'MA10', 'MA20', 'MA50']
    ma_labels = ['MA 5', 'MA 10', 'MA 20', 'MA 50']

    for i, (ma_name, label) in enumerate(zip(ma_names, ma_labels)):
        if ma_name in df.columns and locals()[f'show_{ma_name.lower()}']:
            ma_trace = go.Scatter(
                x=df.index,
                y=df[ma_name],
                mode='lines',
                name=label,
                line=dict(color=colors[i], width=1)
            )
            if show_volume:
                fig.add_trace(ma_trace, row=1, col=1)
            else:
                fig.add_trace(ma_trace)

    # Fibonacci Levels
    if show_fibonacci and 'Fib_0.236' in df.columns:
        fib_levels = ['Fib_0.236', 'Fib_0.382', 'Fib_0.5', 'Fib_0.618', 'Fib_0.786']
        fib_labels = ['Fib 23.6%', 'Fib 38.2%', 'Fib 50%', 'Fib 61.8%', 'Fib 78.6%']
        fib_colors = ['rgba(255,0,0,0.4)', 'rgba(255,165,0,0.4)', 'rgba(0,255,0,0.4)', 'rgba(0,0,255,0.4)', 'rgba(128,0,128,0.4)']

        for level, label, color in zip(fib_levels, fib_labels, fib_colors):
            if level in df.columns:
                fib_trace = go.Scatter(
                    x=df.index,
                    y=df[level],
                    mode='lines',
                    name=label,
                    line=dict(color=color, width=1, dash='dash')
                )
                if show_volume:
                    fig.add_trace(fib_trace, row=1, col=1)
                else:
                    fig.add_trace(fib_trace)

    # Volume bar chart
    if show_volume:
        volume_trace = go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            marker_color='rgba(0,100,255,0.5)'
        )
        fig.add_trace(volume_trace, row=2, col=1)

    # Update layout
    fig.update_layout(
        title=f'{ticker} Technical Analysis',
        yaxis_title='Price (IDR)',
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=True
    )

    if show_volume:
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Trading Signals Section
    st.subheader("🚨 Trading Signals")

    # Map numeric signals to labels
    signal_labels = df['Final'].map({1: 'BUY', -1: 'SELL', 0: 'HOLD'}).fillna('HOLD')
    latest_signals = signal_labels.tail(10).to_frame(name='Final')

    # Create signal summary
    signal_counts = signal_labels.value_counts()
    buy_signals = signal_counts.get('BUY', 0)
    sell_signals = signal_counts.get('SELL', 0)
    hold_signals = signal_counts.get('HOLD', 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Buy Signals", buy_signals)

    with col2:
        st.metric("Sell Signals", sell_signals)

    with col3:
        st.metric("Hold Signals", hold_signals)

    with col4:
        latest_signal = signal_labels.iloc[-1] if not df.empty else 'N/A'
        st.metric("Latest Signal", latest_signal)

    # Recent signals table
    st.subheader("Recent Signals")
    st.dataframe(latest_signals)

    # Backtest Results
    st.subheader("📊 Backtest Results")

    if 'Cum_Strategy_LongOnly' in df.columns and 'Cum_Market' in df.columns:
        backtest_return = (df['Cum_Strategy_LongOnly'].iloc[-1] - 1) * 100 if not df.empty else 0
        market_return = (df['Cum_Market'].iloc[-1] - 1) * 100 if not df.empty else 0
        portfolio_metrics = calculate_portfolio_metrics(df, starting_capital)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Strategy Return", f"{backtest_return:.2f}%")

        with col2:
            st.metric("Market Return", f"{market_return:.2f}%")

        with col3:
            st.metric("Portfolio Value", format_idr(portfolio_metrics.get('final_value', 0)))

        with col4:
            st.metric("Total Trades", portfolio_metrics.get('total_trades', 0))

        # Performance chart
        st.subheader("Strategy vs Market Performance")
        perf_fig = go.Figure()
        perf_fig.add_trace(go.Scatter(x=df.index, y=df['Cum_Strategy_LongOnly'], mode='lines', name='Strategy (Long Only)', line=dict(color='green')))
        perf_fig.add_trace(go.Scatter(x=df.index, y=df['Cum_Market'], mode='lines', name='Market', line=dict(color='blue')))
        perf_fig.update_layout(title='Cumulative Returns', xaxis_title='Date', yaxis_title='Cumulative Return')
        st.plotly_chart(perf_fig, use_container_width=True)

        # Portfolio tracking
        st.subheader("📈 Portfolio Tracking")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Starting Capital", format_idr(starting_capital))
        with col2:
            st.metric("Growth", f"{portfolio_metrics.get('growth_pct', 0):.2f}%")
        with col3:
            st.metric("Max Drawdown", f"{portfolio_metrics.get('max_drawdown', 0):.2f}%")
        with col4:
            st.metric("Market Value", format_idr(portfolio_metrics.get('market_value', 0)))

        track_fig = go.Figure()
        track_fig.add_trace(go.Scatter(x=df.index, y=df['Portfolio_Value'], mode='lines', name='Portfolio Value', line=dict(color='green')))
        track_fig.add_trace(go.Scatter(x=df.index, y=df['Market_Value'], mode='lines', name='Market Value', line=dict(color='blue', dash='dash')))
        track_fig.update_layout(title='Portofolio vs Pasar', xaxis_title='Date', yaxis_title='Nilai (IDR)')
        st.plotly_chart(track_fig, use_container_width=True)

    # Raw data (collapsible)
    with st.expander("📋 Raw Data (Last 50 rows)"):
        st.dataframe(df.tail(50))

except Exception as e:
    st.error(f"❌ Error processing data: {str(e)}")
    st.code(str(e))