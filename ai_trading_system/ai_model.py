from sklearn.ensemble import RandomForestClassifier

def train_model(df):
    df = df.dropna()

    X = df[['RSI','MACD']]
    y = (df['Close'].shift(-1) > df['Close']).astype(int)

    model = RandomForestClassifier()
    model.fit(X, y)

    return model