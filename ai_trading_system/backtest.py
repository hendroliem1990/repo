def backtest(df, initial_capital=10000000, signal_col='Final'):
    df['Return'] = df['Close'].pct_change()
    df['Signal_for_Backtest'] = df[signal_col].shift(1).fillna(0)

    # Long-only portfolio: invest only when the signal is BUY
    df['Position_LongOnly'] = df['Signal_for_Backtest'].apply(lambda x: 1 if x == 1 else 0)
    df['Strategy_LongOnly'] = df['Position_LongOnly'] * df['Return']
    df['Cum_Strategy_LongOnly'] = (1 + df['Strategy_LongOnly']).cumprod()

    # Long-short strategy for comparison
    df['Strategy_LongShort'] = df['Signal_for_Backtest'] * df['Return']
    df['Cum_Strategy_LongShort'] = (1 + df['Strategy_LongShort']).cumprod()

    df['Cum_Market'] = (1 + df['Return']).cumprod()
    df['Portfolio_Value'] = initial_capital * df['Cum_Strategy_LongOnly']
    df['Market_Value'] = initial_capital * df['Cum_Market']

    return df