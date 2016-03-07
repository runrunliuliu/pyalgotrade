PyAlgoTrade++
=============
PyAlgoTrade++是PyAlgoTrade的升级版，其在兼容原版的接口的基础上，为了适应中国股票市场的规则，增加了一些参数，具体如下：

主要新增特性
----------
1. 交易规则相关
  * 涨跌停的限制
  * T+1或者T+0的可配置
2. 特殊平开仓条件，提供简便的接口，避免代码多次重复编写
  * 最多持仓时间参数，到期日强制平仓
  * 平仓上下限，price =［low high］，股价突破区间边界，强制平仓
3. 指标集
  * 量能
  * 形态
  * 强势涨停

TODO Lists
----------
1. 交易规则
   * 持有标的后可做日内假T+0的回测支持；
2. 指标集
   * 均线系统

PyAlgoTrade++ is an upgrated version of pyAlgotrade
PyAlgoTrade
===========

[![version status](https://pypip.in/v/pyalgotrade/badge.png)](https://pypi.python.org/pypi/pyalgotrade)
[![downloads](https://pypip.in/d/pyalgotrade/badge.png)](https://pypi.python.org/pypi/pyalgotrade)
[![build status](https://travis-ci.org/gbeced/pyalgotrade.png?branch=master)](https://travis-ci.org/gbeced/pyalgotrade)
[![Coverage Status](https://coveralls.io/repos/gbeced/pyalgotrade/badge.svg?branch=master)](https://coveralls.io/r/gbeced/pyalgotrade?branch=master)


PyAlgoTrade is an **event driven algorithmic trading** Python library. Although the initial focus
was on **backtesting**, **paper trading** is now possible using:

 * [Bitstamp](https://www.bitstamp.net/) for Bitcoins
 * [Xignite](https://www.xignite.com/) for stocks

and **live trading** is now possible using:

 * [Bitstamp](https://www.bitstamp.net/) for Bitcoins

To get started with PyAlgoTrade take a look at the [tutorial](http://gbeced.github.io/pyalgotrade/docs/v0.17/html/tutorial.html) and the [full documentation](http://gbeced.github.io/pyalgotrade/docs/v0.17/html/index.html).

Main Features
-------------

 * Event driven.
 * Supports Market, Limit, Stop and StopLimit orders.
 * Supports any type of time-series data in CSV format like Yahoo! Finance, Google Finance, Quandl and NinjaTrader.
 * [Xignite](https://www.xignite.com/) realtime feed.
 * Bitcoin trading support through [Bitstamp](https://www.bitstamp.net/).
 * Technical indicators and filters like SMA, WMA, EMA, RSI, Bollinger Bands, Hurst exponent and others.
 * Performance metrics like Sharpe ratio and drawdown analysis.
 * Handling Twitter events in realtime.
 * Event profiler.
 * TA-Lib integration.

Installation
------------

PyAlgoTrade is developed using Python 2.7 and depends on:

 * [NumPy and SciPy](http://numpy.scipy.org/).
 * [pytz](http://pytz.sourceforge.net/).
 * [dateutil](https://dateutil.readthedocs.org/en/latest/).
 * [requests](http://docs.python-requests.org/en/latest/).
 * [matplotlib](http://matplotlib.sourceforge.net/) for plotting support.
 * [ws4py](https://github.com/Lawouach/WebSocket-for-Python) for Bitstamp support.
 * [tornado](http://www.tornadoweb.org/en/stable/) for Bitstamp support.
 * [tweepy](https://github.com/tweepy/tweepy) for Twitter support.

You can install PyAlgoTrade using pip like this:

```
pip install pyalgotrade
```
