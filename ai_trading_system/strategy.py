def generate_signal(df):
    """Generate trading signals based on RSI and MACD"""
    df['Signal'] = 0

    # Only generate signals if we have the required indicators
    if 'RSI' in df.columns and 'MACD' in df.columns and 'MACD_signal' in df.columns:
        df.loc[(df['RSI'] > 50) & (df['MACD'] > df['MACD_signal']), 'Signal'] = 1
        df.loc[(df['RSI'] < 50) & (df['MACD'] < df['MACD_signal']), 'Signal'] = -1

    return df