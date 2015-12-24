# -*- coding: utf-8 -*-
from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade.talibext import indicator
"""
Created on Sun Dec 20 19:21:42 2015

@author: liu
"""


class Patterns(strategy.BacktestingStrategy):
    
    def __init__(self, feed, instrument):
        
        strategy.BacktestingStrategy.__init__(self, feed)
        
        self.__instrument = instrument
        self.__position = None
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(False)
        self.__prices = feed[instrument].getPriceDataSeries()

    def onEnterCanceled(self, position):
        self.__position = None

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY: " + str(position.getEntryOrder().getInstrument()) + " at $%.2f" % (execInfo.getPrice()))

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL: " + str(position.getEntryOrder().getInstrument()) + " at $%.2f" % (execInfo.getPrice()))
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        barDs = self.getFeed().getDataSeries(self.__instrument)
        sar = indicator.CDLHAMMER(barDs,barDs.__len__())
        if sar is not None:
            self.info("indicator: $%d" % sar[-1]) 
