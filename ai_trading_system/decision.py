def final_signal(df):
    df['Final'] = 0

    df.loc[(df['Signal'] == 1) & (df['Smart_Money']), 'Final'] = 1
    df.loc[df['Signal'] == -1, 'Final'] = -1

    return df