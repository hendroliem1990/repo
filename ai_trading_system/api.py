from fastapi import FastAPI, HTTPException
import pandas as pd
from database import get_engine
from strategy import generate_signal
import sqlalchemy

app = FastAPI()
engine = get_engine()

@app.get("/")
def read_root():
    return {"status": "API Running", "endpoints": ["/signal/{ticker}", "/tables"]}

@app.get("/tables")
def get_tables():
    try:
        inspector = sqlalchemy.inspect(engine)
        tables = inspector.get_table_names()
        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        return {"error": str(e), "tables": []}

@app.get("/signal/{ticker}")
def get_signal(ticker: str):
    try:
        df = pd.read_sql(f"SELECT * FROM '{ticker}'", engine)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data for ticker {ticker}")
        
        df = generate_signal(df)
        last = df.iloc[-1]

        return {
            "ticker": ticker,
            "signal": int(last.get('Signal', 0)),
            "rsi": float(last.get('RSI', 0)),
            "macd": float(last.get('MACD', 0)),
            "status": "success"
        }
    except HTTPException:
        raise
    except (pd.errors.DatabaseError, Exception) as e:
        error_msg = str(e)
        if "no such table" in error_msg.lower():
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found in database")
        raise HTTPException(status_code=500, detail=f"Error: {error_msg[:100]}")