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
from pyalgotrade.technical import ma


def gain_loss_one(prevValue, nextValue):
    change = nextValue - prevValue
    if change < 0:
        gain = 0
        loss = abs(change)
    else:
        gain = change
        loss = 0
    return gain, loss


# [begin, end)
def avg_gain_loss(values, begin, end):
    rangeLen = end - begin
    if rangeLen < 2:
        return None

    gain = 0
    loss = 0
    for i in xrange(begin+1, end):
        currGain, currLoss = gain_loss_one(values[i-1], values[i])
        gain += currGain
        loss += currLoss
    return (gain/float(rangeLen-1), loss/float(rangeLen-1))


def vol(values, period):
    assert(period > 1)
    if len(values) < period + 1:
        return None

    avgGain, avgLoss = avg_gain_loss(values, 0, period)
    for i in xrange(period, len(values)):
        gain, loss = gain_loss_one(values[i-1], values[i])
        avgGain = (avgGain * (period - 1) + gain) / float(period)
        avgLoss = (avgLoss * (period - 1) + loss) / float(period)

    if avgLoss == 0:
        return 100
    rs = avgGain / avgLoss
    return 100 - 100 / (1 + rs)


class VOLEventWindow(technical.EventWindow):
    def __init__(self, period):
        assert(period > 1)
        # We need N + 1 samples to calculate N averages because they are calculated based on the diff with previous values.
        technical.EventWindow.__init__(self, period + 1)
        self.__value = None
        self.__prevGain = None
        self.__prevLoss = None
        self.__period = period

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)

        # Formula from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:relative_strength_index_rsi
        if value is not None and self.windowFull():
            pass

    def getValue(self):
        return self.__value


class VOLUME(technical.EventBasedFilter):
    """Relative Strength Index filter as described in http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:relative_strength_index_rsi.

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param period: The period. Note that if period is **n**, then **n+1** values are used. Must be > 1.
    :type period: int.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.
    """

    def __init__(self, dataSeries, ma5, ma10, ma20, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, dataSeries, VOLEventWindow(ma5), maxLen)
        self.__ma5  = ma.SMA(dataSeries, ma5, maxLen)
        self.__ma10 = ma.SMA(dataSeries, ma10, maxLen)
        self.__ma20 = ma.SMA(dataSeries, ma20, maxLen)

    def getMA5(self):
        return self.__ma5

    def getMA20(self):
        return self.__ma20
##
