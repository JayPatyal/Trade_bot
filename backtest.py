import datetime as dt

import pandas as pd

from openbb_terminal.sdk import openbb
import quantstats as qs
import backtrader as bt

def openbb_data_to_bt_data(symbol, start_date, end_date):
    
    df = openbb.stocks.load(symbol, start_date=start_date, end_date=end_date)
    
    fn = f"{symbol.lower()}.csv"
    df.to_csv(fn)
    
    return bt.feeds.YahooFinanceCSVData(
        dataname=fn,
        fromdate=dt.datetime.strptime(start_date, '%Y-%m-%d'),
        todate=dt.datetime.strptime(end_date, '%Y-%m-%d')
    )

