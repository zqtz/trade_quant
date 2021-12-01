# 导入请求库,时间处理库,数据处理和画图的第三方库,文件处理的os库
import requests
from datetime import time,datetime,timedelta
import pandas as pd
import numpy as np
from dateutil import parser
import os
import matplotlib.pyplot as plt

# 该函数的作用为bar_generator_for_backtesting函数提供形成K线的数据
# 该例子的储存个人地址为:
# tickpath = D:\\代码\\爬虫项目\\spider_one_year_1\\量化交易\\300014_ticks.csv
# bar_path = 'D:\\代码\\爬虫项目\\spider_one_year_1\\量化交易\\300014_5m.csv'
def get_ticks_for_backtesting(tick_path, bar_path):
    # 判断tick_path是否存在,存在则利用read_csv进行数据的处理,为bar_generator_for_backtesting函数提供形成K线的数据
    if os.path.exists(tick_path):#判断是否存在
        # 存在即进行数据的处理
        # 读取数据
        ticks = pd.read_csv(
            tick_path,
            parse_dates = ['datetime'],
            index_col = 'datetime'
            )
        tick_list = []
#         处理数据形成tick数据
        for index, row in ticks.iterrows():
            tick_list.append((index, row[0]))
        ticks = tick_list
#         不存在即进行bar_path数据的处理
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
#例如:np.arange(30.00, 30.11, 0.02)          
#当step的步长大于0.01时,30.11则会不包含再tick数据里面,为让其包含在tick数据里面,需要 np.append(arr, row['high']),np.append(arr, row['low'])
            arr = np.arange(row['open'], row['high'], step)
            arr = np.append(arr, row['high'])
            arr = np.append(arr, np.arange(row['open']-step, row['low'], -step))
            arr = np.append(arr, row['low'])
            arr = np.append(arr, row['close'])

            i = 0
#             利用timedelta对数据进行切分微分化,返回tick数据并储存到tick_bar里面
            dt = parser.parse(str(row['datetime'])) - timedelta(minutes=5)
            for item in arr:
                ticks.append((dt+timedelta(seconds=0.1*i), item))
                i += 1
        tick_df = pd.DataFrame(ticks, columns=['datetime', 'price'])
        tick_df.to_csv(tick_path, index=0)
    return ticks

class AstockTrading(object):
#     AstockTrading,有真实交易和模拟交易(目前为模拟交易),需要的参数为strategy_name
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
#         定义买入的函数
        self._order_number += 1
        key = "order" + str(self._order_number)#定义order交易的名称
#         将交易的订单储存到当前的交易中
        self._current_orders[key] = {
            "open_datetime": self._Dt[0],
            "open_price": price,
            "volume": volume
        }
#     将开仓价格储存到初始化的列表中
        self._open_price = price

#     定义卖出函数
    def sell(self,key,price):
#         将卖出的订单数据储存到当前的订单
        self._current_orders[key]['close_price'] = price#卖出的价格
        self._current_orders[key]['close_datetime'] = self._Dt[0]#卖出的时间
#         利润pnl为(卖出价格-开仓价格)*成交数量-(卖出价格+开仓价格)*成交数量*3/10000-(卖出价格)*成交数量/1000,假设交易佣金为万分之三,印花税为千分之一
        self._current_orders[key]['pnl'] = (price-self._current_orders[key]['open_price'])\
        *self._current_orders[key]['volume']-price*self._current_orders[key]['volume']/1000\
        -(price+self._current_orders[key]['open_price'])*self._current_orders[key]['volume']*3/10000
#     一旦卖出将当前订单,则将当前订单移除到历史订单,以便跟新当前订单进行买卖
        self._history_orders[key] = self._current_orders.pop(key)
# 将卖出价储存到初始化的卖出列表
        self._close_price = price

#     该函数定义一个均线策略并加入A股T+1交易规则的限制
    def strategy(self):
#         判断是否为新的20日K线,是则算出20日均线的值,并储存到初始化的ma20中
        if self._is_new_bar:
            sum_ = 0
            for item in self._Close[1:21]:
                sum_ = sum_ +item
            self._ma20 = sum_/20
#             当当前订单的长度为0是,证明还没有开仓,则考虑达到设定的条件进行买入
        if 0 == len(self._current_orders):
#         如果当前价格小于ma20*0.93则买入
                if self._Close[0] < 0.93 * self._ma20:
                    volume = int((100000/self._Close[0])/100)*100
                    self.volume = volume
#                当前价格为买一,为立即交,买入价格加0.01为卖一,可马上成交
                    self.buy(self._Close[0]+0.01,volume)
#             当当前订单的长度为1时,证明已开仓,则考虑达到设定的条件进行卖出(设定的条件为价格小于ma20*1.07)   
        elif 1 == len(self._current_orders):
#         如果当前价格大于ma20*1.07则卖出
            if self._Close[0] > self._ma20*1.07:
                key = list(self._current_orders.keys())[0]
#             如果触发卖出条件且卖出日期不等于买进日期则卖出
                if self._Dt[0].date() != self._current_orders[key]['open_datetime']:
                    self.sell(key,self._Close[0])
                    print('open datetime is: %s,close datetime is: %s.'% (self._history_orders[key]['open_datetime'],self._Dt[0].date()))
#                 如果触发卖出条件但卖出日期等于买进日期则打印T+0限制
                else:
                    print('sell order aborted due to T+0 limited')
        else:
#             出现其他情况,则交易异常
            raise ValueError('order raise error')
    
#   该函数判断tick数据是否为新的5日K线数据
    def bar_generator_for_backtesting(self, tick):
#         如果能交易时间的分钟单位能被5整除且当前时间不等于上一根5分钟K线数据的数据,则为新K线,对返回的tick数据进行处理
        if tick[0].minute % 5 == 0 and \
                tick[0].minute != self._last_bar_start_minute:
            self._last_bar_start_minute = tick[0].minute

            self._Open.insert(0, tick[1])
            self._High.insert(0, tick[1])
            self._Low.insert(0, tick[1])
            self._Close.insert(0, tick[1])
            self._Dt.insert(0, tick[0])
            self._is_new_bar = True
#             否则更新当前K线数据
        else:
            self._High[0] = max(self._High[0], tick[1])
            self._Low[0] = min(self._Low[0], tick[1])
            self._Close[0] = tick[1]
            self._Dt[0] = tick[0]
            self._is_new_bar = False
            
# 定义一个运行函数
    def run_backtesting(self, ticks):
#         将处理的ticks数据进行遍历
        for tick in ticks:
#         对tick数据进行处理
            self.bar_generator_for_backtesting(tick)
#     如果为初始化状态则运行策略
            if self._init:
                self.strategy()
#             否则进入else
            else:
#         如果_open价格列表长度大于等于100进行策略
                if len(self._Open) >= 100:
                    self._init = True
                    self.strategy()
# 启动策略
if __name__ == '__main__':
    tick_path = 'D:\\代码\\爬虫项目\\spider_one_year_1\\量化交易\\300014_ticks.csv'
    bar_path = 'D:\\代码\\爬虫项目\\spider_one_year_1\\量化交易\\300014_5m.csv'
    ticks = get_ticks_for_backtesting(tick_path, bar_path)#传入参数
    ast = AstockTrading('ma')#启动AstockTrading,参数为('ma'),ma自定义
    ast.run_backtesting(ticks)#启动策略
    print(ast._history_orders)#打印历史订单信息
    for order in ast._history_orders:#获取order的key值
        print(ast._history_orders[order])#
    profit_orders = 0
    loss_orders = 0
    profit = 0
    orders = ast._history_orders
    for key in orders.keys():
        profit += orders[key]['pnl']#获取总利润
        if orders[key]['pnl'] >= 0:
            profit_orders += 1#计算利润大于零的次数
        else:
            loss_orders += 1#计算利润小于零的次数
    profit_late = profit_orders/len(orders)#计算胜率
    loss_late = loss_orders/len(orders)#计算输的概率
    print('胜的概率为:'+str(profit_late),'输的概率为:'+str(loss_late))
    print('利润为:'+str(profit))
    orders_df = pd.DataFrame(orders).T#转置数据让matplotlib处理
    plt.bar(orders.keys(),orders_df.loc[:,'pnl'])
    plt.show()#
