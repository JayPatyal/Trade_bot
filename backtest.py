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

def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + dt.timedelta(days=4)
    return (next_month - dt.timedelta(days=next_month.day)).day

class MonthlyFlows(bt.Strategy):
    
    params = (
        ("end_of_month", 23),
        ("start_of_month", 7),
    )
    def __init__(self):
        self.order = None
        self.dataclose = self.datas[0].close
        
    def notify_order(self, order):
        # No more orders
        self.order = None 
        
    def next(self):
        
        # Get today's date, day of month, and 
        # last day of current month
        dt_ = self.datas[0].datetime.date(0)
        dom = dt_.day
        ldm = last_day_of_month(dt_)
        
        # If an order is pending, exit
        if self.order:
            return
        
        # Check if we are in the market
        if not self.position:
            
            # We're in the first week of the month, sell
            if dom <= self.params.start_of_month:

                # Sell the entire portfolio
                self.order = self.order_target_percent(target=-1)
                
                print(f"ELL at {self.data_close[0]}")
            
            if dom >= self.params.end_of_month:

                # Buy the entire portfolio
                self.order = self.order_target_percent(target=1)
                
                print(f"BUY at {self.data_close[0]}")
                
        else:
            
            # If we're long
            if self.position.size > 0:
                
                # And not within the last week of the month, close
                if not self.params.end_of_month <= dom <= ldm:
                    
                    print(f"CLOSE at {self.data_close[0]}")

                    self.order = self.order_target_percent(target=0.0)
            if self.position.size < 0:
                
                # And not within the first week of the month, close
                if not 1 <= dom <= self.params.start_of_month:
                    
                    print(f"CLOSE at {self.data_close[0]}")

                    # self.order = self.close()
                    self.order = self.order_target_percent(target=0.0)
                    
data = openbb_data_to_bt_data(
    "TLT", 
    start_date="2002-01-01",
    end_date="2022-06-30"
)

cerebro = bt.Cerebro(stdstats=False)

cerebro.adddata(data)
cerebro.broker.setcash(1000.0)

cerebro.addstrategy(MonthlyFlows)

cerebro.addobserver(bt.observers.Value)

cerebro.addanalyzer(
    bt.analyzers.Returns, _name="returns"
)
cerebro.addanalyzer(
    bt.analyzers.TimeReturn, _name="time_return"
)

backtest_result = cerebro.run()

returns_dict = backtest_result[0].analyzers.time_return.get_analysis()

returns_df = (
    pd.DataFrame(
        list(returns_dict.items()),
        columns = ["date", "return"]
    )
    .set_index("date")
)

bench = openbb.stocks.load(
    "TLT",
    start_date="2002-01-01",
    end_date="2022-06-30"
)["Adj Close"]

qs.reports.metrics(
    returns_df,
    benchmark=bench,
    mode="full"
)

