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
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""
import pprint
from collections import OrderedDict
import numpy as np
from pyalgotrade import technical
from pyalgotrade import dataseries
from pyalgotrade.utils import collections


class KLineEventWindow(technical.EventWindow):
    def __init__(self, period):
        assert(period > 1)
        technical.EventWindow.__init__(self, period, dtype=object)
        self.__value = None

        # 跳空低开
        # 跳空幅度比较大 > 0.02
        # or 跳空幅度> 0.005, 相比昨日跌幅比较大 > 0.015，光头阴线，几乎没有上下影
        self.__tkdk = 1024
        self.__tkdf = 1024
        self.__bdie = 1024
        self.__ctxt  = -1
        self.__ctxt2 = -1
        self.__ctxt3 = -1
        self.__zyd   = -1
        self.__szx   = -1
        self.__kztm  = -1
        self.__wxx   = -1
        self.__xtsxy = -1
        self.__xtztf = -1
        self.__ugtc  = -1
        self.__bab   = -1
        # GAPS跳空缺口
        self.__gaps = []
        self.__gapindex = 0
        self.__ngap_list = collections.ListDeque(10)

        self.__candles = []
        self.__cdlist  = collections.ListDeque(20)
        self.__dtzq    = OrderedDict()
        self.__zq      = 0

        self.__tphp   = None

    def setParameters(self, tmpars):
        self.__sharePars = tmpars 

    def baodie(self, dateTime, diefu, zhenfu):
        mins = diefu
        if diefu > zhenfu:
            mins = zhenfu
        if mins < -0.04:
            self.__bdie = 1
        else:
            self.__bdie = 1024

    # 跳空低开
    def tkdk(self, dateTime, jump, diefu, shying, xaying):
        if jump < -0.02 and diefu < 0.0:
            self.__tkdk = jump
        else:
            self.__tkdk = 1024
        if jump < -0.005 and shying < 0.08 and xaying < 0.05 and diefu < -0.015:
            self.__tkdk = jump
            self.__tkdf = diefu

    # Define IN QuChaoGu Corp.
    def xtZTF(self, dateTime, values):
        flag = -1
        if len(values) < 2:
            return flag
        nbar = values[-1]
        ybar = values[-2]
       
        cl1 = ybar.getClose()
        cl0 = nbar.getClose()

        diff = (cl0 - cl1) / cl1
        # 1. 微涨：0<P≤0.4%
        if diff > 0 and diff <= 0.004:
            flag = 1
        # 2. 中阳：0.4<P≤1%
        if diff > 0.004 and diff <= 0.01:
            flag = 2
        # 3. 大涨：P>1%
        if diff > 0.01:
            flag = 3
        # 4. 微跌：-0.4%≤P<0%
        if diff >= -0.004 and diff < 0.0:
            flag = 4
        # 5. 中阴：-1%≤P<-0.4%
        if diff >= -0.01 and diff < -0.004:
            flag = 5
        # 6. 大跌：P < -1%
        if diff < -0.01:
            flag = 6
        # 7. 无涨跌：0%
        if diff == 0.0:
            flag = 7
        return flag
        
    # Define IN QuChaoGu Crop.
    def xtSXY(self, dateTime, values):
        flag = -1
        nbar = values[-1]
        
        op = nbar.getOpen()
        hi = nbar.getHigh()
        lw = nbar.getLow()
        cl = nbar.getClose()

        up = op
        dn = cl
        if cl > op:
            up = cl
            dn = op
        # 1. 长上影线：上影线价格区间/实体线价格区间≥2
        if (hi - up) / (up - dn + 0.00001) >= 2.0:
            flag = 1
        # 2. 中上影线：1≤上影线价格区间/实体线价格区间<2
        if (hi - up) / (up - dn + 0.00001) < 2.0 and (hi - up) / (up - dn + 0.00001) >= 1.0:
            flag = 2
        # 3. 短上影线：0≤上影线价格区间/实体线价格区间<1
        if (hi - up) / (up - dn + 0.00001) < 1.0 and (hi - up) / (up - dn + 0.00001) >= 0.0:
            flag = 3
        # 4. 长下影线：下影线价格区间/实体线价格区间≥2
        if (dn - lw) / (up - dn + 0.00001) >= 2.0:
            flag = 4
        # 5. 中下影线：1≤下影线价格区间/实体线价格区间<2
        if (dn - lw) / (up - dn + 0.00001) < 2.0 and (dn - lw) / (up - dn + 0.00001) >= 1.0:
            flag = 5
        # 6. 短下影线：0≤下影线价格区间/实体线价格区间<1
        if (dn - lw) / (up - dn + 0.00001) < 1.0 and (dn - lw) / (up - dn + 0.00001) >= 0.0:
            flag = 6
        
        return flag

    # 刺透
    def CTXT(self, dateTime, values):
        ret = 0
        day1 = values[-2]
        op1 = day1.getOpen()
        cl1 = day1.getClose()
        lw1 = day1.getLow()

        nday = values[-1]
        op0 = nday.getOpen()
        cl0 = nday.getClose()

        if op1 > cl1 and cl0 > (op1 + cl1) * 0.5 \
                and op0 < lw1 and op1 / cl1 >= 1.02 \
                and cl0 > op0 and cl0 < op1:
            ret = 1
        return ret

    # 刺透2
    def CTXT2(self, dateTime, values):
        ret = 0
        day1 = values[-2]
        op1 = day1.getOpen()
        cl1 = day1.getClose()
        lw1 = day1.getLow()

        nday = values[-1]
        op0 = nday.getOpen()
        cl0 = nday.getClose()
        hi0 = nday.getHigh()

        if op1 > cl1 and hi0 > (op1 + cl1) * 0.5 \
                and op0 < lw1 and op1 / cl1 >= 1.02 \
                and cl0 > op0 and cl0 < op1 and cl0 > cl1:
            ret = 1
        return ret
 
    # 刺透3
    def CTXT3(self, dateTime, values):
        ret = 0
        day1 = values[-2]
        op1 = day1.getOpen()
        cl1 = day1.getClose()
        lw1 = day1.getLow()

        nday = values[-1]
        op0 = nday.getOpen()
        cl0 = nday.getClose()
        lw0 = nday.getLow()

        if op1 > cl1 and cl0 > (op1 + cl1) * 0.5 \
                and op0 < cl1 and op1 / cl1 >= 1.02 \
                and cl0 > op0 and cl0 < op1 and cl0 > cl1 \
                and lw0 >= lw1:
            ret = 1
        return ret
   
    # 前阴捉腰带
    def ZYD(self, dateTime, values):
        ret = 0
        day1 = values[-2]
        op1 = day1.getOpen()
        cl1 = day1.getClose()

        nday = values[-1]
        op0  = nday.getOpen()
        cl0  = nday.getClose()
        lw0  = nday.getLow()

        if op0 / lw0 < 1.001 and cl0 / op0 > 1.03 and cl0 / op0 <= 1.08 \
                and op1 > cl1:
            ret = 1
        return ret

    # 看涨吞没形态
    def KZTM(self, dateTime, values):
        ret = 0
        day1 = values[-2]
        op1 = day1.getOpen()
        cl1 = day1.getClose()
        vol1 = day1.getVolume()

        nday = values[-1]
        op0 = nday.getOpen()
        cl0 = nday.getClose()
        vol0 = nday.getVolume()

        if vol0 / (vol1 + 0.00000001) > 1.0 and op1 > cl1 \
                and op0 < cl1 and op1 / cl1 <= 1.02 \
                and cl0 > op0 and cl0 > op1:
            ret = 1
        return ret

    # 十字星
    def SZX(self, dateTime, values):
        ret = 0
        day1 = values[-2]
        vol1 = day1.getVolume()

        nday = values[-1]
        vol0 = nday.getVolume()
        op0  = nday.getOpen()
        cl0  = nday.getClose()
        lw0  = nday.getLow()
        hi0  = nday.getHigh()

        diff = op0 - cl0
        fenm = cl0
        if op0 < cl0:
            diff = cl0 - op0
            fenm = op0

        if hi0 == lw0:
            return ret

        if vol0 / (vol1 + 0.00000001)  < 1.10 and diff / (fenm + 0.0000001) < 0.005 and diff / (hi0 - lw0 + 0.000000001) < 0.1:
            ret = 1
        return ret

    # 挽袖线形态
    def WXX(self, dateTime, values):
        ret = 0
        day1 = values[-2]
        op1 = day1.getOpen()
        cl1 = day1.getClose()
        hi1 = day1.getHigh()
        vol1 = day1.getVolume()

        nday = values[-1]
        op0 = nday.getOpen()
        cl0 = nday.getClose()
        vol0 = nday.getVolume()

        if vol0 / (vol1 + 0.0000000001) > 1.0 and op1 > cl1 \
                and op0 > cl1 and op1 / cl1 >= 1.02 \
                and cl0 > hi1 and cl0 > op0:
            ret = 1
        return ret

    # 向上跳空两只乌鸦
    def UGTC(self, dateTime, values):
        ret = {} 
        if self.__cl2 / self.__op2 >= 1.03 \
                and self.__op1 > self.__hi2 and self.__cl1 < self.__op1 \
                and self.__op0 > self.__op1 and self.__cl0 > self.__cl2 \
                and self.__cl0 < self.__cl1:
            ret['drt'] = 1
            ret['nm']  = 'ugtc'
        return ret

    # 牛市弃婴
    def BAB(self, dateTime, values):
        ret = 0
        cross = self.CROSS(dateTime, values[-2])
        if self.__cl2 / self.__op2 <= 0.98 \
                and len(cross) > 0 and cross['drt'] == 1 \
                and self.__op1 < self.__lw2 \
                and self.__op0 > self.__hi1 \
                and self.__cl0 / self.__op0 >= 1.02:
            ret = 1
        return ret

    # 岛形反转
    def IslandReverse(self, dateTime):
        ret = {}
        af = self.__ngap['p1']
        ng = self.__ngap['n']
        tk = -1; fz = -1; zq = -1; drt = 0
        if len(af) > 0 and len(ng) > 0: 
            for g in af:
                if g['d'] < 0 and ng['d'] > 0 and ng['lev1'] >= g['lev1']:
                    drt = 1
                if g['d'] > 0 and ng['d'] < 0 and ng['lev1'] < g['lev1']:
                    drt = -1
                if drt != 0:
                    tk = abs(ng['s'] / (g['s'] + 0.0000001))
                    fz = (ng['lev1'] - g['lev1']) / (g['lev1'] + 0.0000001)
                    zq = self.__dtzq[ng['day']] - self.__dtzq[g['day']]
                    ret['pday'] = g['day'].strftime(self.__sharePars[1])
                    ret['tk']   = float("{:.2f}".format(tk))
                    ret['fz']   = float("{:.2f}".format(fz))
                    ret['drt']  = drt
                    ret['zq']   = zq
                    ret['nm']   = 'ir'
                    self.__candles.append(ret)
                    break
        return ret

    # 吞没形态
    def Engulfed(self, dateTime, values):
        drt = 0
        ret = {}
        if max((self.__op0, self.__cl0)) > self.__hi1 and \
                min((self.__op0, self.__cl0)) < self.__lw1:
            if self.__op0 > self.__cl0 \
                    and self.__op1 < self.__cl1:
                drt = -1
            if self.__op0 < self.__cl0 \
                    and self.__op1 > self.__cl1:
                drt = 1
            if drt != 0:
                ret['drt'] = drt
                ret['nm']  = 'engulfed'
                self.__candles.append(ret)
        return ret

    # 刺透形态
    def Piercing(self, dateTime, values):
        ret = {} 
        drt = 0
        if self.__op1 > self.__cl1 and \
                self.__cl0 > self.__op0 and \
                self.__op1 / self.__cl1 >= 1.02:
            if self.__cl0 > (self.__op1 + self.__cl1) * 0.5 \
                    and self.__op0 < self.__lw1 \
                    and self.__cl0 < self.__op1:
                drt = 1
            if self.__hi0 > (self.__op1 + self.__cl1) * 0.5 \
                    and self.__cl0 < self.__op1 \
                    and self.__op0 < self.__lw1 \
                    and self.__cl0 > self.__cl1:
                drt = 2
            if self.__cl0 > (self.__op1 + self.__cl1) * 0.5 \
                    and self.__op0 < self.__cl1 \
                    and self.__lw0 >= self.__lw1 \
                    and self.__cl0 > self.__cl1 \
                    and self.__cl0 < self.__op1:
                drt = 3
        if drt != 0:
            ret['drt'] = drt 
            ret['nm']  = 'piercing'
            self.__candles.append(ret)
        return ret

    # 爆阳横盘
    def TPHP(self, dateTime, values):
        ret    = {}
        update = 0
        nbar   = self.BarStatus(values[-1])
        neibor = self.NeighborBarStatus(values[-1], values[-2])
        if nbar is not None and nbar[0] > 0.08 and nbar[1] > 0.8 \
                and neibor[1] > 0.09 and neibor[3] > 2.0:
            self.__tphp = (dateTime, values[-1])
            update = 1

        # 第一次更新过滤
        if update == 1:
            return ret

        if update == 0 and self.__tphp is not None:
            flag = 1
            zq = self.__dtzq[dateTime] - self.__dtzq[self.__tphp[0]]
            if zq > 15:
                flag = 0
            if values[-1].getVolume() / self.__tphp[1].getVolume() > 1.0:
                flag = 0
            if values[-1].getClose() / self.__tphp[1].getClose() > 1.05:
                flag = 0
            if values[-1].getClose() / self.__tphp[1].getClose() < 0.95:
                flag = 0
            # 突破横盘状态中
            if flag == 1:
                ret['zq'] = zq
                ret['nm'] = 'tphp'
                self.__candles.append(ret)
            # 突破无效
            if flag == 0:
                self.__tphp = None

    # 获取最近的一个缺口
    def LastGAP(self, dateTime, values):
        ret = {}
        if len(self.__gaps) > 0:
            lev1 = self.__gaps[-1][1][2]
            lev2 = self.__gaps[-1][1][3]
            ret['nm']   = 'lastgap'
            ret['l1'] = lev1
            ret['l2'] = lev2
            ret['dt'] = self.__gaps[-1][0].strftime(self.__sharePars[1])
            self.__candles.append(ret)
        return ret

    # 跳空缺口形态
    def JumpGAP(self, dateTime, values):
        ret = {}
        drt = 0
        if len(self.__ngap_list) > 1:

            # 跳空阴阳线
            p1gap = self.__ngap_list[-2]
            if len(p1gap['n']) > 0 \
                    and self.__cl1 / values[-3].getClose() >= 1.03 \
                    and self.__cl1 > self.__op1 \
                    and self.__cl0 < self.__op0 \
                    and (self.__cl1 / self.__op1) - (self.__op0 / self.__cl0) < 0.01 \
                    and self.__lw0 > p1gap['n']['lev2'] \
                    and p1gap['n']['d'] > 0:
                drt = 1

            # 向上跳空缺口
            if len(self.__ngap['n']) > 0 and self.__ngap['n']['d'] > 0:
                drt = 2

            if drt != 0:
                ret['drt'] = drt
                ret['nm']  = 'jumpgap'
                self.__candles.append(ret)
        return ret

    # 连续一字板打开
    def YZB(self, dateTime, values):
        ret  = {}
        bar1 = values[-2]
        bar0 = values[-1]

        op1 = bar1.getOpen()
        hi1 = bar1.getHigh()
        lw1 = bar1.getLow()
        cl1 = bar1.getClose()

        op0 = bar0.getOpen()
        hi0 = bar0.getHigh()
        lw0 = bar0.getLow()
        cl0 = bar0.getClose()

        if op1 == cl1 and op1 == hi1 and op1 == lw1 \
                and op0 == hi0 and op0 == cl0 and op0 > lw0:
            ret['nm']  = 'yzbk'
            ret['drt'] = 1
            print dateTime, ret

    # 孕线形态
    def Pregnant(self, dateTime, values):
        ret = {}
        drt = 0
        if max((self.__op1, self.__cl1)) > self.__hi0 and \
                min((self.__op1, self.__cl1)) < self.__lw0:
            if self.__op0 > self.__cl0 \
                    and self.__op1 < self.__cl1:
                drt = -1
            if self.__op0 < self.__cl0 \
                    and self.__op1 > self.__cl1:
                drt = 1
            if drt != 0:
                ret['drt'] = drt
                ret['nm']  = 'pregnant'
                self.__candles.append(ret)
        return ret

    # N字形
    def NZX(self, dateTime, values):
        ret = {}
        d4cl = values[-4].getClose()
        d4vl = values[-4].getVolume()

        d3op = values[-3].getOpen()
        d3cl = values[-3].getClose()
        d3vl = values[-3].getVolume()
        d3st = self.BarStatus(values[-3])
        if d3st is None:
            return ret
        d3sy = d3st[4]
        d3rb = d3st[0]

        d2cl = values[-2].getClose()
        d2op = values[-2].getOpen()
        d2vl = values[-2].getVolume()
        d2st = self.BarStatus(values[-2])
        if d2st is None:
            return ret
        d2rb = d2st[0]
        
        d1cl = values[-1].getClose()
        d1op = values[-1].getOpen()
        d1vl = values[-1].getVolume()
        d1st = self.BarStatus(values[-1])
        if d1st is None:
            return ret
        d1rb = d1st[0]

        if d3vl / (0.000001 + d4vl) > 1.5 and d3cl / d4cl > 1.06 \
                and d3rb > 0.05 and d3sy < 0.005 and d3cl > d3op \
                and d2rb > 0.02 and d2cl < d2op and d2cl < d3cl \
                and d2cl > (d3cl / 4 + 3 * d3op / 4) \
                and d1rb > 0.01 and d1cl < d1op and d1cl < d2cl \
                and d1cl > (d3cl / 8 + 7 * d3op / 8) \
                and d1vl / (0.0000001 + d2vl) < 0.8 and d1vl / (0.0000001 + d3vl) <= 0.5:
            ret['nm']  = 'NZX'
            ret['drt'] = 1
            self.__candles.append(ret)

    # 捉腰带
    def BELT(self, dateTime, Bar):
        ret = {} 
        bars = self.BarStatus(Bar)
        if bars is None:
            return ret
        rb = bars[0]
        ts = bars[2]
        di = bars[3]
        if rb >= 0.03 and ts < 0.002:
            ret['drt'] = 1 - di
            ret['nm']  = 'belt'
            self.__candles.append(ret)
        return ret

    # 锤子线, Hammer
    #  1 --正锤子
    # -1 --倒锤子
    def HAMMER(self, dateTime, Bar):
        ret = {}
        bars = self.BarStatus(Bar)
        if bars is None:
            return ret
        rb = bars[0]
        bs = bars[1]
        ts = bars[2]
        di = bars[3]
        if rb < 0.02 and rb > 0.005 and \
                bs < 0.318 and bs > 0.1 and ts < 0.002:
            ret['drt'] = 1 - di
            ret['nm']  = 'hammer'
            self.__candles.append(ret)
        return ret

    # 十字星
    def CROSS(self, dateTime, Bar):
        ret = {}
        bars = self.BarStatus(Bar)
        if bars is None:
            return ret
        rb = bars[0]
        bs = bars[1]
        if rb < 0.005 and bs < 0.1:
            ret['drt'] = 1
            ret['nm']  = 'cross'
            self.__candles.append(ret)
        return ret

    # 单个Bar的状态
    def BarStatus(self, Bar):
        op0  = Bar.getOpen()
        cl0  = Bar.getClose()
        lw0  = Bar.getLow()
        hi0  = Bar.getHigh()
        if hi0 == lw0:
            return None
        dirt  = 0
        diff  = op0 - cl0
        fenm  = cl0
        shying = (hi0 - op0) / op0
        sysize = hi0 - op0

        xaying = (cl0 - lw0) / lw0
        xysize = cl0 - lw0

        if (hi0 - op0) < (cl0 - lw0):
            cbin = shying
        else:
            cbin = xaying
            dirt = 2

        if op0 < cl0:
            diff = cl0 - op0
            fenm = op0
            shying = (hi0 - cl0) / cl0
            sysize = hi0 - cl0

            xaying = (op0 - lw0) / lw0
            xysize = op0 - lw0

            if (hi0 - cl0) < (op0 - lw0):
                cbin = shying
            else:
                cbin = xaying
                dirt = 2
        realbody = diff / fenm
        bodysize = diff / (hi0 - lw0)
        tailsize = cbin
        direct   = dirt
        sysize   = sysize / (hi0 - lw0)
        xysize   = xysize / (hi0 - lw0)

        return (realbody, bodysize, tailsize, \
                direct, shying, xaying, \
                sysize, xysize)

    # 相邻的BARS状态
    def NeighborBarStatus(self, day0, day1):
        op0 = day0.getOpen()
        hi0 = day0.getHigh()
        lw0 = day0.getLow()
        cl0 = day0.getClose()

        op1 = day1.getOpen()
        hi1 = day1.getHigh()
        lw1 = day1.getLow()
        cl1 = day1.getClose()

        lb  = day0.getVolume() / (0.0000000001 + day1.getVolume())

        # T-1日阴阳
        last = cl1
        if cl1 > op1:
            last = op1
        jump  = (op0 - last) / last
        diefu = (cl0 - cl1) / cl1

        # T日周期
        up = cl0
        dn = op0
        if cl0 < op0:
            up = op0
            dn = cl0

        # 上下缺口定义, 1向上跳空, -1向下跳空
        gap = None
        if lw0 > hi1:
            self.__gapindex = self.__gapindex + 1
            gap = ((lw0 - hi1) / hi1, (dn - hi1) / hi1, lw0, hi1, 1, 0, self.__gapindex, lw0, hi1)
        if hi0 < lw1:
            self.__gapindex = self.__gapindex + 1
            gap = ((hi0 - lw1) / lw1, (up - lw1) / lw1, hi0, lw1, -1, 0, self.__gapindex, hi0, lw1)

        return (jump, diefu, gap, lb)

    # 加入GAP进入GAP列表, Remove填平的GAPs
    # attr表示缺口与前邻关系，abs(attr)表示同方向个数
    def add2GAP(self, dateTime, gap, values):
        out  = {}
        nbar = values[-1]
        lw0 = nbar.getLow(); hi0 = nbar.getHigh()
        filled = []; filling = None; tgap = []
        for g in self.__gaps:
            if g[1][4] > 0:
                if lw0 <= g[1][3]:
                    filled.append(g)
                    continue
                if lw0 > g[1][3] and lw0 < g[1][2]:
                    newg = (g[0], (g[1][0], g[1][1], lw0, g[1][3], \
                                   g[1][4], g[1][5] + 1, g[1][6], \
                                   g[1][7], g[1][8]))
                    g    = newg
                    filling = g 
            if g[1][4] < 0:
                if hi0 >= g[1][3]:
                    filled.append(g)
                    continue
                if hi0 < g[1][3] and hi0 > g[1][2]:
                    newg = (g[0], (g[1][0], g[1][1], hi0, g[1][3], \
                                   g[1][4], g[1][5] + 1, g[1][6], \
                                   g[1][7], g[1][8]))
                    g    = newg
                    filling = g
            tgap.append(g)
        self.__gaps = tgap

        (af, df) = self.gapStats(dateTime, filled, filling, gap)
        # add GAP
        ngap = {}
        if gap is not None:
            ng = self.gapNeighbor(dateTime, gap)
            if ng[0] is not None:
                gap = ng[0]
            self.__gaps.append((dateTime, gap))
            ngap = ng[1]
        out['n']  = ngap
        out['p1'] = af
        out['p2'] = df
        return out

    # 统计GAP的特征及相邻特征
    def gapNeighbor(self, dateTime, g):
        newg = g 
        zhuq = -1
        ngap = {}
        if len(self.__gaps) > 0:
            pgap = self.__gaps[-1]
            if g[6] == (pgap[1][6] + 1):
                if g[4] * pgap[1][4] > 0:
                    flag = 1
                    if g[4] < 0:
                        flag = -1
                    newg = (g[0], g[1], g[2], g[3], g[4] + flag, g[5], g[6], g[7], g[8])
                    zhuq = self.__dtzq[dateTime] - self.__dtzq[pgap[0]]
        ngap['d']  = newg[4]
        ngap['s']  = float("{:.2f}".format(newg[0] * 100))
        ngap['hb'] = float("{:.2f}".format((newg[1] - newg[0]) / newg[0]))
        ngap['zq'] = zhuq 
        ngap['day'] = dateTime
        ngap['lev1'] = newg[7]
        ngap['lev2'] = newg[8]
        return (newg, ngap)

    # 统计GAP的填补特征, 特殊返回是否存在岛形翻转
    def gapStats(self, dateTime, filled, filling, gap):
        af = []
        df = {} 
        if len(filled) > 0:
            for f in filled:
                g = {}
                g['d']    = f[1][4]
                g['s']    = float("{:.2f}".format(f[1][0] * 100))
                g['zq']   = self.__dtzq[dateTime] - self.__dtzq[f[0]] 
                g['day']  = f[0]
                g['hfq']  = f[1][5]
                g['lev1'] = f[1][7]
                g['lev2'] = f[1][8]
                af.append(g)
        if filling is not None:
            df['d']   = filling[1][4]
            df['s']   = float("{:.2f}".format(filling[1][0] * 100))
            df['zq']  = self.__dtzq[dateTime] - self.__dtzq[filling[0]] 
            df['day'] = filling[0]
            df['hfq'] = filling[1][5]
            df['lev1'] = filling[1][7]
            df['lev2'] = filling[1][8]
        return (af, df)

    # 初始化计算共用变量
    def Init(self, values):
        day2 = values[-3]
        self.__op2  = day2.getOpen()
        self.__cl2  = day2.getClose()
        self.__hi2  = day2.getHigh()
        self.__lw2  = day2.getLow()
        day1 = values[-2]
        self.__op1  = day1.getOpen()
        self.__cl1  = day1.getClose()
        self.__hi1  = day1.getHigh()
        self.__lw1  = day1.getLow()
        day0 = values[-1]
        self.__op0  = day0.getOpen()
        self.__cl0  = day0.getClose()
        self.__hi0  = day0.getHigh()
        self.__lw0  = day0.getLow()

        # 当日K线形态
        bars = self.BarStatus(day0)
        if bars is None:
            shying = 0
            xaying = 0
            zhenfu = 0
        else:
            zhenfu = bars[0]
            shying = bars[4]
            xaying = bars[5]
        # 相邻K线状态
        (jump, diefu, gap, lb) = self.NeighborBarStatus(day0, day1)
        return (jump, diefu, shying, xaying, zhenfu, gap)

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)

        self.__zq = self.__zq + 1
        self.__dtzq[dateTime] = self.__zq

        if value is not None and self.windowFull():
            self.__tkdk = 1024
            self.__tkdf = 1024
            self.__candles = []
            values = self.getValues()
            (jump, diefu, shying, xaying, zhenfu, gap) = self.Init(values)

            self.tkdk(dateTime, jump, diefu, shying, xaying)
            self.baodie(dateTime, diefu, zhenfu)

            # add GAP to GAPs, REMOVE FILLED GAPs
            self.__ngap = self.add2GAP(dateTime, gap, values)
            self.__ngap_list.append(self.__ngap)

            self.__ctxt  = self.CTXT(dateTime, values)
            self.__zyd   = self.ZYD(dateTime, values)
            self.__ctxt2 = self.CTXT2(dateTime, values)
            self.__szx   = self.SZX(dateTime, values)
            self.__kztm  = self.KZTM(dateTime, values)
            self.__ctxt3 = self.CTXT3(dateTime, values)
            self.__wxx   = self.WXX(dateTime, values)
            self.__xtsxy = self.xtSXY(dateTime, values)
            self.__xtztf = self.xtZTF(dateTime, values)
            self.__ugtc  = self.UGTC(dateTime, values)
            self.__bab   = self.BAB(dateTime, values)
            self.__hamm  = self.HAMMER(dateTime, values[-1])
            self.__cross = self.CROSS(dateTime, values[-1])
            self.__belt  = self.BELT(dateTime, values[-1])
            self.__efed  = self.Engulfed(dateTime, values)
            self.__pgant = self.Pregnant(dateTime, values)
            self.__island  = self.IslandReverse(dateTime)
            self.__pierce  = self.Piercing(dateTime, values)
            self.__jump    = self.JumpGAP(dateTime, values)
            self.__nxz     = self.NZX(dateTime, values)
            self.__yzbk    = self.YZB(dateTime, values)
            self.__lastgap = self.LastGAP(dateTime, values)
            
            self.TPHP(dateTime, values)

            self.__cdlist.append((dateTime, self.__candles))

    def getValue(self):
        return (self.__tkdk, self.__tkdf, self.__bdie, \
                self.__ctxt, self.__zyd, self.__ctxt2, \
                self.__szx, self.__kztm, self.__ctxt3, \
                self.__wxx, self.__xtsxy, self.__xtztf, \
                self.__cdlist)
#
