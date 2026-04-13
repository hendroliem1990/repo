def generate_signal(df):
    df['Signal'] = 0

    df.loc[(df['RSI'] > 50) & (df['MACD'] > df['MACD_signal']), 'Signal'] = 1
    df.loc[(df['RSI'] < 50) & (df['MACD'] < df['MACD_signal']), 'Signal'] = -1

    return df