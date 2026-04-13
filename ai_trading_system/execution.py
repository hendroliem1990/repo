def execute_trade(signal, ticker):
    if signal == 1:
        print(f"BUY {ticker}")
    elif signal == -1:
        print(f"SELL {ticker}")