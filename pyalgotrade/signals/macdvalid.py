import numpy as np


# macd有效信号判定，结合macd和sar指标
class MACDvalid(object):

    def __init__(self):
        self.__test = 0 

    # 转折点的Hist值不能远小于上一波升浪的开始值
    def HistRaTio(self, dateTime, nhist, inchist):
        ret = 1 
        if len(inchist[-1]) > 0:
            ratio = nhist[-1] / inchist[-1][0][1]
            if abs(ratio) < 0.9:
                ret = 0
        return ret
