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
from pyalgotrade.utils import collections


class ROCcompute(object):
    def __init__(self):
        self.__ok = 1

    def getROC(self, pbar, nbar, itype):
        ROC = None 

        if pbar is None or nbar is None:
            return ROC

        if itype == 1:
            pval = pbar.getClose()
            nval = nbar.getHigh()

            ROC = (nval - pval) / (pval + 0.000000001)
        return ROC


class ROCEventWindow(technical.EventWindow):
    def __init__(self, windowSize):
        technical.EventWindow.__init__(self, windowSize)

    def getValue(self):
        ret = None
        if self.windowFull():
            prev = self.getValues()[0]
            actual = self.getValues()[-1]
            if actual is not None and prev is not None:
                diff = float(actual - prev)
                if diff == 0:
                    ret = float(0)
                elif prev != 0:
                    ret = diff / prev
        return ret


class RateOfChange(technical.EventBasedFilter):
    """Rate of change filter as described in http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:rate_of_change.

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param valuesAgo: The number of values back that a given value will compare to. Must be > 0.
    :type valuesAgo: int.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.
    """

    def __init__(self, dataSeries, valuesAgo, maxLen=dataseries.DEFAULT_MAX_LEN):
        assert(valuesAgo > 0)
        technical.EventBasedFilter.__init__(self, dataSeries, ROCEventWindow(valuesAgo + 1), maxLen)


class BARROCEventWindow(technical.EventWindow):
    def __init__(self, windowSize, ntype):
        technical.EventWindow.__init__(self, windowSize, dtype=object)

        # 1. T+1.open() - T.close() / T.close()
        self.__type = ntype 
        self.__roc = ROCcompute()

        self.__bars = collections.ListDeque(256)
        self.__r1 = None

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)

        if value is not None and self.windowFull():
            bars = self.getValues()
            pbar = bars[0]
            nbar = bars[-1]
            
            roc  = self.__roc.getROC(pbar, nbar, self.__type)
            self.__r1 = roc

    def getValue(self):
        ret = self.__r1 
        return ret


class RateOfBarChange(technical.EventBasedFilter):
    def __init__(self, bardataSeries, valuesAgo, ntype=1, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, bardataSeries, BARROCEventWindow(valuesAgo + 1, ntype), maxLen)
#
