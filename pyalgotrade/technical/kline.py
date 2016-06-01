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

            # 相比昨日
            last = values[-2].getClose()
            if values[-2].getClose() > values[-2].getOpen():
                last = values[-2].getOpen()
            jump = ((values[-1].getOpen() - last) / last)

            diefu = (values[-1].getClose() - values[-2].getClose()) / values[-2].getClose()

            if jump < -0.02 and diefu < 0.0:
                self.__tkdk = jump 
            else:
                self.__tkdk = 1024 

            if jump < -0.005 and shying < 0.05 and xaying < 0.05 and diefu < -0.015:
                self.__tkdk = jump
                self.__tkdf = diefu

    def getValue(self):
        return (self.__tkdk, self.__tkdf) 
