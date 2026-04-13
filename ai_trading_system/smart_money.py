def smart_money_signal(df):
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Smart_Money'] = (df['Volume'] > 2 * df['Vol_Avg']) & (df['Close'] > df['Close'].shift(1))
    return df