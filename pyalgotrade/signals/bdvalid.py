import numpy as np


# 波段的有效性指标
class BDvalid(object):

    def __init__(self, direct, qshist, change, dtzq, value):

        self.__direct = direct 
        self.__qshist = qshist
        self.__change = change
        self.__dtzq   = dtzq
        self.__nbar   = value

        self.__status = -1 
        # 上升
        if self.__direct == -1 and qshist == 1:
            self.__status = 10
        # 上升调整
        if self.__direct == -1 and qshist == -1:
            self.__status = 11 
        # 下降
        if self.__direct == 1 and qshist == -1:
            self.__status = 20 
        # 下降反弹
        if self.__direct == 1 and qshist == 1:
            self.__status = 21

    def goldSegment(self, peek, valley):
        # 反弹
        ret  = []
        g    = [0.764, 0.618, 0.5, 0.382, 0.236]
        diff = peek - valley
        baseval = -1 
        flag    = 0
        if self.__status == 20:
            baseval = self.__nbar.getHigh()
            flag    = 1 
        if self.__status == 21:
            baseval = self.__nbar.getClose()
            flag    = -1 
        if baseval > 0: 
            for i in g:
                fb = peek - diff * i
                rt = (baseval - fb) / fb
                if rt > 0 and rt < 0.01: 
                    ret.append(flag) 
                else:
                    ret.append(0)
        else:
            ret = [0]
        return ret

    def period(self, dateTime, fpeek, fvalley):

        if self.__status == 10 or self.__status == 11:
            print dateTime, fpeek[0][0], fvalley[0][0]
            # timediff = self.__dtzq[vtime] - self.__dtzq[ptime]

    def bupStatus(self, dateTime, nowgd, fpeek, fvalley, datelow, datehigh):
        ret = None
        if len(fpeek) < 1 or len(fvalley) < 1:
            return ret 
        ptime = fpeek[0][0]
        vtime = fvalley[0][0]

        peek   = datehigh[ptime] 
        valley = datelow[vtime] 

        gold = self.goldSegment(peek, valley)
        return (sum(gold),)
#
