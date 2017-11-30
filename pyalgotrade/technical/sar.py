# coding: utf-8
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
.. moduleauthor:: liuliu <liuliu.tju@gmail.com>
"""

from pyalgotrade import technical
from pyalgotrade import dataseries
from pyalgotrade.dataseries import bards
from pyalgotrade.utils import collections


class SAREventWindow(technical.EventWindow):
    def __init__(self, period):
        assert(period > 1)
        technical.EventWindow.__init__(self, period + 1, dtype=object)
        self.__period = 2
        self.__value = None
        self.__high = collections.ListDeque(20)
        self.__low  = collections.ListDeque(20)
        self.__long = collections.ListDeque(2)
        self.__nsar = collections.ListDeque(2)
        self.__signal = collections.ListDeque(2)

        self.__long.append(1)

        self.__af    = 0.02
        self.__maxaf = 0.20
        self.__sar  = None 
        self.__ep   = None
        self.__nstat = None
        self.__diff  = None

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        self.__high.append(value.getHigh())
        self.__low.append(value.getLow())
 
        if len(self.__high) == 5:
            self.__sar = min(self.__low)
            self.__ep  = max(self.__high)
            self.__long.append(1)

        if self.__sar is not None and self.__ep is not None:
            act = None 
            ep  = None
            af  = None
            sar = None

            # ------------ COMPUT EP ----------------------#
            if self.__long[-1] == 1:
                # compute NEW EP
                if self.__high[-1] >= self.__ep:
                    ep = self.__high[-1]
                else:
                    ep = self.__ep
            if self.__long[-1] == -1:
                # compute NEW EP
                if self.__low[-1] <= self.__ep:
                    ep = self.__low[-1]
                else:
                    ep = self.__ep
            # ------------ COMPUT SAR ----------------------#
            if self.__long[-1] == self.__long[-2]:
                tmp1 = self.__sar + (self.__ep - self.__sar) * self.__af 
                
                start = -1 - self.__period
                minlw = min(self.__low[start:-1])
                maxhi = max(self.__high[start:-1])

                if self.__long[-1] == 1:
                    if tmp1 < minlw:
                        sar = tmp1
                    else:
                        sar = minlw
                else:
                    if tmp1 > maxhi:
                        sar = tmp1
                    else:
                        sar = maxhi
            else:
                sar = self.__ep 

            # ------------ COMPUT ACT ----------------------#
            if self.__long[-1] == 1:
                if self.__low[-1] >= sar:
                    act = 1
                else:
                    act = -1
            else:
                if self.__high[-1] <= sar:
                    act = -1
                else:
                    act = 1

            # ------------ COMPUT AF ----------------------#
            if self.__long[-1] == act:
                if act == 1:
                    if ep >= self.__ep:
                        if self.__af >= 0.2:
                            af = self.__af
                        else:
                            af = self.__af + 0.02
                    else:
                        af = self.__af        
                else:
                    if ep <= self.__ep:
                        if self.__af >= 0.2:
                            af = self.__af 
                        else:
                            af = self.__af + 0.02
                    else:
                        af = self.__af        
            else:
                af = 0.02

            # 变化信号, 1绿转红，-1红转绿
            signal = 0
            if act == 1 and self.__long[-1] == -1:
                signal = 1
            if act == -1 and self.__long[-1] == 1:
                signal = -1

            # diff >= 0 则为买入周期, abs(diff)表示强度
            # diff = 0.0
            if self.__long[-1] == 1:
                diff = (self.__low[-1] - sar) / (sar + 0.0000001)
            if self.__long[-1] == -1:
                diff = (self.__high[-1] - sar) / (sar + 0.0000001)

            def nextsar(t1, t2, ep, psar, af, minlw, maxhi):
                if t1 == t2:
                    tmp1 = psar + (ep - psar) * af 
                    if t1 == 1:
                        if tmp1 < minlw:
                            sar = tmp1
                        else:
                            sar = minlw
                    else:
                        if tmp1 > maxhi:
                            sar = tmp1
                        else:
                            sar = maxhi
                else:
                    sar = ep 
                return sar

            minlw = min(self.__low[-1], self.__low[-2])
            maxhi = max(self.__high[-1], self.__high[-2])
            
            nsar = nextsar(act, self.__long[-1], ep, sar, af, minlw, maxhi)

            # Future Status，价格阈值, (high, low)
            # 1. 持续
            # 2. 反转
            # if act == 1:
            #     status = (-1, nsar) 
            # if act == -1:
            #     status = (nsar, -1)
            # print 'DEBUG:', dateTime, act, signal, status, self.__high[-1], self.__low[-1]

            self.__ep     = ep
            self.__af     = af
            self.__sar    = sar

            self.__diff   = diff

            self.__signal.append(signal)
            self.__nsar.append(nsar)
            self.__long.append(act)

    def getValue(self):
        return (self.__sar, self.__long[-1], self.__signal[-1], self.__diff, self.__nsar[-1])


class SAR(technical.EventBasedFilter):
    def __init__(self, barDataSeries, period=5, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        assert isinstance(barDataSeries, bards.BarDataSeries), \
            "barDataSeries must be a dataseries.bards.BarDataSeries instance"
        technical.EventBasedFilter.__init__(self, barDataSeries, SAREventWindow(period), maxLen)
#
