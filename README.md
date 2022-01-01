# trade_quant
1,项目简述

一个均线量化交易策略,并进行回测在efinance中获取5minute数据,经numpy处理生成ticks数据,计算20日均线,设置策略,价格低于均线一定比例买入,高于一定比例卖出,并且计算出每笔交易的时间,价格,利润以及总利润,胜率。通过matplotlib处理,显示每一笔交易的价格和利润等交易信息


2,准备工作

准备python3

准备requests,pandas,numpy,matplotlib,efinance

pip install (对应要安装的第三方库)


3,克隆代码

git clone git@github.com:zqtz/trade_quant.git


4,运行代码

输入回测的股票代码和投入的资金


5,效果图
![image](https://user-images.githubusercontent.com/61925624/147843284-d4d232b4-16a7-4963-bf53-e921f6772e6d.png)
![image](https://user-images.githubusercontent.com/61925624/147843286-f89c6690-beaf-4afa-915c-25a408311174.png)

