import numpy as np
import logging
import logging.config


# 波段的有效性指标
class BDvalid(object):

    def __init__(self, direct, qshist, change, dtzq, value, inst):

        self.__logger = logging.getLogger('BDvalid')

        self.__inst   = inst
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

    def longGoldSegment(self, dateTime, peek, valley):
        ret   = []
        g     = [1.0, 0.764, 0.618, 0.5, 0.382]
        fbp   = 1024
        gprice = []
        press  = [] 
        diff   = peek - valley
        # 回踩黄金分割位
        if self.__status == 20 or self.__status == 21:
            nlow = self.__nbar.getLow()
            nhi  = self.__nbar.getHigh()
            ncls = self.__nbar.getClose()
            cnt  = 0
            for i in g:
                cnt = cnt + 1
                fb = peek - diff * i
                rt = (nlow - fb) / fb
                if ncls > fb and abs(rt) < 0.005: 
                    fbp = fb
                    ret.append(1) 
                else:
                    ret.append(0)
                if nhi > fb and ncls < fb:
                    press.append(cnt)
                gprice.append(fb)
        else:
            ret = [0]
        return (ret, fbp, press, gprice)

    def shortGoldSegment(self, dateTime, peek, valley):
        ret  = []
        g    = [1.0, 0.764, 0.618, 0.5, 0.382, 0.236]
        diff = peek - valley
        # 上冲黄金分割位
        nhi  = self.__nbar.getHigh()
        ncls = self.__nbar.getClose()
        price = -1024
        for i in g:
            fb = valley + diff * i
            rt = (nhi - fb) / fb
            if ncls < fb and abs(rt) < 0.02: 
                ret.append(1) 
                price = fb
            else:
                ret.append(0)
        return (ret, price)

    def period(self, dateTime, fpeek, fvalley):
        if self.__status == 10 or self.__status == 11:
            print dateTime, fpeek[0][0], fvalley[0][0]
            # timediff = self.__dtzq[vtime] - self.__dtzq[ptime]

    # 前峰受阻
    def peekZL(self, dateTime, peek):
        ret = 0
        nhi = self.__nbar.getHigh()
        ncl = self.__nbar.getClose()
        if nhi > peek and ncl < peek:
            ret = 1
        return ret

    # M-Head
    def MHead(self, dateTime, peek, valley, high):
        MLINE = 1024 
        ret   = [] 
        if self.__status == 10 or self.__status == 11:
            for i in range(0, len(peek)):
                if len(ret) == 2:
                    break
                ptime = peek[i][0]
                if (i + 1) >= len(valley):
                    return MLINE 

                vtime = valley[i+1][0]
                timediff = self.__dtzq[ptime] - self.__dtzq[vtime]
                if (timediff + 1) >= 5:
                    ret.append((ptime,high[ptime]))
        if len(ret) == 2:
            if abs((ret[0][1] - ret[1][1]) / ret[1][1]) < 0.005:
                MLINE = ret[0][1]
                self.__logger.log(logging.ERROR, 'M_HEAD: %s %s %f', dateTime, self.__inst, MLINE)
        return MLINE

    def bupStatus(self, dateTime, nowgd, fpeek, fvalley, datelow, datehigh):
        ret = None
        if len(fpeek) < 1 or len(fvalley) < 1:
            return ret 
        ptime = fpeek[0][0]
        vtime = fvalley[0][0]
        
        peek   = datehigh[ptime] 
        valley = datelow[vtime] 
       
        longGold  = ([0], 1024, [], [])
        shortGold = ([0], -1024)
        timediff = self.__dtzq[vtime] - self.__dtzq[ptime]

        bddf = (peek - valley) / valley

        if (abs(timediff) >= 7 and (peek - valley) / valley >= 0.20) \
                or (abs(timediff) >= 11 and (peek - valley) / valley >= 0.10):
            longGold = self.longGoldSegment(dateTime, peek, valley)
       
        if self.__status <= 11 and (peek - valley) / valley > 0.8:
            shortGold = self.shortGoldSegment(dateTime, peek, valley)
        if self.__status == 21 and ((peek - datelow[nowgd]) / datelow[nowgd] > 0.8):
            shortGold = self.shortGoldSegment(dateTime, peek, datelow[nowgd])
        
        gs = 1024
        if len(longGold[0]) > 1:
            goldseg = np.where(np.array(longGold[0]) > 0)
            if len(goldseg[0]) > 0:
                gs = goldseg[0][0]

        peekzl = self.peekZL(dateTime, peek)
        mhead  = self.MHead(dateTime, fpeek, fvalley, datehigh)

        return (sum(longGold[0]), sum(shortGold[0]), shortGold[1], \
                longGold[1], longGold[2], longGold[3], bddf, gs, \
                peekzl, mhead)
#
