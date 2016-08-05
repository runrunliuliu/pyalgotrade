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
from pyalgotrade.technical import kline 
from array import array
from pyalgotrade.barfeed import indfeed
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

    def __init__(self, inst, windows=250, useAdjustedValues=False):
        technical.EventWindow.__init__(self, windows, dtype=object)
        self.__barWrapper = BarWrapper(useAdjustedValues)
       
        self.__mawins   = [5, 10, 20, 30, 60, 90, 120, 250]
        self.__maevents = {} 
        self.__mavol5  = ma.SMAEventWindow(5)
        self.__mavol10 = ma.SMAEventWindow(10)
        self.__mas   = collections.ListDeque(10)
        self.__vol   = collections.ListDeque(20)
        self.__kline = kline.KLineEventWindow(7) 
        
        self.__madirect   = collections.ListDeque(3)
        self.__maposition = collections.ListDeque(3)
        self.__mascore = collections.ListDeque(5)

        self.__pf1 = None
        self.__pf2 = None

        for i in self.__mawins:
            self.__maEvent     = ma.SMAEventWindow(i)
            self.__maevents[i] = self.__maEvent

        self.__fts  = []

        self.__inst = inst

        self.__dt = indfeed.Feed()
        self.__dt.addBarsFromCSV('dt',"./data/dtboard.csv.out")

    def boostVol(self, dt, ma5, ma20):
        lb1 = -1 
        lb2 = -1 
        lb3 = -1 
        if len(self.__vol) > 1:
            yvol = self.__vol[-2]
            nvol = self.__vol[-1]
            lb1  =  nvol / yvol
        if ma5 is not None:
            lb2 = self.__vol[-1] / ma5
        if ma20 is not None:
            lb3 = self.__vol[-1] / ma20
        return (lb1, lb2, lb3) 

    # 短线空头排列
    def MAdxShort(self, nma_dict, madirect): 
        ret = 0
        if len(nma_dict) > 3: 
            m12 = nma_dict[5]  - nma_dict[10]
            m23 = nma_dict[10] - nma_dict[20]
            m34 = nma_dict[20] - nma_dict[30]
            if m12 < 0 and m23 < 0 and m34 < 0 and madirect[2] < 0:
                ret = 1
        return ret

    # 长线空头排列
    def MAcxShort(self, dateTime, f1, f2, bars):
        ret  = 0 
        bear = 0
        # 收盘价连续三日低于年线进入熊市
        if f2[-1] is not None:
            t3  = bars[-3].getClose()
            t2  = bars[-2].getClose()
            t1  = bars[-1].getClose()
            mas = self.__mas
            if 250 in mas[-1] and 250 in mas[-2] and 250 in mas[-3] and \
                    t1 < mas[-1][250] and t2 < mas[-2][250] and t3 < mas[-3][250]:
                bear = 1

        # MA WORSE计算，极端的清仓
        # 1. 均线皆拐头朝下
        # 2. MA60连续三日拐头< -0.001 
        # 3. MA20当日拐头 <- -0.001
        if f2[-1] is not None and f2[-1] < 0 and f1[-1] < -0.03 and \
                self.__madirect[-1] is not None and \
                self.__madirect[-2] is not None and \
                self.__madirect[-3] is not None:
            ma60  = [self.__madirect[-1][4], self.__madirect[-2][4], self.__madirect[-3][4]]
            nma60 = np.asarray(ma60)
            cnt60 = (nma60 < -0.001).sum()
            
            dma20 = f2[2]

            nf2   = np.asarray(f2)
            count = (nf2 < 0).sum()
            if count == len(f2) and cnt60 == 3 and dma20 < -0.001:
                ret = 1
        return (bear, ret)

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

    def MAposition(self, nma_dict, nowclose):
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
        sline = 'NULL' 
        sstr  = 'NULL'
        pline = 'NULL'
        space = 'NULL'
        if supma is not None:
            sline = supma[1]
            sstr  = supma[3]
        if prsma is not None:
            pline = prsma[1]
            space = abs(prsma[2])
        ret = (score, sline, sstr, pline, space, oddma) 
        return ret 

    def MAattack(self, dateTime, f1, f2, dxshort, cxshort, nma_dict, wsma5):
        # [5, 10, 20, 30, 60, 90, 120, 250]
        ret = -1 
        if dxshort == 1 or cxshort[1] == 1 or wsma5 == 1:
            return ret
        def worse(ind, diff): 
            ret = 0
            if diff is not None and abs(diff) < 0.08 and \
                    self.__madirect[-1] is not None and \
                    self.__madirect[-2] is not None and \
                    self.__madirect[-3] is not None:
                ma  = [self.__madirect[-1][ind], self.__madirect[-2][ind], self.__madirect[-3][ind]]
                nma = np.asarray(ma)
                print nma
                cnt = (nma < -0.001).sum()
                if cnt == 3:
                    ret = 1
            return ret

        ma60  = worse(4, f1[4])
        ma90  = worse(5, f1[5])
        ma120 = worse(6, f1[6])
        ma250 = worse(7, f1[7])
        print dateTime, ma60, ma90, ma120, ma250

    def MAfeature(self, bars, dateTime):
        nma_dict = self.__mas[-1]
        nowclose = bars[-1].getClose()
        fts = []
        
        # 收盘价与均线关系
        f1 = self.MAposition(nma_dict, nowclose)
        # 均线运行方向
        f2 = self.MAdirect(nma_dict)
        # 量能变化 
        lb = self.boostVol(dateTime, self.__mavol5.getValue(), self.__mavol10.getValue())
        # 价格变化
        bp = self.changePrice(dateTime, bars)
        # K线分形, MOVE TO K-LINE MODULE
        # kl = self.KLine(dateTime, bars)
       
        score = self.MAscore(f1, f2)
        roc   = self.ROC(bars, dateTime)

        dxshort = self.MAdxShort(nma_dict, f2)
        cxshort = self.MAcxShort(dateTime, f1, f2, bars)

        ma = (1024,1024)
        if f2[-1] is not None:
            dma250 = "{:.4f}".format(f2[-1])
            pma250 = "{:.4f}".format(f1[-1])
            ma = (dma250, pma250)

        wsma5 = 0
        if f2[0] is not None and self.__pf2[0] is not None:
            if f2[0] < -0.01 and abs(f2[0] / self.__pf2[0]) > 2:
                wsma5 = 1
            if f2[0] < -0.02:
                wsma5 = 1
        cxshort = cxshort + (wsma5,0) 

        # 计算MA系统的短期攻击度
        # attack = self.MAattack(dateTime, f1, f2, dxshort, cxshort, nma_dict, wsma5)

        # dtboard
        dt = self.dtboard(dateTime, lb)

        fts.append(score)
        fts.append(roc)
        fts.append(dxshort)
        fts.append(cxshort)
        fts.append(ma)
        fts.append(self.__kline.getValue())
        fts.append(lb)
        fts.append(bp)
        fts.append(dt)
        
        self.__pf1 = f1
        self.__pf2 = f2
        self.__madirect.append(f2)
        self.__maposition.append(f1)
        self.__mascore.append(score)

        return fts

    def KLine(self, dateTime, bars):
        mubei = 0
        yby   = 0
        if len(bars) > 1:
            ybar = bars[-2]
            nbar = bars[-1]
            # 放量墓碑线
            solid = (nbar.getClose() - nbar.getOpen()) / nbar.getOpen()
            uline = (nbar.getHigh() - nbar.getOpen()) / nbar.getOpen()
            dline = (nbar.getClose() - nbar.getLow()) / nbar.getLow()
            zhenf = (nbar.getHigh() - nbar.getLow()) / nbar.getLow()
            if solid < 0 and abs(solid) < 0.02 and zhenf > 0.03:
                mubei = (abs(uline) / (abs(uline) + abs(solid)))
            # 放量阴包阳
            yx = ybar.getClose() - ybar.getOpen()
            kp = (nbar.getOpen() - ybar.getClose()) / ybar.getClose()
            if solid < 0 and yx > 0 and kp > 0 and abs(solid) > 0.02 and (uline < 0.01 or dline < 0.01):
                yby = solid 
    
        mubei = "{:.4f}".format(mubei)
        yby   = "{:.4f}".format(yby)
        return (mubei, yby)

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

    def dtboard(self, dateTime, lb):
        ret = (0,)
        keydate = dateTime.strftime('%Y-%m-%d')
        inst    = self.__inst[2:]
        (code,indval) = self.__dt.getMatch(inst, keydate)
        if code is not None and indval['rate'] > 1.0 and \
                lb[0] < 2.0 and \
                lb[1] < 1.5 and lb[1] > 0 and \
                lb[2] < 1.2 and lb[2] > 0:
            ret = (1,)            
        return ret

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        bars = self.getValues()

        for i in self.__mawins:
            self.__maevents[i].onNewValue(dateTime, value.getClose())

        # Volume
        self.__mavol5.onNewValue(dateTime, value.getVolume())
        self.__mavol10.onNewValue(dateTime, value.getVolume())

        ma_dict = {}
        for i in self.__mawins:
            if self.__maevents[i].windowFull():
                ma_dict[i] = self.__maevents[i].getValue()
        self.__mas.append(ma_dict) 
        self.__vol.append(value.getVolume())

        self.__kline.onNewValue(dateTime, value)

        # collection MA features
        fts = self.MAfeature(bars, dateTime)
        self.__fts.extend(fts)

    def getMAscore(self):
        return self.__mascore

    def getMAdirect(self):
        return self.__madirect

    def getMAPosition(self):
        return self.__maposition

    def getValue(self):
        ret = self.__fts 
        self.__fts = []
        return (ret, self.__mas[-1])


class Indicator(technical.EventBasedFilter):
    def __init__(self, barDataSeries, windows=250, inst=None, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        assert isinstance(barDataSeries, bards.BarDataSeries), \
            "barDataSeries must be a dataseries.bards.BarDataSeries instance"
        technical.EventBasedFilter.__init__(self, barDataSeries, IndEventWindow(useAdjustedValues), maxLen)
###
