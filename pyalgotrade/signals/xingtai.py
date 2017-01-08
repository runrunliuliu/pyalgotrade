# coding:utf-8
import json


class XINGTAI(object):

    def __init__(self, dateTime, tups):

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
        self.__nowgd = tups[7]

        # qshist
        self.__qshist = tups[8]

        # direct
        self.__direct = tups[9]

        # final output
        self.__nqs    = 0
        self.__preqs  = 0
        self.__struct = []
        self.__gs     = []
        self.__zc     = {} 
        self.__jd     = {} 

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
   
    # 反转
    def fanzhuan(self):
        pass

    # 持续形态
    def chixu(self):
        pass

    # 支撑线和阻挡线
    def zcjd(self, nqs, nowclose, tup):
        peek1 = tup[1]; speek1 = peek1.strftime('%Y-%m-%d')
        vall1 = tup[3]; svall1 = vall1.strftime('%Y-%m-%d')

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

    # 三种最基本的走势定义
    #  1 -- 上升
    #  2 -- 盘整
    #  3 -- 下降
    def basicQS(self, tup):
        ret = 0 
        peek0 = tup[0]; speek0 = peek0.strftime('%Y-%m-%d')
        peek1 = tup[1]; speek1 = peek1.strftime('%Y-%m-%d')
        vall0 = tup[2]; svall0 = vall0.strftime('%Y-%m-%d')
        vall1 = tup[3]; svall1 = vall1.strftime('%Y-%m-%d')

        high0 = self.__high[peek0]; high1 = self.__high[peek1]
        low0 = self.__low[vall0]; low1 = self.__low[vall1]

        struct = None 
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

        gs = self.goldseg(max(high0, high1), min(low0, low1))

        return (ret, high0, low0, high1, low1, struct, gs)
#
