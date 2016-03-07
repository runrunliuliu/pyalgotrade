# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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


class SIEventWindow(technical.EventWindow):
    def __init__(self, period, useAdjustedValues, ma20):
        assert(period > 1)
        technical.EventWindow.__init__(self, period, dtype=object)
        self.__barWrapper = BarWrapper(useAdjustedValues)
        self.__ma20 = ma20

    def getValue(self):
        ret = None

        SUOYANG    = 0
        CXSUOLIANG = 0
        if self.windowFull():
            bars = self.getValues()

            nowbar = bars[-1]
            yesbar = bars[-2]
            tb3bar = bars[-3]

            now_rets  = (nowbar.getClose() - yesbar.getClose()) / yesbar.getClose()
            now_vrate = nowbar.getVolume() / yesbar.getVolume()
            now_guang = (nowbar.getHigh() - nowbar.getClose()) / (nowbar.getClose())

            # Before T - 2 
            hist_vol = []
            hist_ret = []
            prevbars = bars[:-2]
            for i in range(len(prevbars)):
                hist_vol.append(prevbars[i].getVolume())
                hist_ret.append((prevbars[i].getClose() - prevbars[i].getOpen()) / prevbars[i].getOpen())
            navol = np.array(hist_vol)
            naret = np.array(hist_ret)
           
            if self.__ma20[-1] is not None:
                # 1. T-4 T-3 T-2 normal vol--[0.9,1.1] and all of increase--[0.01,0.04] 
                # 2. T-1 boost vol and Increase > 0.7
                # 3. T, Close() ~ High() but shink vol
                diffrate = navol[1:] / navol[:-1] 
                normvol  = ((diffrate > 0.8) & (diffrate < 1.2)).all()
                normret  = ((naret > -0.001) & (naret < 0.06)).all()
                yes_vrate = yesbar.getVolume() / tb3bar.getVolume() 
                if normvol == True and normret == True and yes_vrate > 1.7 \
                        and now_vrate < 1.0 and now_vrate > 0.5 \
                        and now_rets > 0.0 and now_guang < 0.001:
                    SUOYANG = 1
                # Current Day volume rate and returns
                # if volrate > 0.3 and volrate < 1.0 and returns > 0.095:

        ret = (SUOYANG,CXSUOLIANG)
        return ret


class ShrinkVolRise(technical.EventBasedFilter):
    def __init__(self, barDataSeries, period=5, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        assert isinstance(barDataSeries, bards.BarDataSeries), \
            "barDataSeries must be a dataseries.bards.BarDataSeries instance"
        ma20 = ma.SMA(barDataSeries.getVolumeDataSeries(), 20, maxLen)
        technical.EventBasedFilter.__init__(self, barDataSeries, SIEventWindow(period, useAdjustedValues, ma20), maxLen)
###
