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
        self.__ctxt3 = -1
        self.__zyd   = -1
        self.__szx   = -1
        self.__kztm  = -1
        self.__wxx   = -1
        self.__xtsxy = -1
        self.__xtztf = -1
        self.__ugtc  = -1
        self.__bab   = -1

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

    # Up Gap Two Crows
    def UGTC(self, dateTime, values):
        ret = 0
        if self.__cl2 / self.__op2 >= 1.03 \
                and self.__op1 > self.__hi2 and self.__cl1 < self.__op1 \
                and self.__op0 > self.__op1 and self.__cl0 > self.__cl2 \
                and self.__cl0 < self.__cl1:
            ret = 1
        return ret

    # Bullish Abandoned Baby
    def BAB(self, dateTime, values):
        ret = 0
        if self.__cl2 / self.__op2 <= 0.98 \
                and self.CROSS(values[-2]) == 1 \
                and self.__op1 < self.__lw2 \
                and self.__op0 > self.__hi1 \
                and self.__cl0 / self.__op0 >= 1.02:
            ret = 1
        return ret

    # 捉腰带
    def BELT(self, dateTime, Bar):
        pass

    # 锤子线, Hammer
    #  1 --正锤子
    # -1 --倒锤子
    def HAMMER(self, dateTime, Bar):
        ret = 0
        op0  = Bar.getOpen()
        cl0  = Bar.getClose()
        lw0  = Bar.getLow()
        hi0  = Bar.getHigh()
        if hi0 == lw0:
            return ret

        dirt = 0
        diff = op0 - cl0
        fenm = cl0
        if (hi0 - op0) < (cl0 - lw0):
            cbin = (hi0 - op0) / op0
        else:
            cbin = (cl0 - lw0) / lw0
            dirt = 2

        if op0 < cl0:
            diff = cl0 - op0
            fenm = op0
            if (hi0 - cl0) < (op0 - lw0):
                cbin = (hi0 - cl0) / cl0
            else:
                cbin = (op0 - lw0) / lw0
                dirt = 2

        if diff / fenm < 0.015 and diff / fenm > 0.005 \
                and diff / (hi0 - lw0) < 0.318 and diff / (hi0 - lw0) > 0.1 \
                and cbin < 0.005:
            ret = 1 - dirt
        return ret

    # 十字星
    def CROSS(self, Bar):
        ret = 0
        op0  = Bar.getOpen()
        cl0  = Bar.getClose()
        lw0  = Bar.getLow()
        hi0  = Bar.getHigh()
        if hi0 == lw0:
            return ret

        diff = op0 - cl0
        fenm = cl0
        if op0 < cl0:
            diff = cl0 - op0
            fenm = op0
        if diff / (fenm + 0.0000001) < 0.005 and diff / (hi0 - lw0 + 0.000000001) < 0.1:
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

            day2 = values[-3]
            self.__op2  = day2.getOpen()
            self.__cl2  = day2.getClose()
            self.__hi2  = day2.getHigh()
            self.__lw2  = day2.getLow()
            day1 = values[-2]
            self.__op1  = day1.getOpen()
            self.__cl1  = day1.getClose()
            self.__hi1  = day1.getHigh()
            day0 = values[-1]
            self.__op0  = day0.getOpen()
            self.__cl0  = day0.getClose()

            self.tkdk(dateTime,jump, diefu, shying, xaying) 
            self.baodie(dateTime, diefu, zhenfu)
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
            self.__hamm  = self.HAMMER(dateTime, day0)
            print dateTime, '=======', self.__hamm

    def getValue(self):
        return (self.__tkdk, self.__tkdf, self.__bdie, \
                self.__ctxt, self.__zyd, self.__ctxt2, \
                self.__szx, self.__kztm, self.__ctxt3, \
                self.__wxx, self.__xtsxy, self.__xtztf, \
                self.__ugtc, self.__bab)
#
