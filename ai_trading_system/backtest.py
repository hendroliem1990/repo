def backtest(df):
    df['Return'] = df['Close'].pct_change()
    df['Strategy'] = df['Signal'].shift(1) * df['Return']

    df['Cum_Strategy'] = (1 + df['Strategy']).cumprod()
    df['Cum_Market'] = (1 + df['Return']).cumprod()

    return df