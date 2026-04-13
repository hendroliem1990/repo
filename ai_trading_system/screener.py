import pandas as pd
from database import get_engine
import sqlalchemy

engine = get_engine()

def get_top_stock():
    try:
        # Use inspector for newer SQLAlchemy compatibility
        inspector = sqlalchemy.inspect(engine)
        tables = inspector.get_table_names()
    except Exception as e:
        print(f"Error getting tables: {e}")
        return []
    
    result = []

    for t in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM '{t}'", engine)

            if len(df) < 50:
                continue

            last = df.iloc[-1]

            if last.get('RSI', 0) > 50 and last.get('MACD', 0) > last.get('MACD_signal', 0):
                result.append(t)
        except Exception as e:
            print(f"Error processing table {t}: {e}")
            continue

    return result