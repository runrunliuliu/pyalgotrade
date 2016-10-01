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

    def goldSegment(self, dateTime, peek, valley):
        ret  = []
        g    = [1.0, 0.764, 0.618, 0.5, 0.382]
        diff = peek - valley
        # 回踩黄金分割位
        if self.__status == 20 or self.__status == 21:
            nlow = self.__nbar.getLow()
            ncls = self.__nbar.getClose()
            for i in g:
                fb = peek - diff * i
                rt = (nlow - fb) / fb
                if ncls > fb and abs(rt) < 0.005: 
                    ret.append(1) 
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
        
        timediff = self.__dtzq[vtime] - self.__dtzq[ptime]
        if (abs(timediff) >= 7 and (peek - valley) / valley >= 0.20) \
                or (abs(timediff) >= 11 and (peek - valley) / valley >= 0.10):
            gold = self.goldSegment(dateTime, peek, valley)
            return (sum(gold),)
        return ret
#
