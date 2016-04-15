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


class IndEventWindow(technical.EventWindow):

    def __init__(self, windows=250, useAdjustedValues=False):
        technical.EventWindow.__init__(self, windows, dtype=object)
        self.__barWrapper = BarWrapper(useAdjustedValues)
       
        self.__mawins   = [5, 10, 20, 30, 60, 90, 120, 250]
        self.__maevents = {} 
        self.__mavol = ma.SMAEventWindow(20)
        self.__mas   = collections.ListDeque(10)
        self.__vol   = collections.ListDeque(20)

        self.__pf1 = None
        self.__pf2 = None

        for i in self.__mawins:
            self.__maEvent     = ma.SMAEventWindow(i)
            self.__maevents[i] = self.__maEvent

        self.__fts  = []

    def boostVol(self, dt, ma20):
        lb1 = None 
        lb2 = None
        if len(self.__vol) > 1:
            yvol = self.__vol[-2]
            nvol = self.__vol[-1]
            lb1  =  nvol / yvol
        if ma20 is not None:
            lb2 = self.__vol[-1] / ma20
        return (lb1, lb2) 

    def MAdirect(self, nma_dict):
        f2 = []
        if len(self.__mas) > 1:
            yma_dict = self.__mas[-2]
            for i in self.__mawins:
                if i in nma_dict and i in yma_dict: 
                    slope = (nma_dict[i] - yma_dict[i]) / yma_dict[i]
                    f2.append(slope)
                else:
                    f2.append(None)
        else:
            f2 = [None] * (len(self.__mawins))
        return f2

    def MAclose(self, nma_dict, nowclose):
        f1 = []
        for i in self.__mawins:
            if i in nma_dict:
                diff = (nowclose - nma_dict[i]) / nma_dict[i]
                f1.append(diff)
            else:
                f1.append(None)
        return f1

    def changePrice(self, dateTime, bars):
        zhangf = None
        zhangd = None
        if len(bars) > 1:
            nbar = bars[-1]
            pbar = bars[-2]
            zhangf = (nbar.getClose() - pbar.getClose()) / pbar.getClose()
            zhangd = (nbar.getClose() - nbar.getOpen()) / nbar.getClose()
        return (zhangf,zhangd)

    # press: f1<0，f2<0, boost>1
    # support: f1>0, f2>0, boost>1
    def MAvalid(self, i, dist, speed, acc, oddma):
        flag = None 
        if dist > 0 and speed > 0 and acc > 0.1:
            flag = 1
        if dist < 0 and speed < 0 and acc > 0.1:
            flag = 0
        if abs(dist) < 0.02 and abs(speed * 1000 * acc) > 20:
            oddma.append(self.__mawins[i])
        return ((flag, self.__mawins[i], dist, speed * 1000 * acc), oddma)

    def updateMAline(self, valid, supma, prsma):
        ret = (supma, prsma) 
        if valid[0] == 1:
            if supma is not None:
                if abs(supma[2]) > abs(valid[2]):
                    ret = (valid, prsma) 
            else:
                ret = (valid, prsma)
        if valid[0] == 0:
            if abs(valid[2]) > 0.01:
                if prsma is not None:
                    if abs(prsma[2]) > abs(valid[2]):
                        ret = (supma, valid)
                else:
                    ret = (supma, valid)
        return ret

    def MAscore(self, f1, f2):
        ret   = None
        score = 0 
        # [5, 10, 20, 30, 60, 90, 120, 250]
        if self.__pf1 is None or self.__pf2 is None:
            return score
        supma = None
        prsma = None
        oddma = []
        for i in range(0, len(self.__mawins)):
            if self.__pf2[i] is None:
                continue
            tmp = self.__pf2[i]
            if abs(self.__pf2[i]) < 0.0000001:
                tmp = 1.0
            boost = abs(f2[i] / tmp)
            (valid, oddma) = self.MAvalid(i, f1[i], f2[i], boost, oddma)
            if valid[0] is not None:
                (supma, prsma) = self.updateMAline(valid, supma, prsma)
            if self.__mawins[i] < 20:
                weight = 5
            if self.__mawins[i] == 20:
                weight = 10
            if self.__mawins[i] > 20 and self.__mawins[i] < 120:
                weight = 8
            if self.__mawins[i] > 90:
                weight = 5
            score = score + weight * f2[i] * 1000 * boost
        sline = None
        sstr = None
        pline = None
        space = None 
        if supma is not None:
            sline = supma[1]
            sstr  = supma[3]
        if prsma is not None:
            pline = prsma[1]
            space = abs(prsma[2])
        ret = (score, sline, sstr, pline, space, oddma) 
        return ret 

    def MAfeature(self, bars, dateTime):
        nma_dict = self.__mas[-1]
        nowclose = bars[-1].getClose()
        fts = []
        
        # 收盘价与均线关系
        f1 = self.MAclose(nma_dict, nowclose)
        # 均线运行方向
        f2 = self.MAdirect(nma_dict)
        # 量能变化 
        lb = self.boostVol(dateTime, self.__mavol.getValue())
        # 价格变化
        bp = self.changePrice(dateTime, bars)
        # K线分形
        
        score = self.MAscore(f1, f2)
        roc   = self.ROC(bars, dateTime)

        self.__pf1 = f1
        self.__pf2 = f2

        fts.append(score)
        fts.append(roc)
        fts.extend(lb)
        fts.extend(bp)

        return fts

    def ROC(self, bars, dateTime):
        ret = None
        if len(bars) > 20:
            nbar   = bars[-1]
            ybar   = bars[-2]
            bbar5  = bars[-5]
            bbar20 = bars[-20]

            roc1 = (nbar.getClose() - ybar.getOpen()) / ybar.getOpen()
            roc2 = (nbar.getClose() - bbar5.getOpen()) / bbar5.getOpen()
            roc3 = (nbar.getClose() - bbar20.getOpen()) / bbar20.getOpen()

            ret = (roc1, roc2, roc3)
        return ret

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        bars = self.getValues()

        for i in self.__mawins:
            self.__maevents[i].onNewValue(dateTime, value.getClose())

        self.__mavol.onNewValue(dateTime, value.getVolume())

        ma_dict = {}
        for i in self.__mawins:
            if self.__maevents[i].windowFull():
                ma_dict[i] = self.__maevents[i].getValue()
        self.__mas.append(ma_dict) 
        self.__vol.append(value.getVolume())

        # collection MA features
        self.__fts.extend(self.MAfeature(bars, dateTime))

    def getValue(self):
        ret = self.__fts 
        self.__fts = []
        return ret


class Indicator(technical.EventBasedFilter):
    def __init__(self, barDataSeries, windows=250, inst=None, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        assert isinstance(barDataSeries, bards.BarDataSeries), \
            "barDataSeries must be a dataseries.bards.BarDataSeries instance"
        technical.EventBasedFilter.__init__(self, barDataSeries, IndEventWindow(useAdjustedValues), maxLen)
###