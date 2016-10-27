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
from pyalgotrade.technical import ma
from pyalgotrade import dataseries
from pyalgotrade.utils import collections


def get_low_high_values(bars):
    currBar     = bars[0]
    lowestLow   = currBar.getLow()
    highestHigh = currBar.getHigh()
    for i in range(len(bars)):
        currBar     = bars[i]
        lowestLow   = min(lowestLow, currBar.getLow())
        highestHigh = max(highestHigh, currBar.getHigh())
    return (lowestLow, highestHigh)


class KDJEventWindow(technical.EventWindow):
    """Stochastic Oscillator filter as described in
    http://stockcharts.com/school/doku.php?st=stochastic+oscillator&id=chart_school:technical_indicators:stochastic_oscillator_fast_slow_and_full.
    Note that the value returned by this filter is %K. To access %D use :meth:`getD`.

    :param barDataSeries: The BarDataSeries instance being filtered.
    :type barDataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param period: The period. Must be > 1.
    :type period: int.
    :param dSMAPeriod: The %D SMA period. Must be > 1.
    :type dSMAPeriod: int.
    :param useAdjustedValues: True to use adjusted Low/High/Close values.
    :type useAdjustedValues: boolean.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.
    """
    def __init__(self, maxlen, kperiod, dperiod):
        # We need N + 1 samples to calculate N averages because they are calculated based on the diff with previous values.
        technical.EventWindow.__init__(self, maxlen, dtype=object)
        self.__value = None

        self.__kEMAWindow = ma.EMAEventWindow(kperiod, 1.0)
        self.__dEMAWindow = ma.EMAEventWindow(dperiod, 1.0)

        self.__rsv = None
        self.__K   = None 
        self.__D   = None 
        self.__J   = None 

        self.__KDcomp = collections.ListDeque(30)
        self.__DeadX  = collections.ListDeque(30)
        self.__DeadXX = None 

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)

        # Init 
        self.__DeadXX = None

        if value is not None and self.windowFull():
            lowestLow, highestHigh = get_low_high_values(self.getValues())
            currentClose = self.getValues()[-1].getClose()
            self.__rsv = (currentClose - lowestLow) / (0.0001 + float(highestHigh - lowestLow)) * 100

        self.__kEMAWindow.onNewValue(dateTime, self.__rsv)
        self.__K = self.__kEMAWindow.getValue()

        self.__dEMAWindow.onNewValue(dateTime, self.__K)
        self.__D = self.__dEMAWindow.getValue()

        if self.__K is not None and self.__D is not None:
            self.__J = 3 * self.__K - 2 * self.__D
            self.__KDcomp.append((dateTime, self.__K - self.__D))

        if len(self.__KDcomp) > 1 and self.__K <= self.__D and self.__KDcomp[-2][1] > 0:
            self.__DeadX.append((dateTime, self.__K))
            if len(self.__DeadX) > 1:
                self.__DeadXX = ((dateTime, self.__K), self.__DeadX[-2])

    def getDeadXX(self):
        return self.__DeadXX
#
