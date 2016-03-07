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


class CDEventWindow(technical.EventWindow):
    def __init__(self, windows, useAdjustedValues, ma1, threshold):
        assert(windows > 0)
        technical.EventWindow.__init__(self, windows, dtype=object)
        self.__barWrapper = BarWrapper(useAdjustedValues)
        self.__windows = windows
        
        self.__maEventWindow = ma.SMAEventWindow(ma1)
        self.__ma = collections.ListDeque(256)
        self.__cd1 = collections.ListDeque(256)
        self.__cd2 = collections.ListDeque(256)
        self.__cd3 = collections.ListDeque(256)
        
        self.__bars = collections.ListDeque(256)
        self.__threshold = threshold

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        bars = self.getValues()

        self.__bars.append(bars[-1])

        # Call Event Window or ONLY get Last Day indicator
        self.__maEventWindow.onNewValue(dateTime, value.getClose())
        if not self.__maEventWindow.windowFull():
            return 
        else:
            self.__ma.append(self.__maEventWindow.getValue())

        if value is not None and self.windowFull():
            nowbar = bars[-1]

            barclose = nowbar.getLow() 
            zhangfu  = (nowbar.getClose() - nowbar.getOpen()) / nowbar.getOpen()
           
            liangbi = 0
            if len(self.__bars) > 1:
                yesbar  = self.__bars[-2]
                liangbi = nowbar.getVolume() / yesbar.getVolume()

            self.__cd2.append(zhangfu)
            self.__cd3.append(liangbi)

            if barclose < self.__ma[-1] * self.__threshold:
                self.__cd1.append(1)
            else:
                self.__cd1.append(0)

    def getValue(self):
        ret = (self.__cd1, self.__cd2, self.__cd3) 
        return ret


class ChaoDie(technical.EventBasedFilter):
    def __init__(self, barDataSeries, windows=5, ma1=5, threshold=0.90, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        assert isinstance(barDataSeries, bards.BarDataSeries), \
            "barDataSeries must be a dataseries.bards.BarDataSeries instance"
        technical.EventBasedFilter.__init__(self, barDataSeries, CDEventWindow(windows, useAdjustedValues, ma1, threshold), maxLen)
###
