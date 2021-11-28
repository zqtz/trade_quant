import requests
from datetime import time,datetime,timedelta
import pandas as pd
import numpy as np
from dateutil import parser
import os
import matplotlib.pyplot as plt

def get_ticks_for_backtesting(tick_path, bar_path):
    if os.path.exists(tick_path):
        ticks = pd.read_csv(
            tick_path,
            parse_dates = ['datetime'],
            index_col = 'datetime'
            )
        tick_list = []
        for index, row in ticks.iterrows():
            tick_list.append((index, row[0]))
        ticks = tick_list
    else:
        bar_5m = pd.read_excel(bar_path)
        ticks = []

        for index, row in bar_5m.iterrows():
            if row['open'] < 30:
                step = 0.01
            elif row['open'] < 60:
                step = 0.03
            elif row['open'] < 90:
                step = 0.05
            else:
                step = 0.1
            arr = np.arange(row['open'], row['high'], step)
            arr = np.append(arr, row['high'])
            arr = np.append(arr, np.arange(row['open']-step, row['low'], -step))
            arr = np.append(arr, row['low'])
            arr = np.append(arr, row['close'])

            i = 0
            dt = parser.parse(str(row['datetime'])) - timedelta(minutes=5)
            for item in arr:
                ticks.append((dt+timedelta(seconds=0.1*i), item))
                i += 1
        tick_df = pd.DataFrame(ticks, columns=['datetime', 'price'])
        tick_df.to_csv(tick_path, index=0)
    return ticks

class AstockTrading(object):
    def __init__(self,strategy_name):
        self._strategy_name = strategy_name
        self._Open = []
        self._High = []
        self._Low = []
        self._Close = []
        self._Dt = []
        self._trade_time = None
        self._last_bar_start_minute = None
        self._is_new_bar = None
        self._history_orders = {}
        self._current_orders = {}
        self._order_number = 0
        self._ma20 = []
        self._init = None
        self._open_price = None
        self._close_price = None

    def buy(self,price,volume):
        self._order_number += 1
        key = "order" + str(self._order_number)
        self._current_orders[key] = {
            "open_datetime": self._Dt[0],
            "open_price": price,
            "volume": volume
        }
        self._open_price = price

    def sell(self,key,price):
        self._current_orders[key]['close_price'] = price
        self._current_orders[key]['close_datetime'] = self._Dt[0]
        self._current_orders[key]['pnl'] = (price-self._current_orders[key]['open_price'])\
        *self._current_orders[key]['volume']-price*self._current_orders[key]['volume']/1000\
        -(price+self._current_orders[key]['open_price'])*self._current_orders[key]['volume']*3/10000
        self._history_orders[key] = self._current_orders.pop(key)

        self._close_price = price

    def strategy(self):
        if self._is_new_bar:
            sum_ = 0
            for item in self._Close[1:21]:
                sum_ = sum_ +item
            self._ma20 = sum_/20
        if 0 == len(self._current_orders):
                if self._Close[0] < 0.93 * self._ma20:
                    volume = int((100000/self._Close[0])/100)*100
                    self.volume = volume
                    self.buy(self._Close[0]+0.01,volume)
        elif 1 == len(self._current_orders):
            if self._Close[0] > self._ma20*1.07:
                key = list(self._current_orders.keys())[0]
                if self._Dt[0].date() != self._current_orders[key]['open_datetime']:
                    self.sell(key,self._Close[0]-0.01)
                    print('open datetime is: %s,close datetime is: %s.'% (self._history_orders[key]['open_datetime'],self._Dt[0].date()))
                else:
                    print('sell order aborted due to T+0 limited')
        else:
            raise ValueError('order raise error')

    def bar_generator_for_backtesting(self, tick):
        if tick[0].minute % 5 == 0 and \
                tick[0].minute != self._last_bar_start_minute:
            self._last_bar_start_minute = tick[0].minute

            self._Open.insert(0, tick[1])
            self._High.insert(0, tick[1])
            self._Low.insert(0, tick[1])
            self._Close.insert(0, tick[1])
            self._Dt.insert(0, tick[0])
            self._is_new_bar = True
        else:
            self._High[0] = max(self._High[0], tick[1])
            self._Low[0] = min(self._Low[0], tick[1])
            self._Close[0] = tick[1]
            self._Dt[0] = tick[0]
            self._is_new_bar = False

    def run_backtesting(self, ticks):
        for tick in ticks:
            self.bar_generator_for_backtesting(tick)
            if self._init:
                self.strategy()
            else:
                if len(self._Open) >= 100:
                    self._init = True
                    self.strategy()

if __name__ == '__main__':
    tick_path = 'D:\\代码\\爬虫项目\\spider_one_year_1\\量化交易\\300014_ticks.csv'
    bar_path = 'D:\\代码\\爬虫项目\\spider_one_year_1\\量化交易\\300014_5m.csv'
    ticks = get_ticks_for_backtesting(tick_path, bar_path)
    ast = AstockTrading('ma')
    ast.run_backtesting(ticks)
    print(ast._history_orders)
    for order in ast._history_orders:
        print(ast._history_orders[order])
    profit_orders = 0
    loss_orders = 0
    profit = 0
    orders = ast._history_orders
    for key in orders.keys():
        profit += orders[key]['pnl']
        if orders[key]['pnl'] >= 0:
            profit_orders += 1
        else:
            loss_orders += 1
    profit_late = profit_orders/len(orders)
    loss_late = loss_orders/len(orders)
    print(profit_late,loss_late)
    print(profit)
    orders_df = pd.DataFrame(orders).T
    plt.bar(orders.keys(),orders_df.loc[:,'pnl'])
    plt.show()