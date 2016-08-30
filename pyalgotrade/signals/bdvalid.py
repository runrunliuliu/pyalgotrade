import numpy as np


# 波段的有效性指标
class BDvalid(object):

    def __init__(self, direct, qshist, change, dtzq):

        self.__direct = direct 
        self.__qshist = qshist
        self.__change = change
        self.__dtzq   = dtzq

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

    def goldSegment(self, peek, valley, direct):
        # 反弹
        ret = []
        g = [0.809, 0.618, 0.5, 0.382, 0.236]
        if direct == 1:
            diff = peek - valley
            for i in g:
                ret.append(valley + diff * i) 
        return ret

    def bupStatus(self, dateTime, nowgd, fpeek, fvalley, datelow, datehigh):
        ret = None
        if len(fpeek) < 1 or len(fvalley) < 1:
            return ret 
        ptime = fpeek[0][0]
        vtime = fvalley[0][0]

        peek   = datehigh[ptime] 
        valley = datelow[vtime] 

        # gold = self.goldSegment(peek, valley, 1)
        timediff = self.__dtzq[vtime] - self.__dtzq[ptime]
        # print dateTime, vtime, ptime, timediff 

#
