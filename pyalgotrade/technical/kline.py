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

import numpy as np
from pyalgotrade import technical
from pyalgotrade import dataseries


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
        self.__zyd   = -1
        self.__szx   = -1
        self.__kztm  = -1

    def baodie(self, dateTime, diefu, zhenfu):
        mins = diefu
        if diefu > zhenfu:
            mins = zhenfu 
        if mins < -0.04:
            self.__bdie = 1
        else:
            self.__bdie = 1024

    def tkdk(self, dateTime, jump, diefu, shying, xaying):
        if jump < -0.02 and diefu < 0.0:
            self.__tkdk = jump 
        else:
            self.__tkdk = 1024 
        if jump < -0.005 and shying < 0.08 and xaying < 0.05 and diefu < -0.015:
            self.__tkdk = jump
            self.__tkdf = diefu

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
    
    # 卓腰带
    def ZYD(self, dateTime, values):
        ret = 0
        nday = values[-1]
        op0  = nday.getOpen()
        cl0  = nday.getClose()
        lw0  = nday.getLow()

        if op0 / lw0 < 1.001 and cl0 / op0 > 1.03 and cl0 / op0 <= 1.08: 
            ret = 1
        return ret

    # 看涨吞没形态 
    def KZTM(self, dateTime, values):
        ret = 0
        day1 = values[-2]
        op1 = day1.getOpen()
        cl1 = day1.getClose()
        lw1 = day1.getLow()
        hi1 = day1.getHigh()
        vol1 = day1.getVolume()

        nday = values[-1]
        op0 = nday.getOpen()
        cl0 = nday.getClose()
        hi0 = nday.getHigh()
        vol0 = nday.getVolume()

        if vol0 / vol1 > 0.99 and op1 > cl1 and hi0 > hi1 \
                and op0 < lw1 and op1 / cl1 >= 1.02 \
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

        if vol0 / vol1  < 1.10 and diff / fenm < 0.005 and diff / (hi0 - lw0) < 0.1:
            ret = 1
        return ret

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        if value is not None and self.windowFull():
            self.__tkdk = 1024 
            self.__tkdf = 1024 

            values = self.getValues()
            # 当日K线形态
            nop = values[-1].getOpen()
            ncl = values[-1].getClose() 
            nhi = values[-1].getHigh() 
            nlw = values[-1].getLow() 
            up = nop
            dn = ncl
            if ncl > nop:
                up = ncl
                dn = nop
            shying = (nhi - up) / (nhi - nlw + 0.00000001) 
            xaying = (dn - nlw) / (nhi - nlw + 0.00000001)
            zhenfu = (ncl - nop) / (nop + 0.000000001)
            # 相比昨日
            last = values[-2].getClose()
            if values[-2].getClose() > values[-2].getOpen():
                last = values[-2].getOpen()
            jump = ((values[-1].getOpen() - last) / last)
            diefu = (values[-1].getClose() - values[-2].getClose()) / values[-2].getClose()

            self.tkdk(dateTime,jump, diefu, shying, xaying) 
            self.baodie(dateTime, diefu, zhenfu)
            self.__ctxt  = self.CTXT(dateTime, values)
            self.__zyd   = self.ZYD(dateTime, values)
            self.__ctxt2 = self.CTXT2(dateTime, values)
            self.__szx   = self.SZX(dateTime, values)
            self.__kztm  = self.KZTM(dateTime, values)

    def getValue(self):
        return (self.__tkdk, self.__tkdf, self.__bdie, \
                self.__ctxt, self.__zyd, self.__ctxt2, \
                self.__szx, self.__kztm) 
