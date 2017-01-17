# coding:utf-8
import json
import numpy as np
from pyalgotrade.utils import collections
from pyalgotrade.utils import qsLineFit 


class XINGTAI(object):

    def __init__(self):
        # final output
        self.__nqs    = 0
        self.__preqs  = 0
        self.__struct = []
        self.__gs     = []
        self.__zc     = {} 
        self.__jd     = {} 

        self.__incsector = []
        self.__dessector = []
       
        # QUSHI HISTORY
        self.__history_qs = collections.ListDeque(10)

    def initTup(self, dateTime, tups):
        self.__nowdt = dateTime
        # 周期
        self.__dtzq  = tups[0] 
        # 峰点
        self.__fpeek   = tups[1]
        # 谷点
        self.__fvalley = tups[2]

        # open
        self.__open  = tups[3]
        # high
        self.__high  = tups[4]
        # low
        self.__low   = tups[5]
        # close
        self.__close = tups[6]

        # nowgd 
        self.__nowgd  = tups[7]
        # qshist
        self.__qshist = tups[8]
        # direct
        self.__direct = tups[9]
        self.__format = '%Y-%m-%d'
        if tups[10] == '15mink':
            self.__format = '%Y-%m-%d-%H'

        self.__update = 0
        if tups[11] == 1 or tups[12] == -1:
            self.__update = 1

    # Main Module
    def run(self):
        self.qushi()

    def retJSON(self):
        out = dict()
        
        qs = dict()
        qs['nqs'] = self.__nqs
        qs['pqs'] = self.__preqs
        qs['gds'] = self.__struct
        qs['hcx'] = self.__gs
        qs['zc']  = self.__zc
        qs['jd']  = self.__jd

        out['qs'] = qs

        return json.dumps(out) 

    def retDICT(self):
        out = dict()
        
        qs = dict()
        qs['nqs'] = self.__nqs
        qs['pqs'] = self.__preqs
        qs['gds'] = self.__struct
        qs['hcx'] = self.__gs
        qs['zc']  = self.__zc
        qs['jd']  = self.__jd

        qs['isector']  = self.__incsector
        qs['dsector']  = self.__dessector

        out['qs'] = qs

        return out

    # 趋势
    def qushi(self):
        # 至少4段,前完趋势，当前可能趋势
        ret = None
        if len(self.__fpeek) < 2:
            return ret
        if len(self.__fvalley) < 2:
            return ret

        peek0 = self.__fpeek[0][0]
        peek1 = self.__fpeek[1][0]
        vall0 = self.__fvalley[0][0]
        vall1 = self.__fvalley[1][0]

        ngdlow  = self.__low[self.__nowgd]
        ngdhigh = self.__high[self.__nowgd]

        tup = (peek0, peek1, vall0, vall1)
        bqs = self.basicQS(tup)
        if self.__update == 1:
            self.__history_qs.append(bqs)
        pqs = bqs[0] 
        nqs = pqs

        if pqs == 1101 or pqs == 1201 or pqs == 1202:
            if ngdhigh >= bqs[1]:
                nqs = 2102
            else:
                nqs = 2203

        if pqs == 1301 or pqs == 1302:
            if ngdhigh >= bqs[2] and ngdhigh < bqs[1]:
                nqs = 2204
            if ngdhigh < bqs[2]:
                nqs = 2303
            if ngdhigh >= bqs[1]:
                nqs = 2103

        if pqs == 2102 or pqs == 2103:
            if ngdlow < bqs[1] and ngdlow > bqs[2]:
                nqs = 1201
            if ngdlow >= bqs[1]: 
                nqs = 1101
            if ngdlow < bqs[2]:
                nqs = 1301

        if pqs == 2203 and pqs == 2303 and pqs == 2204:
            if ngdlow >= bqs[2]:
                nqs = 1202
            else:
                nqs = 1302

        self.__preqs  = pqs
        self.__nqs    = nqs
        self.__struct = bqs[5]
        self.__gs     = bqs[6]

        nowclose = self.__close[self.__nowdt]
        self.zcjd(pqs, nowclose, tup)

        self.__incsector = self.incSectorLine(self.__nowdt)
        self.__dessector = self.desSectorLine(self.__nowdt)

        self.szline(self.__nowdt)
   
    # 反转
    def fanzhuan(self):
        pass

    # 持续形态
    def chixu(self):
        pass

    # 合并QS, 减少毛刺
    def mergeQS(self, dateTime, qslist):
        fgds  = set()
        QS    = []
        tnum  = 3 
        count = 1
        for i in range(1, len(qslist) + 1):
            if count > tnum:
                break
            struct = qslist[-1 * i][5]
            # 背离产生的异常结构
            zqarr  = np.asarray(qslist[-1 * i][7])
            if min(zqarr) < 0:
                continue
            # 如果相邻拐点bars过少, 前溯1个基本结构, 默认是3个基本结构
            index = -1
            if min(zqarr) <= 3:
                index = np.argmin(zqarr) 
                flag = 0
                for k in range(0, 2):
                    tday = struct[index + k]['d'] 
                    if tday in fgds:
                        flag = 1
                        break
                    else:
                        fgds.add(tday)
                if flag == 0:
                    tnum = tnum + 2
            QS.append(qslist[-1 * i] + (index,))
            count = count + 1
        return QS

    # 消除毛刺的5浪重构
    def wave5construct(self, dateTime, QS):
        used = set()
        w5 = () 
        i  = 1
        def add(w5, used, new):
            for item in new:
                if item not in used:
                    w5 = w5 + (item,)
                used.add(item)
            return (w5, used)

        while(i < len(QS) + 1):
            q = QS[-1 * i]
            # 基本结构无minbar
            if q[-1] == -1:
                if i == 1:
                    # w5 = w5 + q[8][0:3]
                    (w5, used) = add(w5, used, q[8][0:3])
                elif i == len(QS):
                    # w5 = w5 + q[8][2:4]
                    (w5, used) = add(w5, used, q[8][2:4])
                else:
                    # w5 = w5 + (q[8][2],)
                    (w5, used) = add(w5, used, (q[8][2],))
                step = 1 
            # 基本结构minbar居中
            if q[-1] == 1:
                if q[0] == 1302 or q[0] == 1301 \
                        or q[0] == 2102 or q[0] == 2103:
                    # w5 = w5 + (q[8][3],)
                    (w5, used) = add(w5, used, (q[8][3],))
                    step = 2
                else:
                    # w5 = w5 + (q[8][1],)
                    (w5, used) = add(w5, used, (q[8][1],))
                    step = 1
            # 基本结构minbar居始
            if q[-1] == 0:
                # w5 = w5 + q[8][2:4]
                (w5, used) = add(w5, used, q[8][2:4])
                step = 2
            # 基本结构minbar居末尾
            if q[-1] == 2:
                if i == len(QS):
                    # w5 = w5 + q[8][0:3]
                    (w5, used) = add(w5, used, q[8][0:3])
                else:
                    # w5 = w5 + q[8][0:2]
                    (w5, used) = add(w5, used, q[8][0:2])
                step = 1
            if i == len(QS) - 1:
                step = 1
            i = i + step
        print w5

    # 速阻线
    def szline(self, dateTime):
        qslist = self.__history_qs
        QS = self.mergeQS(dateTime, qslist)
        self.wave5construct(dateTime, QS)

    # 支撑线和阻挡线
    def zcjd(self, nqs, nowclose, tup):
        peek1 = tup[1]; speek1 = peek1.strftime(self.__format)
        vall1 = tup[3]; svall1 = vall1.strftime(self.__format)

        high1 = self.__high[peek1]
        low1 = self.__low[vall1]

        cxl = {} 
        if nqs == 1101 or nqs == 2102 or nqs == 2103: 
            cxl = {"d":speek1, "v":high1}
            if nowclose > high1:
                self.__zc = cxl 
            else:
                self.__jd = cxl 
        if nqs == 1301 or nqs == 1302 or nqs == 2204:
            cxl = {"d":svall1, "v":low1}
            if nowclose > low1:
                self.__zc = cxl 
            else:
                self.__jd = cxl 

    # 黄金分割位，百分比回撤
    def goldseg(self, high, low):
        out  = []
        gs   = [0.809, 0.618, 0.5, 0.382, 0.236]
        diff = high - low
        for g in gs:
            gi = high - diff * g
            gi = "{:.2f}".format(gi)
            gi = float(gi)
            out.append(gi)
        return out

    # 上升扇形
    def incSectorLine(self, dateTime):
        ret = []
        if len(self.__fvalley) < 4:
            return ret
        tgds = self.__fvalley
        ngd = tgds[3]
        
        nind1  = self.__dtzq[tgds[1][0]]
        close1 = self.__close[tgds[1][0]]
        nind2  = self.__dtzq[tgds[2][0]]
        close2 = self.__close[tgds[2][0]]

        if ngd[1] < tgds[0][1] and ngd[1] < tgds[1][1] and ngd[1] < tgds[2][1]:
            for i in range(0, 3):
                v     = (ngd[0], ngd[1], tgds[i][0], tgds[i][1])
                qsfit = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq)
                if i == 0:
                    if close1 < qsfit.compute(nind1) or close2 < qsfit.compute(nind2):
                        return [] 
                if i == 1:
                    if close2 < qsfit.compute(nind2):
                        return [] 
                ret.append(qsfit)
        out = []
        if len(ret) == 3:
            for r in ret:
                out.append(r.toDICT(self.__dtzq[dateTime]))
        return out

    # 下降扇形
    def desSectorLine(self, dateTime):
        ret = []
        if len(self.__fpeek) < 4:
            return ret
        tgds = self.__fpeek
        ngd = tgds[3]
        
        nind1  = self.__dtzq[tgds[1][0]]
        close1 = self.__close[tgds[1][0]]
        nind2  = self.__dtzq[tgds[2][0]]
        close2 = self.__close[tgds[2][0]]

        if ngd[1] > tgds[0][1] and ngd[1] > tgds[1][1] and ngd[1] > tgds[2][1]:
            for i in range(0, 3):
                v     = (ngd[0], ngd[1], tgds[i][0], tgds[i][1])
                qsfit = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq)
                if i == 0:
                    if close1 > qsfit.compute(nind1) or close2 > qsfit.compute(nind2):
                        return [] 
                if i == 1:
                    if close2 > qsfit.compute(nind2):
                        return [] 
                ret.append(qsfit)
        out = []
        if len(ret) == 3:
            for r in ret:
                out.append(r.toDICT(self.__dtzq[dateTime]))
        return out

    # 三种最基本的走势定义
    #  1 -- 上升
    #  2 -- 盘整
    #  3 -- 下降
    def basicQS(self, tup):
        ret = 0 
        peek0 = tup[0]; speek0 = peek0.strftime(self.__format)
        peek1 = tup[1]; speek1 = peek1.strftime(self.__format)
        vall0 = tup[2]; svall0 = vall0.strftime(self.__format)
        vall1 = tup[3]; svall1 = vall1.strftime(self.__format)

        high0 = self.__high[peek0]; high1 = self.__high[peek1]
        low0 = self.__low[vall0]; low1 = self.__low[vall1]

        # print self.__nowdt, tup, high0, high1, low0, low1
        zhouqi = None
        struct = None 
        timegd = None
        if self.__direct == -1:
            if high0 >= high1:
                if low0 >= high1:
                    ret = 1101
                else:
                    if low0 >= low1:
                        ret = 1201
                    else:
                        ret = 1301
            else:
                if low0 >= low1:
                    ret = 1202
                else:
                    ret = 1302
            struct = [{"d":speek1, 'v':high1}, {"d":svall1, 'v':low1}, \
                      {"d":speek0, 'v':high0}, {"d":svall0, 'v':low0}]

            zq1 = self.__dtzq[vall1] - self.__dtzq[peek1] + 1
            zq2 = self.__dtzq[peek0] - self.__dtzq[vall1] + 1
            zq3 = self.__dtzq[vall0] - self.__dtzq[peek0] + 1
            zhouqi = (zq1, zq2, zq3)
            timegd = (peek1, vall1, peek0, vall0)

        if self.__direct == 1:
            if low0 >= low1:
                if high0 >= high1:
                    ret = 2102 
                else:
                    ret = 2203 
            else:
                if high0 < low1:
                    ret = 2303 
                else:
                    if high0 < high1:
                        ret = 2204 
                    else:
                        ret = 2103
            struct = [{"d":svall1, 'v':low1}, {"d":speek1, 'v':high1}, \
                      {"d":svall0, 'v':low0}, {"d":speek0, 'v':high0}]
            zq1 = self.__dtzq[peek1] - self.__dtzq[vall1] + 1
            zq2 = self.__dtzq[vall0] - self.__dtzq[peek1] + 1
            zq3 = self.__dtzq[peek0] - self.__dtzq[vall0] + 1
            zhouqi = (zq1, zq2, zq3)
            timegd = (vall1, peek1, vall0, peek0)

        gs = self.goldseg(max(high0, high1), min(low0, low1))

        return (ret, high0, low0, high1, low1, struct, gs, zhouqi, timegd)
#
