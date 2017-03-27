# coding:utf-8
import logging
import json
import copy
import datetime
import os
import numpy as np
from pyalgotrade.utils import collections
from pyalgotrade.utils import qsLineFit


class XINGTAI(object):

    def __init__(self, inst):
        self.__logger  = logging.getLogger('XINGTAI')
        # final output
        self.__nqs    = 0
        self.__preqs  = 0
        self.__struct = []
        self.__gs     = []
        self.__zc     = {}
        self.__jd     = {}
        self.__szl    = {}

        self.__dtd = {}
        self.__xtd = {}

        self.__speedqs = {}

        self.__incsector = []
        self.__dessector = []

        self.__peekdays   = set()
        self.__valleydays = set()
       
        self.__gdp = None

        # QUSHI HISTORY
        self.__hist_qs     = collections.ListDeque(60)

        # 5浪结构数据
        self.__histinc_wave5  = collections.ListDeque(120)
        self.__histdes_wave5  = collections.ListDeque(120)
        self.__histhp_wave5   = collections.ListDeque(120)

        self.__eliotw5 = []
        self.__eliot   = dict()
        
        self.__tmp_eliotw5 = []
        self.__recursion   = 0
       
        # MHead历史数据
        self.__hist_mhead = []
        self.__hist_whead = []
        # TriBottom
        self.__hist_trib = []
        # TriHead
        self.__hist_trih = []
        # HeadShouldersBottom
        self.__hist_hsb  = []
        # HeadShouldersPeek
        self.__hist_hsp  = []
        
        # 趋势线
        self.__hist_qsl  = []
        self.__spec_qsl  = []
        
        self.__hist_chan = []

        # Triangle
        self.__hist_triangle  = collections.ListDeque(20)

        # 加速上升趋势线
        self.__qushi    = 0
        self.__pspeedup = None
        self.__pspeeddn = None
        self.__speedup   = []
        self.__speeddown = []
       
        # K线形态
        self.__kline = []

        # 周期
        self.__zhouqi = []

        # 斐波那契数列
        self.__fbsq  = {1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144}
        self.__fbsq1 = {2, 4, 7, 12, 20, 33, 54, 88, 143}

        # Load ChanLun Data
        self.__list_cl = []
        self.__dict_cl = {}
        fname = './data/czsc/' + inst + '.csv'
        tmp = self.loadChanLun(fname)
        if len(tmp) != 0:
            self.__list_cl = tmp[0]
            self.__dict_cl = tmp[1]

    # 初始化Tuple
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
        self.__period = tups[10]
        if tups[10] == '30min':
            self.__format = '%Y-%m-%d-%H-%M'
        if tups[10] == '60min':
            self.__format = '%Y-%m-%d-%H-%M'

        self.__beili  = tups[12]
        self.__update = 0
        if tups[11] == 1 or tups[12] == -1:
            self.__update = 1

        self.__inst = tups[13]
        self.__diff = 0.01
        if self.__inst[0:2] == 'SZ' or self.__inst[0:2] == 'SH':
            self.__diff = 0.01
            if self.__period == '30min':
                self.__diff = 0.001
            if self.__period == '60min':
                self.__diff = 0.001

        self.__klines   = tups[14]
        self.__score    = float("{:.2f}".format(tups[15]))
        self.__masigs   = tups[16]
        self.__macdsigs = tups[17]
        self.__nowval   = tups[18]

        self.__gd = dict()
        if len(self.__macdsigs) > 0:
            self.__gd['d'] = self.__nowgd.strftime(self.__format)
            if self.__macdsigs['hist'] > 0:
                self.__gd['v'] = self.__high[self.__nowgd]
            else:
                self.__gd['v'] = self.__low[self.__nowgd]

    # load chanlun
    def loadChanLun(self, fname):
        dic = {}
        ret = []
        if not os.path.isfile(fname):
            return ret
        fname = open(fname, 'r')
        cnt = 0
        for l in fname:
            if cnt == 0:
                cnt = cnt + 1
                continue
            arr = l.strip().split(',')
            dt = datetime.datetime.strptime(arr[0], "%Y-%m-%d")
            tp = int(arr[1])
            ret.append((dt, tp))
            dic[dt] = cnt - 1

            cnt = cnt + 1
        return (ret, dic)

    # Main Module
    def run(self):
        self.qushi()
        self.fanzhuan()
        self.chixu()
        self.klines()
        self.zhouqi()
        self.EliotWave5()

    def retJSON(self):
        out = dict()
        
        qs = dict()
        qs['nqs'] = self.__nqs
        qs['pqs'] = self.__preqs
        qs['gds'] = self.__struct
        qs['hcx'] = self.__gs
        qs['zc']  = self.__zc
        qs['jd']  = self.__jd
        qs['szl'] = self.__szl

        out['qs'] = qs

        return json.dumps(out) 

    # 返回字典结构数据
    def retDICT(self, value):
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

        qs['szl'] = self.__szl
        qs['sqs'] = self.__speedqs

        qs['mhead'] = self.__mhead
        qs['whead'] = self.__whead

        # qs['trib']     = self.__trib
        # qs['trih']     = self.__trih
        qs['hsb']      = self.__hsb
        qs['hsp']      = self.__hsp
        qs['triangle'] = self.__triangle

        qs['kline'] = self.__kline

        qs['ohlc'] = [value.getOpen(), value.getHigh(), \
                      value.getLow(), value.getClose()]

        qs['zq']   = self.__zhouqi
        qs['wave'] = self.__eliot

        out['qs']    = qs
        out['score'] = self.__score
        out['ma']    = self.__masigs
        out['macd']  = self.__macdsigs
        out['nowgd'] = self.__gd

        return out

    # 计算周期
    def zhouqi(self):
        def compute(dt):
            trange = nind - self.__dtzq[dt] + 1
            return trange
        zq   = dict()
        dateTime = self.__nowdt
        nind = self.__dtzq[dateTime]
        ret1 = dict()
        ret2 = []
        if len(self.__hist_qs) > 0:
            pqs  = self.__hist_qs[-1]
            pqs2 = None
            if len(self.__hist_qs) > 1:
                pqs2 = self.__hist_qs[-2]
                ret1['AF'] = compute(pqs2[8][0])
            ret1['BF'] = compute(pqs[8][0])
            ret1['CF'] = compute(pqs[8][1])

            DF = compute(pqs[8][2])
            ret1['DF'] = DF

            EF = compute(pqs[8][3])
            ret1['EF'] = EF

            # 谐波关系1: DE && EN
            DE = self.__dtzq[pqs[8][3]] - self.__dtzq[pqs[8][2]] + 1
            ret1['DE'] = DE
            
            # 谐波关系2: CE && DF
            CE = self.__dtzq[pqs[8][3]] - self.__dtzq[pqs[8][1]] + 1
            ret1['CE'] = CE
            
            # 谐波关系3: CE/AC && DF/BD
            BD = self.__dtzq[pqs[8][2]] - self.__dtzq[pqs[8][0]] + 1
            ret1['BD'] = BD
            if pqs2 is not None:
                AC = self.__dtzq[pqs[8][1]] - self.__dtzq[pqs2[8][0]] + 1
                ret1['AC'] = AC
                r1 = float("{:.2f}".format(CE / (AC + 0.0)))
                ret1['CE/AC'] = r1
                r2 = float("{:.2f}".format(DF / (BD + 0.0)))
                ret1['DF/BD'] = r2

            # 江恩比率
            CD = self.__dtzq[pqs[8][2]] - self.__dtzq[pqs[8][1]] + 1
            ret1['CD'] = CD
            r1 = float("{:.2f}".format(DF / (CD + 0.0)))
            ret1['DF/CD'] = r1
            r1 = float("{:.2f}".format(EF / (CE + 0.0)))
            ret1['EF/CE'] = r1

            # 五浪
            w5  = self.getWave5Neighbor(dateTime)
            if len(w5[1][1]['szx']) > 0:
                st = w5[1][1]['szx']['time']
                w1 = compute(st[0])
                w2 = compute(st[1])
                ret2 = [w1, w2]
            
            zq['zq1'] = ret1
            zq['zq2'] = ret2

        self.__zhouqi = zq

    # KLines
    def klines(self):
        cdlist   = self.__klines[12]
        if len(cdlist) > 0:
            self.__kline = cdlist[-1][1]

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

        # add2peekdays
        self.__peekdays.add(peek0)
        self.__peekdays.add(peek1)
        self.__valleydays.add(vall0)
        self.__valleydays.add(vall1)

        # print self.__nowdt, self.__update, self.__direct, tup
        bqs = self.basicQS(tup, self.__direct)
        if self.__update == 1:
            self.__hist_qs.append(bqs)
        pqs = bqs[0] 
        nqs = pqs

        high0 = bqs[1]; low0 = bqs[2]
        high1 = bqs[3]; low1 = bqs[4]

        if pqs == 1101 or pqs == 1201 or pqs == 1202:
            if ngdhigh >= high0:
                nqs = 2102
            else:
                nqs = 2203
        if pqs == 1301 or pqs == 1302:
            if ngdhigh >= low1 and ngdhigh < high0:
                nqs = 2204
            if ngdhigh < low1:
                nqs = 2303
            if ngdhigh >= high0:
                nqs = 2103
        if pqs == 2102 or pqs == 2103:
            if ngdlow < high1 and ngdlow > low0:
                nqs = 1201
            if ngdlow >= high1: 
                nqs = 1101
            if ngdlow <= low0 and pqs == 2103:
                nqs = 1301
            if ngdlow <= low0 and pqs == 2102:
                nqs = 1201
        if pqs == 2203 or pqs == 2303 or pqs == 2204:
            if ngdlow >= low0:
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

        dateTime = self.__nowdt
        if self.__update == 1:
            wave5    = self.wave5construct(dateTime)
            wave5ret = self.computeWave5(dateTime, wave5)
            if wave5[0] == 1: 
                self.__histinc_wave5.append(wave5ret)
            if wave5[0] == -1: 
                self.__histdes_wave5.append(wave5ret)
            if wave5[0] == 0: 
                self.__histhp_wave5.append(wave5ret)
            self.speedQS(dateTime)

        self.__szl     = self.getSZLine(dateTime)
        self.__speedqs = self.getSpeedQs(dateTime) 

        # 大通道
        self.__dtd = self.getDATD(dateTime)

        # 小通道
        if dateTime in self.__dict_cl:
            w5cl = self.wave5ChanLun(dateTime)
            qsl  = self.qsLine(dateTime, w5cl)
            if len(qsl[0]) > 0:
                self.__hist_chan.append(qsl)
        self.__xtd = self.getXTD(dateTime)

    # 反转
    def fanzhuan(self):
        dateTime = self.__nowdt
        
        # 拐点形成之时构建结构
        if self.__update == 1:
            ret = self.MHead(dateTime)
            if len(ret) > 0:
                self.__hist_mhead.append(ret)
            ret = self.WHead(dateTime)
            if len(ret) > 0:
                self.__hist_whead.append(ret)

        if self.__nowgd is not None:
            ngd = self.__nowgd.strftime(self.__format)
            ngv = self.__low[self.__nowgd] 
            if self.__direct == -1:
                ngv = self.__high[self.__nowgd]
            self.__gdp = (ngd, ngv, self.__direct, {'d': ngd, 'v': ngv})

        self.__mhead = self.getHistXingTai(self.__hist_mhead, dateTime, self.__gdp)
        self.__whead = self.getHistXingTai(self.__hist_whead, dateTime, self.__gdp)
        self.__hsb   = self.getHistXingTai(self.__hist_hsb, dateTime, self.__gdp)
        self.__hsp   = self.getHistXingTai(self.__hist_hsp, dateTime, self.__gdp)

    # M头精准定义
    def MHead(self, dateTime):
        ret = () 
        if len(self.__hist_qs) == 0:
            return ret
        preqs = self.__hist_qs[-1]
        ratio = None
        peek0 = preqs[1]
        peek1 = preqs[3]
        if preqs[0] == 2102:
            ratio = (peek0 - peek1) / peek1
        if preqs[0] == 2203:
            ratio = (peek1 - peek0) / peek0
        if ratio is not None and ratio < self.__diff:
            out = {}
            out['st']  = preqs[5]
            out['nec'] = preqs[5][2]['v'] 
            out['hd']  = float("{:.2f}".format((peek0 + peek1) * 0.5))
            out['s']   = 0
            out['nm']  = 'mh'
            ret = (out, dateTime)
        return ret

    # W头精准定义
    def WHead(self, dateTime):
        ret = () 
        if len(self.__hist_qs) == 0:
            return ret
        preqs = self.__hist_qs[-1]
        ratio = None
        vall0 = preqs[2]
        vall1 = preqs[4]
        if preqs[0] == 1202:
            ratio = (vall0 - vall1) / vall1
        if preqs[0] == 1302:
            ratio = (vall1 - vall0) / vall0
        if ratio is not None and ratio < self.__diff:
            out = {}
            out['st']  = preqs[5]
            out['nec'] = preqs[5][2]['v']
            out['hd']  = float("{:.2f}".format((vall0 + vall1) * 0.5))
            out['s']   = 0
            out['nm']  = 'wh'
            ret = (out, dateTime)
        return ret

    # 持续形态
    def chixu(self):
        dateTime = self.__nowdt
        if self.__update == 1:
            if len(self.__hist_qs) > 0:
                preqs = self.__hist_qs[-1]
                triangle = self.triangle(dateTime, preqs)
                self.__hist_triangle.append(triangle)

        self.__triangle = self.getTriangle(dateTime)

    # 获取Triangle
    def getTriangle(self, dateTime):
        ret = {}
        if len(self.__hist_triangle) > 0:
            triangle = self.__hist_triangle[-1]
            ret = triangle[0]

            qs13 = triangle[2]
            qs24 = triangle[3]
            nind = self.__dtzq[dateTime]
            ret['l1'] = qs13.toDICT(nind)
            ret['l2'] = qs24.toDICT(nind)
            ret['st'] = [ret['l1']['p1'], \
                         ret['l2']['p1'], \
                         ret['l1']['p2'], \
                         ret['l2']['p2']]

            ret['dtd'] = self.__dtd
            ret['xtd'] = self.__xtd

        return ret

    # 获取triangle形态的名字
    def getTriangleName(self, dateTime, pl, vl):
        xtname = 'NULL'
        # 阀值参数parameters
        slope_rt = 3 
        # slope_b = 0.001
        # slope_t = 0.0005
        # if self.__period == '30min':
        #     slope_t = 0.0001
        # if self.__period == '60min':
        #     slope_t = 0.0001

        pslope = pl.getSlope() 
        vslope = vl.getSlope()

        # 喇叭形
        if (pslope > 0 and vslope < 0 ) or \
                (pslope > 0 and vslope > 0 and pslope / vslope > slope_rt) or \
                (pslope < 0 and vslope < 0 and pslope / vslope > slope_rt):
            xtname = 'trumptriangle'

        return xtname

    # 多种形态
    def triangle(self, dateTime, preqs):
        xtname = 'NULL'
        output = {}
        # 1-3
        p1 = preqs[5][0]
        p3 = preqs[5][2]
        v  = (preqs[8][0], p1['v'], preqs[8][2], p3['v']) 
        qs13 = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq, formats = self.__format)
        s13  = qs13.getSlope()
        # 2-4
        p2 = preqs[5][1]
        p4 = preqs[5][3]
        v  = (preqs[8][1], p2['v'], preqs[8][3], p4['v']) 
        qs24 = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq, formats = self.__format)
        s24  = qs24.getSlope()

        # 阀值参数parameters
        slope_t = 0.0005
        slope_b = 0.001

        if self.__period == '30min':
            slope_t = 0.0001
        if self.__period == '60min':
            slope_t = 0.0001

        # 对称三角
        # print 'DEBUG: ------------', dateTime, preqs, s13, s24
        if preqs[0] == 1202 and s13 < -1 * slope_b and s24 > slope_b and abs(s13 + s24) <= slope_t:
            xtname = 'symtriangle'
        if preqs[0] == 2203 and s13 > slope_b and s24 < -1 * slope_b and abs(s13 + s24) <= slope_t:
            xtname = 'symtriangle'
        # 上升三角
        if (preqs[0] == 1201 or preqs[0] == 1202) and abs(s13) <= slope_t and s24 >= slope_b:
            xtname = 'asctriangle'
        if (preqs[0] == 2102 or preqs[0] == 2203) and abs(s24) <= slope_t and s13 >= slope_b:
            xtname = 'asctriangle'
        # 下降三角
        if (preqs[0] == 1202 or preqs[0] == 1302) and abs(s24) <= slope_t and s13 <= -1 * slope_b:
            xtname = 'destriangle'
        if (preqs[0] == 2203 or preqs[0] == 2204) and abs(s13) <= slope_t and s24 <= -1 * slope_b:
            xtname = 'destriangle'
        # 喇叭形
        if preqs[0] == 1301 and s24 <= -1 * slope_b and s13 >= slope_b:
            xtname = 'trumptriangle'
        if preqs[0] == 2103 and s24 >= slope_b and s13 <= -1 * slope_b:
            xtname = 'trumptriangle'
        # 上升旗形
        if (preqs[0] == 1101 and preqs[0] == 1201 and preqs[0] == 2102) \
                and abs(s13 - s24) < slope_t \
                and s13 >= slope_b and s24 >= slope_b:
            xtname = 'aflagtriangle'
        # 下降旗形
        if (preqs[0] == 1302 and preqs[0] == 2303 and preqs[0] == 2204) \
                and abs(s13 - s24) < slope_t \
                and s13 <= -1 * slope_b and s24 <= -1 * slope_b:
            xtname = 'dflagtriangle'
        # 上升楔形
        if (preqs[0] == 1101 and preqs[0] == 1201) \
                and s13 >= slope_b and s24 >= slope_b \
                and (s24 - s13) >= slope_b * 2:
            xtname = 'ascwedge'
        # 上升楔形
        if preqs[0] == 2102 and s13 >= slope_b and s24 >= slope_b \
                and (s13 - s24) >= slope_b * 2:
            xtname = 'ascwedge'
        # 下降楔形
        if (preqs[0] == 2303 and preqs[0] == 2204) \
                and s13 <= -1 * slope_b and s24 <= -1 * slope_b \
                and (s13 - s24) >= slope_b * 2:
            xtname = 'deswedge'
        # 下降楔形
        if preqs[0] == 1302 and s13 <= -1 * slope_b and s24 <= -1 * slope_b \
                and (s24 - s13) >= slope_b * 2:
            xtname = 'deswedge'
        # 矩形
        if abs(s13) <= slope_t and abs(s24) <= slope_t:
            xtname = 'rectangle'

        output['name'] = xtname

        return (output, dateTime, qs13, qs24)

    # 获取加速趋势线
    def getSpeedQs(self, dateTime):
        output = dict()
        nind = self.__dtzq[dateTime]
        speed = None
        if self.__qushi == 1 and len(self.__speedup) > 1:
            speed = self.__speedup
        if self.__qushi == -1 and len(self.__speeddown) > 1:
            speed = self.__speeddown
        lines = []
        if speed is not None:
            for s in speed:
                tmp = dict()
                tmp['line']  = s.toDICT(nind)
                tmp['slope'] = float("{:.2f}".format(s.getSlope()))
                lines.append(tmp)
            output['lines'] = lines
            output['qushi'] = self.__qushi
        return output

    # 加速趋势线 
    def speedQS(self, dateTime):
        preqs = self.__hist_qs[-1]
        v     = (preqs[8][1], preqs[5][1]['v'], preqs[8][3], preqs[5][3]['v']) 
        qsfit = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq)
        # 上升趋势
        if preqs[0] == 1101 or preqs[0] == 1201 or preqs[0] == 1202:
            if self.__pspeedup is None:
                self.__speedup.append(qsfit)
            else:
                if self.__pspeedup.getSlope() < qsfit.getSlope():
                    self.__speedup.append(qsfit)
                else:
                    self.__speedup  = []
                    self.__speedup.append(qsfit)
            self.__pspeedup = qsfit
            self.__qushi    = 1
        if preqs[0] == 1301 or preqs[0] == 1302:
            self.__pspeedup = None
            self.__speedup  = []
        # 下降趋势
        if preqs[0] == 2203 or preqs[0] == 2303 or preqs[0] == 2204:
            if self.__pspeeddn is None:
                self.__speeddown.append(qsfit)
            else:
                if self.__pspeeddn.getSlope() > qsfit.getSlope():
                    self.__speeddown.append(qsfit)
                else:
                    self.__speeddown = []
                    self.__speeddown.append(qsfit)
            self.__pspeeddn = qsfit
            self.__qushi    = -1
        if preqs[0] == 2102 or preqs[0] == 2103:
            self.__pspeeddn  = None
            self.__speeddown = []

    # 计算wave5相关的元素
    def computeWave5(self, dateTime, wave5):
        ret = dict()

        ret['w5']  = wave5
        # 计算速阻线
        szline = self.szline(self.__nowdt, wave5)
        ret['szx'] = szline

        # 计算三重底
        trib = self.triBottom(dateTime, wave5)
        if len(trib[0]) > 0:
            self.__hist_trib.append(trib)

        # 计算三重顶
        trih = self.triHead(dateTime, wave5)
        if len(trih[0]) > 0:
            self.__hist_trih.append(trih)

        # 计算头肩底
        hsb = self.headShoulderBottom(dateTime, wave5)
        if len(hsb[0]) > 0:
            self.__hist_hsb.append(hsb)

        # 计算头肩顶
        hsp = self.headShoulderPeek(dateTime, wave5)
        if len(hsp[0]) > 0:
            self.__hist_hsp.append(hsp)

        # 计算趋势线
        qsl = self.qsLine(dateTime, wave5)
        if len(qsl[0]) > 0:
            self.__hist_qsl.append(qsl)

        return (dateTime, ret)

    def getW5Struct(self, wave5):
        vall = []
        peek = []
        w5    = wave5[1]
        if len(w5) < 3:
            return None 

        d1 = w5[0][8][0]
        d2 = w5[0][8][1]
        d3 = w5[0][8][2]
        d4 = w5[1][8][2]
        d5 = w5[1][8][3]
        d6 = w5[2][8][3]
 
        v1 = w5[0][5][0]['v']
        v2 = w5[0][5][1]['v']
        v3 = w5[0][5][2]['v']
        v4 = w5[1][5][2]['v']
        v5 = w5[1][5][3]['v']
        v6 = w5[2][5][3]['v']

        # 奇数
        odd  = [(d1, v1), (d3, v3), (d5, v5)]
        # 偶数
        even = [(d2, v2), (d4, v4), (d6, v6)]

        peek = even
        vall = odd
        if w5[0][0] < 2000:
            peek = odd
            vall = even
        return (peek, vall) 
 
    # 计算趋势线
    def qsLine(self, dateTime, wave5):
        def gen(arr, flag):
            t13 = (arr[0][0], arr[0][1], arr[1][0], arr[1][1])
            p13 = qsLineFit.QsLineFit.initFromTuples(t13, self.__dtzq)
            t15 = (arr[0][0], arr[0][1], arr[2][0], arr[2][1])
            p15 = qsLineFit.QsLineFit.initFromTuples(t15, self.__dtzq)
            t35 = (arr[1][0], arr[1][1], arr[2][0], arr[2][1])
            p35 = qsLineFit.QsLineFit.initFromTuples(t35, self.__dtzq)

            def check(qsfit, dt, val, flag):
                ret = 0
                ind = self.__dtzq[dt]
                pval = qsfit.compute(ind)
                if (pval - val) * flag < 0:
                    ret = 1
                return (ret, qsfit.getWindows(), qsfit)

            ck13 = check(p13, arr[2][0], arr[2][1], flag)
            ck15 = check(p15, arr[1][0], arr[1][1], flag)
            ck35 = check(p35, arr[0][0], arr[0][1], flag)

            tmp = ck13
            for k in [ck15, ck35]:
                if k[0] == 1 and k[1] > tmp[1]:
                    tmp = k
            return tmp[2]
        ret   = []
        # 前一个5浪
        w5st  = self.getW5Struct(wave5)
        if w5st is not None:
            peek = w5st[0]
            vall = w5st[1]
            pl = gen(peek, -1)
            vl = gen(vall, 1)
            ret = [pl, vl]
        return (ret, wave5[0])

    # 计算三重底
    def triBottom(self, dateTime, wave5):
        ret = {}
        w5  = wave5[1]
        if len(w5) == 3:
            if w5[0][0] == 1202 or w5[0][0] == 1302:
                p2 = w5[0][5][1]['v']
                p3 = w5[0][5][2]['v']
                p4 = w5[1][5][2]['v']
                p5 = w5[1][5][3]['v']
                p6 = w5[2][5][3]['v']
                if abs((p2 - p4) / p4) < self.__diff and \
                        abs((p6 - p4) / p4) < self.__diff and \
                        abs((p3 - p5) / p5) < self.__diff:
                    ret['st']  = w5[0][5] + w5[2][5][2:]
                    ret['nec'] = float("{:.2f}".format((p3 + p5) * 0.5))
                    ret['hd']  = float("{:.2f}".format((p2 + p4 + p6) / 3))
        return (ret, dateTime)
    
    # 计算三重顶
    def triHead(self, dateTime, wave5):
        ret = {}
        w5  = wave5[1]
        if len(w5) == 3:
            if w5[0][0] == 2102 or w5[0][0] == 2203:
                p2 = w5[0][5][1]['v']
                p3 = w5[0][5][2]['v']
                p4 = w5[1][5][2]['v']
                p5 = w5[1][5][3]['v']
                p6 = w5[2][5][3]['v']
                if abs((p2 - p4) / p4) < self.__diff and \
                        abs((p6 - p4) / p4) < self.__diff and \
                        abs((p3 - p5) / p5) < self.__diff:
                    ret['st']  = w5[0][5] + w5[2][5][2:]
                    ret['nec'] = float("{:.2f}".format((p3 + p5) * 0.5))
                    ret['hd']  = float("{:.2f}".format((p2 + p4 + p6) / 3))
        return (ret, dateTime)

    # 计算头肩底
    # st--struct
    def headShoulderBottom(self, dateTime, wave5):
        ret = {}
        w5  = wave5[1]
        if len(w5) == 3:
            if w5[0][0] == 1302:
                p2 = w5[0][5][1]['v']
                p3 = w5[0][5][2]['v']
                p4 = w5[1][5][2]['v']
                p5 = w5[1][5][3]['v']
                p6 = w5[2][5][3]['v']
                if (p4 - p2) / p2 < -0.01 and \
                        abs((p5 - p3) / p3) < 0.03 and \
                        p6 < p3 and (p4 - p6) / p4 < -0.01:
                    ret['st']  = w5[0][5] + w5[2][5][2:]
                    ret['nec'] = [w5[0][5][2], w5[1][5][3]] 
                    ret['hd']  = [w5[0][5][1], w5[2][5][3]]
                    ret['s']   = 0
                    ret['nm']  = 'hsb'
        return (ret, dateTime)

    # 计算头肩顶
    def headShoulderPeek(self, dateTime, wave5):
        ret = {}
        w5  = wave5[1]
        if len(w5) == 3:
            if w5[0][0] == 2102:
                p2 = w5[0][5][1]['v']
                p3 = w5[0][5][2]['v']
                p4 = w5[1][5][2]['v']
                p5 = w5[1][5][3]['v']
                p6 = w5[2][5][3]['v']
                if (p4 - p2) / p2 > 0.01 and \
                        abs((p5 - p3) / p3) < 0.03 and \
                        p6 > p3 and (p4 - p6) / p4 > 0.01:
                    ret['st']  = w5[0][5] + w5[2][5][2:]
                    ret['nec'] = [w5[0][5][2], w5[1][5][3]] 
                    ret['hd']  = [w5[0][5][1], w5[2][5][3]]
                    ret['s']   = 0
                    ret['nm']  = 'hsp'
        return (ret, dateTime)

    # 获取形态
    def getHistXingTai(self, xingtai, dateTime, gdp, wins=90):
        ret = {}
        if len(xingtai) > 0:
            mh  = xingtai[-1] 
            dt0 = self.__dtzq[mh[1]]
            dt1 = self.__dtzq[dateTime]
            if dt1 - dt0 < wins: 
                tmp = self.upXingTai(mh[0], dateTime, gdp)
                if tmp['s'] > 0:
                    ret = tmp
        return ret

    # 更新形态
    def upXingTai(self, xt, dateTime, gdp):
        if gdp is None:
            return xt
        if xt['s'] == 1:
            return xt
        ret = copy.deepcopy(xt)
        if xt['nm'] == 'wh':
            nec = xt['nec']
            if gdp[2] == -1 and gdp[1] >= nec:
                ret['st'] = xt['st'] + [gdp[3]]
                ret['s']  = 1
                self.__hist_whead.append((ret, dateTime))
        if xt['nm'] == 'mh':
            nec = xt['nec']
            if gdp[2] == 1 and gdp[1] <= nec:
                ret['st'] = xt['st'] + [gdp[3]]
                ret['s']  = 1
                self.__hist_mhead.append((ret, dateTime))
        if xt['nm'] == 'hsp':
            if gdp[2] == 1:
                ret['st'] = xt['st'] + [gdp[3]]
                ret['s']  = 1
                self.__hist_hsp.append((ret, dateTime))
        if xt['nm'] == 'hsb':
            if gdp[2] == -1:
                ret['st'] = xt['st'] + [gdp[3]]
                ret['s']  = 1
                self.__hist_hsb.append((ret, dateTime))
        return ret

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

    # 构造wave5define的标准结构，从缠论的顶底分型
    # 六个点, 只考虑最近的六个点
    def wave5ChanLun(self, dateTime):
        # 出现新的拐点
        nind = self.__dict_cl[dateTime]
        w5   = ()
        aqs  = []

        # 至少需要6个拐点
        if len(self.__list_cl) < 6:
            return (0, aqs)

        for i in range(0, 6):
            if nind - i < 0:
                break
            p  = self.__list_cl[nind - i]
            w5 = (p,) + w5
        i = 0
        while i < len(w5) - 3:
            direct = 0
            if w5[i][1] == 0:
                tup = (w5[i+3][0], w5[i+1][0], w5[i+2][0], w5[i+0][0])
                direct = 1
            else:
                tup = (w5[i+2][0], w5[i+0][0], w5[i+3][0], w5[i+1][0])
                direct = -1

            qs = self.basicQS(tup, direct)
            aqs.append(qs)
            i = i + 1

        # 为空返回空
        if len(aqs) < 3:
            return (0, aqs)
        # 上升浪
        if aqs[0][0] == 2102 and (aqs[2][0] == 2102 or aqs[2][0] == 2103):
            return (1, aqs)
        # 下降浪
        if (aqs[0][0] == 1302 or aqs[0][0] == 1202 ) and (aqs[2][0] == 1302 or aqs[2][0] == 1301):
            return (-1, aqs)
        # 其他
        return (0, aqs)

    # 定义五浪的标准结构
    def wave5define(self, dateTime, w5):
        i   = 0
        aqs = []
        while i < len(w5) - 3:
            direct = 0
            if w5[i] in self.__valleydays:
                tup = (w5[i+3], w5[i+1], w5[i+2], w5[i])
                direct = 1
            else:
                tup = (w5[i+2], w5[i], w5[i+3], w5[i+1])
                direct = -1
            qs = self.basicQS(tup, direct)
            aqs.append(qs)
            i = i + 1

        # 为空返回空
        if len(aqs) < 3:
            return (0, aqs)
        # 上升浪
        if aqs[0][0] == 2102 and (aqs[2][0] == 2102 or aqs[2][0] == 2103):
            return (1, aqs)
        # 下降浪
        if (aqs[0][0] == 1302 or aqs[0][0] == 1202 ) and (aqs[2][0] == 1302 or aqs[2][0] == 1301):
            return (-1, aqs)
        # 其他
        return (0, aqs)

    # 消除毛刺的5浪重构
    def wave5construct(self, dateTime):
        qslist = self.__hist_qs
        QS     = self.mergeQS(dateTime, qslist)
        used = set()
        w5 = ()
        i  = 1
        def add(w5, used, new):
            for item in new:
                if item not in used:
                    w5 = w5 + (item,)
                used.add(item)
            return (w5, used)

        def remove(w5, indict):
            new5 = ()
            for i in range(0, len(w5)):
                if i not in indict:
                    new5 = new5 + (w5[i], )
            return new5

        step = 1
        while(i < len(QS) + 1):
            q = QS[-1 * i]
        
            # FOR DEBUG
            # print dateTime, i, q, w5, q[-1], q[0]
            # 基本结构无minbar
            if q[-1] == -1:
                if i == 1:
                    (w5, used) = add(w5, used, q[8][0:3])
                elif i == len(QS):
                    (w5, used) = add(w5, used, q[8][2:4])
                else:
                    (w5, used) = add(w5, used, (q[8][2],))
                step = 1
            # 基本结构minbar居中
            if q[-1] == 1:
                # 第一个QS需要特殊处理
                if i == 1:
                    if q[0] == 1302 or q[0] == 2102:
                        (w5, used) = add(w5, used, (q[8][0],))
                    if q[0] == 1202 or q[0] == 2203:
                        (w5, used) = add(w5, used, (q[8][0],))
                    if q[0] == 1301 or q[0] == 2103:
                        (w5, used) = add(w5, used, q[8][2:4])
                    if q[0] == 1101 or q[0] == 1201 or q[0] == 2303 or q[0] == 2204:
                        (w5, used) = add(w5, used, q[8][1:3])
                    step = 1
                else:
                    if q[0] == 1302 or q[0] == 1301 \
                            or q[0] == 2102 or q[0] == 2103:
                        (w5, used) = add(w5, used, (q[8][3],))
                        step = 2
                    else:
                        (w5, used) = add(w5, used, (q[8][1],))
                        step = 1
            # 基本结构minbar居始
            if q[-1] == 0:
                (w5, used) = add(w5, used, q[8][2:4])
                step = 2
            # 基本结构minbar居末尾
            if q[-1] == 2:
                if i == len(QS):
                    (w5, used) = add(w5, used, q[8][0:3])
                else:
                    if q[0] == 1302 or q[0] == 2102:
                        num = len(w5)
                        w5  = remove(w5, {num - 1})
                        (w5, used) = add(w5, used, (q[8][3],))
                        step = 2
                    else:
                        (w5, used) = add(w5, used, q[8][0:2])
                        step = 1
            if i == len(QS) - 1:
                step = 1
            i = i + step
        return self.wave5define(dateTime, w5)

    # 计算速阻线
    def szline(self, dateTime, wave5):
        ret = None
        out = dict()
        if len(wave5[1]) == 0:
            return out
        if len(wave5[1]) == 3:
            # start point
            timegd0 = wave5[1][0][8]
            struct0 = wave5[1][0][5]
            # end point
            timegd1 = wave5[1][2][8]
            struct1 = wave5[1][2][5]

            sdate  = timegd0[0]
            sprice = struct0[0]['v']
            edate  = timegd1[3]
            eprice = struct1[3]['v']

            high = None
            low  = None
            if wave5[0] == 1:
                ret = 1
                high = eprice
                low  = sprice
            if wave5[0] == -1:
                ret = -1
                high = sprice
                low  = eprice
            if ret is not None:
                third1 = float("{:.2f}".format(2 * high / 3 + low / 3))
                third2 = float("{:.2f}".format(1 * high / 3 + 2 * low / 3))

                show = dict()
                show['dir'] = ret
                show['d0']  = sdate.strftime(self.__format)
                show['d1']  = edate.strftime(self.__format)
                show['v']   = [high, third1, third2, low]
                show['gds'] = self.goldseg(high, low)
               
                # compute Lines
                v   = (sdate, sprice, edate, third1)
                qs1 = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq)
                v   = (sdate, sprice, edate, third2)
                qs2 = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq)

                out['show'] = show
                out['np']   = [qs1, qs2]
                out['time'] = [sdate, edate]
        return out

    # 获取最近的非盘整状态
    def getWave5Neighbor(self, dateTime):
        inc = self.__histinc_wave5
        des = self.__histdes_wave5
        hpp = self.__histhp_wave5
       
        nstatus = 0
        neighbb = None

        if len(inc) > 0 and len(des) == 0:
            nstatus = 1
            neighbb = inc[-1]

        if len(inc) == 0 and len(des) > 0:
            nstatus = -1
            neighbb = des[-1]

        if len(inc) > 0 and len(des) > 0:
            if inc[-1][0] > des[-1][0]:
                nstatus = 1
                neighbb = inc[-1]
            else:
                nstatus = -1
                neighbb = des[-1]

        if len(hpp) > 0:
            if neighbb is None:
                nstatus = 0
                neighbb = hpp[-1]
            else:
                if hpp[-1][0] > neighbb[0]:
                    nstatus = 0

        return (nstatus, neighbb)

    # 获取小通道
    def getXTD(self, dateTime):
        ret = {}
        if len(self.__hist_chan) == 0:
            return ret
        nind = self.__dtzq[dateTime]
        qsl  = self.__hist_chan[-1]
        l1   = qsl[0][0]
        l2   = qsl[0][1]
        ret['l1'] = l1.toDICT(nind)
        ret['l2'] = l2.toDICT(nind)
        return ret

    # 获取qsLine，至少一条线
    def getDATD(self, dateTime):
        ret = {}
        nind = self.__dtzq[dateTime]
        if len(self.__hist_qsl) == 0:
            return ret
        qsl  = self.__hist_qsl[-1]
        # 检查当前是否在通道附近, 或者在通道内部
        def check(qsl, val):
            close = val.getClose()
            ck    = 0
            yuzhi = 0.10
            if self.__inst[0:2] == 'ZS':
                yuzhi = 0.05
            for q in qsl:
                nval = q.compute(nind)
                if abs(close - nval) / abs(nval + 0.00000001) < yuzhi:
                    ck = 1
                    break
            up = qsl[0].compute(nind)
            dn = qsl[1].compute(nind)
            # 在通道内部
            if close <= up and close >= dn:
                ck = 1
            # 通道已经交叉
            if up <= dn:
                ck = 0
            # 在喇叭形的通道内部
            if close < up * 0.90 and close > dn * 1.10 \
                    and self.getTriangleName(dateTime, qsl[0], qsl[1]) == 'trumptriangle':
                ck = 0
            return ck

        val = self.__nowval

        # 计算大通道, 默认是当前五浪，需要检查最近的一次明显趋势通道
        l1   = qsl[0][0]
        l2   = qsl[0][1]

        spec = None
        if len(self.__spec_qsl) > 0:
            spec = self.__spec_qsl[-1]
        checkflag = 0
        if spec is not None:
            checkflag = check(spec[0], val)
            if checkflag == 1:
                l1 = spec[0][0]
                l2 = spec[0][1]

        ret['l1'] = l1.toDICT(nind)
        ret['l2'] = l2.toDICT(nind)

        # ADD SPECIAL to HISTORY
        if qsl[1] != 0:
            self.__spec_qsl.append(qsl)
        return ret
   
    # 获取速阻线
    def getSZLine(self, dateTime):
        ret = {}
        w5  = self.getWave5Neighbor(dateTime)
        if len(w5[1][1]['szx']) > 0:
            qs  = w5[1][1]['szx']['np']
            ind = self.__dtzq[dateTime]
            np1 = float("{:.2f}".format(qs[0].compute(ind)))
            np2 = float("{:.2f}".format(qs[1].compute(ind)))
            np  = [np1, np2]

            show = w5[1][1]['szx']['show']
            ret['dir']  = show['dir']
            ret['d0']   = show['d0']
            ret['d1']   = show['d1']
            ret['v']    = show['v']
            ret['gds']  = show['gds']
            ret['np']   = np
        return ret

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

    # 艾略特标准结构展示
    def EliotShow(self, dateTime, eliot):
        ret = dict()
        def show(wave):
            ret = []
            num = wave['num']
            st  = wave['st']
            for i in range(0, num + 1):
                tmp = dict()
                dat = st[i][0][0].strftime(self.__format)
                val = st[i][0][1]
                drt = st[i][1]
                tmp['d'] = dat
                tmp['v'] = val
                tmp['r'] = drt
                tmp['num'] = i
                ret.append(tmp)
            return ret
        lastdt = eliot['st'][eliot['num']][0][0]
        s = []
        f = show(eliot)
        if len(eliot['son']) > 0:
            s = show(eliot['son'])
            tmp = eliot['son']
            lastdt = tmp['st'][tmp['num']][0][0]
        ret['f']   = f
        ret['s']   = s
        gdp = {}
        if self.__gdp is not None:
            gdp = self.__gdp[3]
        ret['gdp'] = gdp

        if len(self.__tmp_eliotw5) > 0:
            tmpeliot = self.__tmp_eliotw5[-1]
            if tmpeliot['st'][tmpeliot['num']][0][0] > lastdt:
                t = show(tmpeliot)
                ret['g'] = t
        return ret
        
    # 艾略特标准五浪结构解析
    def EliotWave5(self):
        dateTime = self.__nowdt
        line = self.EliotLine(dateTime)
        if line is not None:
            if self.__update == 1:
                self.EliotAddLine(line, self.__eliotw5)
            if len(self.__eliotw5) > 0:
                eliot = self.__eliotw5[-1]

                ret = self.EliotUpRT(eliot)
                self.__eliotw5[-1] = ret

                self.__eliot = self.EliotShow(dateTime, ret)

    # 艾略特一笔的定义
    def EliotLine(self, dateTime):
        line = None
        if len(self.__fpeek) == 0 and len(self.__fvalley) == 0:
            return line
        if len(self.__fpeek) > 0 and len(self.__fvalley) == 0:
            peek0 = self.__fpeek[0]
            line = (peek0, self.__direct)
        if len(self.__fpeek) == 0 and len(self.__fvalley) > 0:
            vall0 = self.__fvalley[0]
            line = (vall0, self.__direct)
        if len(self.__fpeek) > 0 and len(self.__fvalley) > 0:
            peek0 = self.__fpeek[0]
            vall0 = self.__fvalley[0]
            if self.__direct == -1:
                line = (vall0, self.__direct)
            else:
                line = (peek0, self.__direct)
        return line
   
    # 增加一笔
    def EliotAddLine(self, line, eliotw5):
        eliot = dict()
        if len(eliotw5) > 0:
            eliot = eliotw5[-1]
        if len(eliot) == 0:
            tmp    = dict()
            tmp[0] = line
            eliot['st']  = tmp
            eliot['num'] = 0
            eliot['son'] = dict()
            eliotw5.append(eliot)
        else:
            if len(eliot['son']) > 0:
                check = self.EliotCheck(eliot['son'], line)
                self.EliotAdd2Son(eliot, line, check, eliotw5)
            else:
                check = self.EliotCheck(eliot, line)
                eliot = self.EliotAdd2Dad(eliot, line, check, eliotw5)
            eliot = self.EliotTrans(eliot)
            eliotw5[-1] = eliot

    # 浪型更新RealTime
    def EliotUpRT(self, eliot):
        ret = eliot
        son = eliot['son']
        if len(son) > 0:
            gdp = self.__gdp[3]
            if eliot['st'][0][1] == 1 and gdp['v'] > son['fz2'][0][1]:
                ret = eliot['son']
            if eliot['st'][0][1] == -1 and gdp['v'] < son['fz2'][0][1]:
                ret = eliot['son']
        return ret

    # 子浪转主浪
    def EliotTrans(self, eliot):
        ret = eliot
        son = eliot['son']
        if len(son) > 0:
            last = son['st'][son['num']][0][1]
            if son['st'][0][1] == -1 and son['fz1'][0][1] < last:
                ret = eliot['son']
            if son['st'][0][1] == 1 and son['fz1'][0][1] > last:
                ret = eliot['son']
            # 加入新的反转，子浪破了主浪的结构
            if eliot['st'][0][1] == 1 and last > son['fz2'][0][1]:
                ret = eliot['son']
            if eliot['st'][0][1] == -1 and last < son['fz2'][0][1]:
                ret = eliot['son']
        return ret

    # 加入主浪
    def EliotAdd2Dad(self, eliot, line, check, eliotw5):
        num = eliot['num']
        son = eliot['son']

        if check == 3:
            eliot['st'][num]  = line

        # 反转形成新形态
        if check == 2:
            newe = dict()
            tmp  = dict()
            
            index = num
            if num > 1:
                if line[1] == eliot['st'][num][1]:
                    index = num - 1
            tmp[0] = eliot['st'][index]
            tmp[1] = line
            newe['st']  = tmp 
            newe['num'] = 1
            newe['son'] = dict()
            eliotw5.append(newe)
            return newe

        if check == 1:
            eliot['num']          = num + 1
            eliot['st'][num + 1]  = line

        # 形成子浪
        if check == 0:
            if line[1] == eliot['st'][num][1]:
                self.__logger.log(logging.ERROR, 'Drop_line: %s %s', \
                                  line[0][0].strftime(self.__format), line[0][1])
            else:
                tmp = dict()
                tmp[0] = eliot['st'][num - 1]
                tmp[1] = eliot['st'][num]
                tmp[2] = line
                son['st']  = tmp
                son['num'] = 2
                son['fz1']  = eliot['st'][num - 2]
                son['fz2']  = eliot['st'][0]
                son['son'] = dict()
        eliot['son'] = son
        return eliot

    # 加入子浪
    def EliotAdd2Son(self, eliot, line, check, eliotw5):
        son = eliot['son']
        if check == 0:
            num    = son['num']
            tmp0   = son['st'][num]
            if tmp0[1] == -1 and line[0][1] < tmp0[0][1]:
                son['st'][num] = line
            if tmp0[1] == 1 and line[0][1] > tmp0[0][1]:
                son['st'][num] = line
            # if change == 0 and self.__recursion < 1:
            #     self.__recursion = self.__recursion + 1
            #     self.EliotAddLine(line, self.__tmp_eliotw5)
            #     if len(self.__tmp_eliotw5) > 0:
            #         tmp = self.__tmp_eliotw5[-1]
            #         ret = self.EliotUpRT(tmp)
            #         self.__tmp_eliotw5[-1] = ret
            #     self.__recursion = self.__recursion - 1 
            eliot['son'] = son

        # 更新子浪
        if check == 1:
            son['num']            = son['num'] + 1
            son['st'][son['num']] = line
            eliot['son'] = son
            num = eliot['num']

            # 如果子浪形成新高或者新低更新父浪
            if eliot['st'][0][1] == 1 and son['st'][0][1] == -1 \
                    and eliot['st'][num][1] == 1 and line[1] == 1 \
                    and line[0][1] > eliot['st'][num][0][1]:
                eliot['st'][num] = line
            if eliot['st'][0][1] == -1 and son['st'][0][1] == 1 \
                    and eliot['st'][num][1] == -1 and line[1] == -1 \
                    and line[0][1] < eliot['st'][num][0][1]:
                eliot['st'][num] = line

        if check == 2:
            sonlast = son['st'][son['num']]
            eliot['st'][eliot['num']] = sonlast
            eliot['son'] = dict()
            check = self.EliotCheck(eliot, line)
            eliot = self.EliotAdd2Dad(eliot, line, check, eliotw5)

        if check == 4:
            maxv = -1
            minv = 100
            adds = None
            num  = son['num']
            for i in range(0, num + 1):
                if son['st'][i][1] == -1 and son['st'][i][0][1] < minv:
                    minv = son['st'][i][0][1]
                    adds = son['st'][i]
                if son['st'][i][1] == 1 and son['st'][i][0][1] > maxv:
                    maxv = son['st'][i][0][1]
                    adds = son['st'][i]
            eliot['st'][eliot['num']] = adds
            eliot['son'] = dict()
            check = self.EliotCheck(eliot, line)
            eliot = self.EliotAdd2Dad(eliot, line, check, eliotw5)
        return 1

    # 艾略特检测
    def EliotCheck(self, eliot, line):
        ret = 0
        st  = eliot['st']
        if len(st) < 2:
            ret = 1
        else:
            index = eliot['num'] - 1
            # 新的一比时间错误，放弃
            if line[0][0] <= st[index + 1][0][0]:
                ret = -1
                return ret

            # 背离
            if self.__beili == -1 and line[0][0] > st[index + 1][0][0]:
                if line[1] == st[index + 1][1]:
                    if line[1] == -1 and line[0][1] < st[index + 1][0][1]:
                        ret = 3
                    if line[1] == 1 and line[0][1] > st[index + 1][0][1]:
                        ret = 3
                    return ret

            if st[0][1] == 1 and line[0][1] <= st[index][0][1]:
                ret = 1
            if st[0][1] == -1 and line[0][1] >= st[index][0][1]:
                ret = 1
            # 新加入一笔导致当前浪破位, 结束当前浪，反转
            if index == 0 and st[index + 1][1] == 1 and line[0][1] < st[0][0][1]:
                ret = 2
            if index == 0 and st[index + 1][1] == -1 and line[0][1] > st[0][0][1]:
                ret = 2
            if index > 0 and st[0][1] == 1 and st[index + 1][1] == -1 and line[0][1] > st[index][0][1] \
                    and st[index + 1][0][1] < st[index - 1][0][1]:
                ret = 2
            if index > 0 and st[0][1] == -1 and st[index + 1][1] == 1 and line[0][1] < st[index][0][1] \
                    and st[index + 1][0][1] > st[index][0][1]:
                ret = 2

            # 子浪破位，下降浪找低点，上升浪找高点
            if index > 0 and st[0][1] == -1 and line[0][1] < st[0][0][1]:
                ret = 4
            if index > 0 and st[0][1] == 1 and line[0][1] > st[0][0][1]:
                ret = 4
        return ret

    # 三种最基本的走势定义
    #  1 -- 上升
    #  2 -- 盘整
    #  3 -- 下降
    def basicQS(self, tup, direct):
        ret = 0
        peek0 = tup[0]; speek0 = peek0.strftime(self.__format)
        peek1 = tup[1]; speek1 = peek1.strftime(self.__format)
        vall0 = tup[2]; svall0 = vall0.strftime(self.__format)
        vall1 = tup[3]; svall1 = vall1.strftime(self.__format)

        high0 = self.__high[peek0]; high1 = self.__high[peek1]
        low0 = self.__low[vall0]; low1 = self.__low[vall1]

        zhouqi = None
        struct = None
        timegd = None
        if direct == -1:
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

        if direct == 1:
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
