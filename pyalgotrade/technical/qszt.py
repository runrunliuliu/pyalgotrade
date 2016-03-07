# PyAlgoTrade
#
# Copyright 2016- liuliu.tju@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

from pyalgotrade import technical
from pyalgotrade import dataseries
from pyalgotrade.utils import collections
from pyalgotrade.dataseries import bards
from pyalgotrade.technical import ma
from array import array
import numpy as np


class BarWrapper(object):
    def __init__(self, useAdjusted):
        self.__useAdjusted = useAdjusted

    def getLow(self, bar_):
        return bar_.getLow(self.__useAdjusted)

    def getHigh(self, bar_):
        return bar_.getHigh(self.__useAdjusted)

    def getClose(self, bar_):
        return bar_.getClose(self.__useAdjusted)

    def getVol(self, bar_):
        return bar_.getVolume()


def get_low_high_values(barWrapper, bars):
    currBar = bars[0]
    lowestLow = barWrapper.getLow(currBar)
    highestHigh = barWrapper.getHigh(currBar)
    for i in range(len(bars)):
        currBar = bars[i]
        lowestLow = min(lowestLow, barWrapper.getLow(currBar))
        highestHigh = max(highestHigh, barWrapper.getHigh(currBar))
    return (lowestLow, highestHigh)


class QSZTEventWindow(technical.EventWindow):
    def __init__(self, windows, useAdjustedValues, ma1):
        assert(windows > 1)
        technical.EventWindow.__init__(self, windows, dtype=object)
        self.__barWrapper = BarWrapper(useAdjustedValues)
        self.__windows = windows
        
        self.__maEventWindow = ma.SMAEventWindow(ma1)
        self.__ma = collections.ListDeque(256)

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        bars = self.getValues()

        # Call Event Window or ONLY get Last Day indicator
        self.__maEventWindow.onNewValue(dateTime, value.getClose())
        if not self.__maEventWindow.windowFull():
            return 
        else:
            self.__ma.append(self.__maEventWindow.getValue())

        if value is not None and self.windowFull():
            # 1. T-4 = 0.10
            # 2. T-3,T-2,T-1, shrink vol along self.__ma, lowPrice() > T-4.openPrice()
            # 3. T down-through ma but closePrice > ma
            # bars = self.getValues()
            zt  = 0 
            bar = None
            barclose = []
            for i in range(1,self.__windows + 1):
                bar = bars[i * -1]
                pchange = 0
                if i < self.__windows:
                    prebar = bars[ (i + 1) * -1]
                    pchange = (bar.getClose() - prebar.getClose()) / prebar.getClose()
                if bar.getClose() == bar.getHigh() and pchange > 0.090:
                    zt = i
                    break
                barclose.insert(0,bar.getClose())

            if bar is None or zt < 2:
                return
            print bars[-1].getDateTime(),self.__ma[(zt - 1) * -1:]
            print bars[-1].getDateTime(),bar.getDateTime(),zt,barclose

    def getValue(self):
        ret = None
        # mas  = self.__ma[(-1 * self.__windows):]
        # manp = np.array(mas)
        # diffrate = manp[1:] / manp[:-1] 
        return ret


class QiangShiZhangTing(technical.EventBasedFilter):
    def __init__(self, barDataSeries, windows=5, ma1=5, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        assert isinstance(barDataSeries, bards.BarDataSeries), \
            "barDataSeries must be a dataseries.bards.BarDataSeries instance"
        technical.EventBasedFilter.__init__(self, barDataSeries, QSZTEventWindow(windows, useAdjustedValues, ma1), maxLen)
###
