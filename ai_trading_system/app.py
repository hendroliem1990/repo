import streamlit as st
import pandas as pd
from database import get_engine
from strategy import generate_signal
from smart_money import smart_money_signal
from decision import final_signal
from backtest import backtest
import sqlalchemy

engine = get_engine()

st.title("🔥 AI TRADING DASHBOARD")

# Get available tables
try:
    inspector = sqlalchemy.inspect(engine)
    available_tables = inspector.get_table_names()
except:
    available_tables = ['BBCA', 'BBRI', 'BMRI', 'ASII']

if not available_tables:
    st.error("❌ No data available. Please run pipeline.py first.")
    st.stop()

ticker = st.selectbox("Select Ticker", available_tables, index=0)

try:
    df = pd.read_sql(f"SELECT * FROM '{ticker}'", engine)
    
    if df.empty:
        st.error(f"❌ No data for {ticker}")
        st.stop()
    
    df = generate_signal(df)
    df = smart_money_signal(df)
    df = final_signal(df)
    df = backtest(df)

    st.subheader("📈 Strategy vs Market")
    st.line_chart(df[['Cum_Strategy','Cum_Market']])

    st.subheader("🚨 Signal")
    st.write(df[['Final']].tail(10))

    st.subheader("📊 Data")
    st.dataframe(df.tail(50))
    
except Exception as e:
    st.error(f"❌ Error processing data: {str(e)}")