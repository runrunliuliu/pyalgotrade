# -*- coding: utf-8 -*-

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
"""
Created on Sun Dec 20 19:21:42 2015

@author: liu
"""


class DualMAcross(strategy.BacktestingStrategy):
    
    def __init__(self, feed, instrument, ma1,ma2,ma3,ma4):
        
        strategy.BacktestingStrategy.__init__(self, feed)
        
        self.__instrument = instrument
        self.__position = None
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(False)
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__ma1 = ma.SMA(self.__prices, ma1)
        self.__ma2 = ma.SMA(self.__prices, ma2)
        self.__ma3 = ma.SMA(self.__prices, ma3)
        self.__ma4 = ma.SMA(self.__prices, ma4)

    def getMa1(self):
        return self.__ma1
 
    def getMa4(self):
        return self.__ma4
 
    def getMa2(self):
        return self.__ma2
      
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
        # If a position was not opened, check if we should enter a long position.
        # if self.__ma2[-1] is not None:
        #    self.info("ma1: %.2f ma2: %.2f" % (self.__ma1[-1],self.__ma2[-1]))
        #    self.info("ma3: %.2f ma4: %.2f" % (self.__ma3[-1],self.__ma4[-1]))
        if self.__position is None:
            if cross.cross_above(self.__ma1, self.__ma2) > 0:
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                # Enter a buy market order. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, shares, True)
        # Check if we have to exit the position.
        elif not self.__position.exitActive() and cross.cross_below(self.__ma3, self.__ma4) > 0:
            self.__position.exitMarket()
