import numpy as np
import logging
import logging.config


# 波段的有效性指标
class BDvalid(object):

    def __init__(self, direct, qshist, change, dtzq, value, inst, maqstup):

        self.__logger = logging.getLogger('BDvalid')

        self.__inst   = inst
        self.__direct = direct 
        self.__qshist = qshist
        self.__change = change
        self.__dtzq   = dtzq
        self.__nbar   = value
        self.__maqstup = maqstup 

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
        MLINE = None 
        if len(peek) < 1:
            return MLINE
        npeek = peek[0]
        peekA = high[npeek[0]]
        peekB = high[npeek[0]]
        timed = 0
        for i in range(1, len(peek)):
            ptime = peek[i][0]
            peekB = high[ptime]
            hdiff = (peekB - peekA) / peekA
            if hdiff > 0.01:
                return MLINE
            timed = self.__dtzq[npeek[0]] - self.__dtzq[ptime] 

            if hdiff < 0.01 and hdiff > -0.01 and timed >= 31:
                MLINE = (npeek[0], peekA, peekB, timed)
                break
        if MLINE is not None:
            self.__logger.log(logging.ERROR, 'M_HEAD: %s %s %s', dateTime, self.__inst, MLINE)
        return MLINE

    # 通道定义@ QuChaoGu Corp.
    def QTDao(self, dateTime):
        ind   = None
        start = None
        end   = None
        if self.__maqstup[0] == 1:
            ind   = 1
            start = -1 
            end   = 0 
        if self.__maqstup[0] == -1:
            ind   = 5 
            start = 0 
            end   = -1
        ma5s = self.__maqstup[ind]
        nma5 = ma5s[-1]
        diff = (ma5s[start] - ma5s[end]) / ma5s[end]

        ma5t  = self.__maqstup[ind + 1]
        tdiff = self.__dtzq[ma5t[-1]] - self.__dtzq[ma5t[0]]

        ret = (1024, 1024, 1024) 
        if diff >= 0.002:
            diff =  "{:.4f}".format(diff)
            ret = (self.__maqstup[0], diff, tdiff)
        else:
            ma5s  = self.__maqstup[6 - ind + 2][-1]      
            start = end
            diff  = None
            dirt  = None 
            tdiff = self.__dtzq[dateTime] - self.__dtzq[self.__maqstup[6 - ind + 3][-1][0]]
            if ma5s[start] > nma5:
                diff = (ma5s[start] - nma5) / nma5
                dirt = -1
            else:
                diff = (nma5 - ma5s[start]) / ma5s[start]
                dirt = 1
            diff =  "{:.4f}".format(diff)
            ret = (dirt, diff, tdiff)
        return ret

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

        qtdao  = self.QTDao(dateTime)

        return (sum(longGold[0]), sum(shortGold[0]), shortGold[1], \
                longGold[1], longGold[2], longGold[3], bddf, gs, \
                peekzl, mhead, qtdao)
#
