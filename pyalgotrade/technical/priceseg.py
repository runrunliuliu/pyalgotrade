from pyalgotrade import technical
from pyalgotrade import bar
from pyalgotrade import dataseries
from pyalgotrade.utils import collections
from pyalgotrade.utils import qsLineFit 
from pyalgotrade.dataseries import bards
from pyalgotrade.technical import ma
from pyalgotrade.technical import macd
from pyalgotrade.technical import indicator 
from pyalgotrade.technical import sar 
from array import array
from utils import utils
from collections import OrderedDict
import numpy as np
import pyalgotrade.talibext.indicator as ta
from pyalgotrade.signals import mavalid 


class MacdSegEventWindow(technical.EventWindow):

    def __init__(self, BarSeries, windows, inst, useAdjustedValues):
        assert(windows > 0)
        technical.EventWindow.__init__(self, windows, dtype=object)
        self.__windows = windows
        self.__inst    = inst 
        self.__priceDS = BarSeries.getCloseDataSeries()
        self.__macd = macd.MACD(self.__priceDS, 12, 26, 9, flag=0)

        self.__mapma = {
            5: 0,
            10: 1,
            20: 2,
            30: 3,
            60: 4,
            90: 5,
            120:6,
            250:7 
        }

        self.__indicator = indicator.IndEventWindow(inst)
        self.__sar = sar.SAREventWindow(8)

        self.__bars = BarSeries
        self.__period = None

        self.__prevmacd    = None 
        self.__prevXTscore = None

        self.__fix    = 1 
        self.__beili  = 0 
        self.__vbeili = 0 

        self.__gfbeili = (-1, -1)

        self.__xtTriangle = None 
        self.__roc = None
        self.__cxshort = None
        self.__NBS = None

        self.__vbused = set()
        
        # Record Trading Days FOR ZHOUQI theory
        self.__zq   = 0
        self.__dtzq  = OrderedDict() 
        self.__dtmas = OrderedDict()

        self.__qsfilter  = set() 
        self.__qsfit     = {}
        self.__datelow   = {}
        self.__datehigh  = {}
        self.__dateclose = {}
        self.__dateopen  = {}

        self.__fvalley = []
        self.__fpeek   = []
        self.__desline = OrderedDict()
        self.__incline = OrderedDict()
        
        self.__nowdesline = OrderedDict()
        self.__nowincline = OrderedDict()

        self.__gd       = OrderedDict()
        self.__LFVbeili = OrderedDict()
        self.__LFPbeili = OrderedDict()
        self.__hlcluster = []
        self.__nowgd   = None
        self.__nowhist = None

        self.__ftDes = set()
        self.__ftInc = set()

        self.__LongPeriod = collections.ListDeque(5)

        self.__now_zhicheng = []
        self.__now_tupo     = []
        self.__now_zuli     = []
        
        self.__hist_zhicheng = collections.ListDeque(5)
        self.__hist_tupo     = collections.ListDeque(5)
        self.__hist_zuli     = collections.ListDeque(5)

        self.__inchist  = []
        self.__incdate  = []
        self.__inchigh  = []
        self.__inclow   = []
        self.__incclose = []
        self.__inchist_list = collections.ListDeque(5)
        self.__incdate_list = collections.ListDeque(5)
        self.__inchigh_list = collections.ListDeque(5)
        self.__inclow_list  = collections.ListDeque(5)
        self.__incclose_list  = collections.ListDeque(5)

        self.__deshist  = []
        self.__desdate  = []
        self.__deshigh  = []
        self.__deslow   = []
        self.__desclose = []
        self.__deshist_list  = collections.ListDeque(5)
        self.__desdate_list  = collections.ListDeque(5)
        self.__deshigh_list  = collections.ListDeque(5)
        self.__deslow_list   = collections.ListDeque(5)
        self.__desclose_list = collections.ListDeque(5)
        
        self.__posdate  = []
        self.__poshist  = []
        self.__posclose = []
        self.__poshigh  = []
        self.__poshist_list = collections.ListDeque(3)
        self.__posdate_list = collections.ListDeque(3)
        self.__poshigh_list = collections.ListDeque(3)

        self.__neghist  = []
        self.__negdate  = []
        self.__negclose = []
        self.__neglow   = []
        self.__neghist_list = collections.ListDeque(3)
        self.__negdate_list = collections.ListDeque(3)

        self.__dropout  = []
        self.__observed = {}

        self.__qsxt    = []

        self.__preval  = None
        self.__preqs   = None
        self.__prehist = None
        self.__preret  = None

        self.__direct = None
        self.__gdval  = None
        self.__gddt   = None

        self.__QUSHI   = (-1, 0.0)
        self.__DTBORAD = None
        self.__chaodie = 0
        self.__qScore  = collections.ListDeque(5)
        self.__MAscore5  = ma.SMAEventWindow(5)
        self.__MAscore10 = ma.SMAEventWindow(10)

    def addHist(self, hist, dateTime, close, low, high):
        ret    = 1
        change = 0 
        if self.__prehist is None:
            if hist < 0:
                self.__neghist.append(hist)
                self.__negdate.append(dateTime)
                self.__neglow.append(low)
                self.__negclose.append(close)
                ret = -1
            if hist >= 0:
                self.__poshist.append(hist)
                self.__posdate.append(dateTime)
                self.__poshigh.append(high)
                self.__posclose.append(close)
        else:
            if self.__prehist * hist < 0:
                change = 1
                if hist < 0:
                    self.__poshist_list.append(self.__poshist)
                    self.__posdate_list.append(self.__posdate)
                    self.__poshigh_list.append(self.__poshigh)
                   
                    self.__neghist = []
                    self.__negdate = []
                    self.__neglow  = []
                    self.__negclose = []
                    self.__neghist.append(hist)
                    self.__negdate.append(dateTime)
                    self.__neglow.append(low)
                    self.__negclose.append(close)
                    ret = -1
                else:
                    self.__neghist_list.append(self.__neghist)
                    self.__negdate_list.append(self.__negdate)

                    self.__poshist = []
                    self.__posdate = []
                    self.__poshigh = []
                    self.__posclose = []
                    self.__poshist.append(hist)
                    self.__posdate.append(dateTime)
                    self.__poshigh.append(high)
                    self.__posclose.append(close)
            else:
                if hist < 0:
                    self.__neghist.append(hist)
                    self.__negdate.append(dateTime)
                    self.__neglow.append(low)
                    self.__negclose.append(close)
                    ret = -1
                if hist >= 0:
                    self.__poshist.append(hist)
                    self.__posdate.append(dateTime)
                    self.__poshigh.append(high)
                    self.__posclose.append(close)
        return (ret, change)

    # Find BeiLi
    def findBeiLi(self, dateTime, flag):
        # Vally BeiLi 
        if flag == 1:
            if self.__datelow[dateTime] < self.__datelow[self.__gddt]:
                update = (dateTime, self.__datelow[dateTime])
                if self.__gddt in self.__LFVbeili:
                    tmp  = self.__LFVbeili[self.__gddt]
                    plow = tmp[1]
                    if plow < self.__datelow[dateTime]:
                        update = tmp
                self.__LFVbeili[self.__gddt] = update 
        # Peek Beili
        if flag == -1:
            if self.__datehigh[dateTime] > self.__datehigh[self.__gddt]:
                update = (dateTime, self.__datehigh[dateTime])
                if self.__gddt in self.__LFPbeili:
                    tmp = self.__LFPbeili[self.__gddt]
                    phigh = tmp[1]
                    if phigh > self.__datehigh[dateTime]:
                        update = tmp
                self.__LFPbeili[self.__gddt] = update 

    def parsePrevHistDay(self, ret, change, dateTime):
        now_val = None
        now_dt  = None
        if len(self.__poshist_list) > 0 and len(self.__neghist_list) > 0:
            if ret == 1:
                # prev = np.array(self.__neghist)
                prev = np.array(self.__neglow)
                if len(prev) == 0:
                    self.__direct = None
                    return (now_val, now_dt)
                pmin_hist = prev.min()
                pmin_date = self.__negdate[prev.argmin()]
                if change == 1:
                    self.__direct = -1
                    self.__gdval  = pmin_hist
                    self.__gddt   = pmin_date
                now = np.array(self.__poshigh)
                now_val = now.max()
                now_dt  = self.__posdate[now.argmax()]

            if ret == -1:
                # prev = np.array(self.__poshist)
                prev = np.array(self.__poshigh)
                if len(prev) == 0:
                    return (gd_val, gd_dt)
                pmax_hist = prev.max()
                pmax_date = self.__posdate[prev.argmax()]
                if change == 1:
                    self.__direct = 1
                    self.__gdval  = pmax_hist 
                    self.__gddt   = pmax_date
                now = np.array(self.__neglow)
                now_val = now.min()
                now_dt  = self.__negdate[now.argmin()]
            # Find BeiLi point
            self.findBeiLi(dateTime, ret)
            # Find GeFeng BeiLi 
            self.__gfbeili = self.findGFBeiLi(dateTime, ret)

        return (now_val, now_dt)

    # 当前Bar所处的趋势状态,日K线最近的2峰2谷
    # ---------------------------------------------------
    # 1. 趋势向下
    # 101 峰和谷连线皆slope < -0.001, slope(峰) >> slope(谷), 下收敛三角
    # 102 峰和谷连线皆slope < -0.001, slope(峰) << slope(谷), 下扩张三角
    # 103 峰和谷连线皆slope < -0.001, slope(峰) ~ slope(谷), 下平行通道
    # 104 峰连线abs(slope) < 0.001, 谷连线slope<-0.001, 下扩张三角II
    # 105 谷连线abs(slope) < 0.001, 峰连线slope<-0.001, 下支撑三角
    # 2. 趋势盘整
    # 201 峰和谷连线皆abs(slope) < 0.001, 横盘矩形整理
    # 202 峰连线slope < -0.001, 谷连线slope > 0.001, 收敛三角整理区 
    # 3. 趋势向上
    # 301 峰和谷连线皆slope > 0.001, slope(峰) << slope(谷), 上收敛三角
    # 302 峰和谷连线皆slope > 0.001, slope(峰) >> slope(谷), 上扩张三角
    # 303 峰和谷连线皆slope > 0.001, slope(峰) ~ slope(谷), 上平行通道
    # 304 谷连线abs(slope) < 0.001, 峰连线slope > 0.001, 上扩张三角II
    # 305 峰连线abs(slope) < 0.001, 谷连线slope > 0.001, 上支撑三角
    #
    def figureQS(self, dateTime):
        xingtai, vret, vscore, nvpos, pret, pscore, nppos, slope = (-1.0,) * 8 
        if len(self.__fvalley) < 2 or len(self.__fpeek) < 2:
            return (xingtai, vret, vscore, nvpos, pret, pscore, nppos, slope)
        def compute(index, dateTime):
            x0 = index[1][0]
            y0 = index[1][1]
            x1 = index[0][0]
            y1 = index[0][1]
            start = self.__dtzq[x0]
            end   = self.__dtzq[x1]
            qfit = qsLineFit.QsLineFit(start, y0, end, y1)
            qfit.setDesc(x0, x1)
            position = qfit.compute(self.__dtzq[dateTime])
            nextpos  = qfit.compute(self.__dtzq[dateTime] + 1)

            high  = (position / self.__datehigh[dateTime]) - 1.0
            low   = (position / self.__datelow[dateTime]) - 1.0
            close = (position / self.__dateclose[dateTime]) - 1.0

            (ret, score) = utils.positionScore(high, low, close)

            return (y0, y1, qfit.getSlope(), position, nextpos, ret, score)

        (v0, v1, vslope, vpos, nvpos, vret, vscore) = compute(self.__fvalley, dateTime)
        (p0, p1, pslope, ppos, nppos, pret, pscore) = compute(self.__fpeek, dateTime)
        pdv = abs(pslope) / (abs(vslope) + 0.0000000001)
        vdp = abs(vslope) / (abs(pslope) + 0.0000000001)

        pyz = 0.0005
        nyz = -0.0005
        if vslope < nyz and pslope < nyz and pdv > 1.01:
            xingtai = 101
        if vslope < nyz and pslope < nyz and vdp > 1.01:
            xingtai = 102
        if vslope < nyz and pslope < nyz and abs(vdp - 1.0) < 0.01 and abs(pdv - 1.0) < 0.01:
            xingtai = 103
        if abs(pslope) < pyz and vslope < nyz:
            xingtai = 104
        if abs(vslope) < pyz and pslope < nyz:
            xingtai = 105
        if abs(vslope) < pyz and abs(pslope) < pyz:
            xingtai = 201
        if vslope > pyz and pslope < nyz:
            xingtai = 202
        if vslope > pyz and pslope > pyz and vdp > 1.01:
            xingtai = 301
        if vslope > pyz and pslope > pyz and pdv > 1.01:
            xingtai = 302
        if vslope > pyz and pslope > pyz and abs(vdp - 1.0) < 0.01 and abs(pdv - 1.0) < 0.01:
            xingtai = 303
        if abs(vslope) < pyz and pslope > pyz:
            xingtai = 304
        if abs(pslope) < pyz and vslope > pyz:
            xingtai = 305

        vscore = "{:.4f}".format(vscore)
        pscore = "{:.4f}".format(pscore)

        nvpos = "{:.2f}".format(nvpos)
        nppos = "{:.2f}".format(nppos)

        slope = "{:.4f}".format(vslope + pslope)

        if len(self.__qsxt) == 0:
            self.__qsxt.append(xingtai)
        else:
            if self.__qsxt[-1] != xingtai:
                self.__qsxt.append(xingtai)
        # print 'DEBUG', dateTime, xingtai, vret, vscore, nvpos, pret, pscore, nppos, vslope, pslope
        return (xingtai, vret, vscore, nvpos, pret, pscore, nppos, slope)

    def clusterGD(self, dateTime, sdf):
        self.__hlcluster = []
        clusters = {}
        ncts = 0
        for i in range(0, len(sdf) + 1):
            # BUG, LAST index might be missed
            if i == len(sdf):
                if ncts not in clusters:
                    clusters[ncts] = [sdf[i-1]] 
                break
            tmp = []
            if ncts in clusters:
                tmp = clusters[ncts]
            else:
                tmp.append(sdf[i])
                clusters[ncts] = tmp 
                continue
            bf = np.median(tmp)
            if (sdf[i] / bf) < 1.01:
                tmp.append(sdf[i])
                clusters[ncts] = tmp 
            else:
                ncts = ncts + 1
        for i in range(0, ncts + 1):
            self.__hlcluster.append((i,np.mean(clusters[i]), np.median(clusters[i]), np.std(clusters[i]), len(clusters[i])))

    def filterGD(self, indexs, flag):
        res = []
        cnt = 1
        for p in indexs:
            if cnt == 1:
                res.append(p)
                cnt = cnt + 1
                continue
            pre   = p[2]
            nex   = p[3]
            # Peek Point
            if flag == 1:
                if nex > pre * 0.618 * 0.618:
                    res.append(p)
            # Valley point
            if flag == -1:
                if nex > pre * 0.618 * 0.618 or nex > 0.20:
                    res.append(p)
            cnt = cnt + 1
        return res
    
    def pressDesQSLine(self, dateTime, twoline):
        qsfit = twoline[3]
        desdiff = []
        prs = set() 
        cnt = -1 
        for qs in qsfit:
            diff = 0 
            cnt  = cnt + 1
            x1 = qs.getX1()
            above = 0
            below = 0
            for i in range(1, len(self.__bars)):
                nbar = self.__bars[-1 * i]
                ndt  = nbar.getDateTime()
                nind = self.__dtzq[ndt]
                if i == 1:
                    high = nbar.getHigh()
                    diff = (qs.compute(nind) - high) / high
                # ignor Bars effect if Its FAR AWAY from QUSHI Line
                if nbar.getClose() < qs.compute(nind) * 0.80:
                    continue
                if nind == x1:
                    break
                if nbar.getClose() <= qs.compute(nind):
                    below = below + 1
                else:
                    above = above + 1
            desdiff.append(diff)
            prop = below / (above + below + 0.00000000000001)
            if abs(diff) < 0.02:
                prs.add((cnt, prop))
        return (desdiff, prs) 

    # Future Peek or Valley cross the line or NOT
    def breakIncQSLine(self, dateTime, twoline):
        qsfit = twoline[1]
        # 1: support
        # 2: press
        sup = set() 
        prs = set() 
        cnt = -1 
        for qs in qsfit:
            cnt = cnt + 1
            x1 = qs.getX1()
            above = 0
            below = 0
            for i in range(1, len(self.__bars)):
                nbar = self.__bars[-1 * i]
                ndt  = nbar.getDateTime()
                nind = self.__dtzq[ndt]
                # ignor Bars effect if Its FAR AWAY from QUSHI Line
                if nbar.getClose() > qs.compute(nind) * 1.20:
                    continue

                if nind == x1:
                    break
                if nbar.getClose() >= qs.compute(nind):
                    above = above + 1
                else:
                    below = below + 1
            prop = above / (above + below + 0.00000000000001)
            if prop > 0.8:
                sup.add(cnt)
            if prop < 0.5 and prop > 0.0:
                prs.add(cnt)
        return (sup, prs) 

    def scoreQSLine(self, flag, neighbors, lastvex):
        for point in neighbors:
            ndate = point[0]; nval  = point[1]
            lines = None
            if flag == 1 and ndate in self.__desline:
                lines = self.__desline[ndate]
            if flag == -1 and ndate in self.__incline:
                lines = self.__incline[ndate]
            if lines is None:
                continue
            destmp = []; inctmp = []
            indexes = []  
            indexes.extend(self.__fvalley)
            indexes.extend(self.__fpeek)
            for tups in lines: 
                if tups in self.__qsfilter:
                    continue
                y0 = tups[1]; y1 = tups[3]
                # x0 = tups[0]; 
                # diff = self.__dtzq[ndate] - self.__dtzq[x0]
                # 1. remove EXPIRE QUSHI Line 
                if flag == 1 and y0 > nval * 0.95 and y1 > nval * 0.95:
                    if ndate in self.__nowdesline:
                        destmp = self.__nowdesline[ndate]
                    destmp.append(tups)
                    self.__nowdesline[ndate] = destmp
                if flag == -1 and y0 < lastvex[1] and y1 <= lastvex[1]:
                    if ndate in self.__nowincline:
                        inctmp = self.__nowincline[ndate]
                    inctmp.append(tups)
                    self.__nowincline[ndate] = inctmp

    # QuShi Fit to discard some useless lines
    def qsFit(self, tups, flag):
        x0 = tups[0]; y0 = tups[1]; x1 = tups[2]; y1 = tups[3]
        start = self.__dtzq[x0]; end = self.__dtzq[x1]
        qfit = None
        if x1 not in self.__qsfit:
            qfit = qsLineFit.QsLineFit(start, y0, end, y1)
            qfit.setDesc(x0, x1)
        else:
            qfit = self.__qsfit[x1]
        lines = []
        if flag == 1 and x1 in self.__desline:
            lines = self.__desline[x1]
        if flag == -1 and x1 in self.__incline:
            lines = self.__incline[x1]
        qsfilter = 0
        for l in lines:
            x = self.__dtzq[l[0]]
            y = qfit.compute(x)
            if (l[1] - y) * flag > 0:
                qsfilter = 1
                break
        if qsfilter == 1:
            self.__qsfilter.add(tups)
        return qfit

    def connectPoint(self, date, val, lastvex, flag):
        tmp  = []
        tups = (date, val, lastvex[0], lastvex[1])
        # Connect Higher Peek point to plot descending Line
        if flag == 1 and (val - lastvex[1]) / lastvex[1] > 0.05:
            self.qsFit(tups, flag)
            if lastvex[0] in self.__desline:
                tmp = self.__desline[lastvex[0]]
            tmp.append(tups)
            self.__desline[lastvex[0]] = tmp
        # Connect Lower Valley point to plot increasing Line
        if flag == -1 and (lastvex[1] - val) / val > 0.01:
            self.qsFit(tups, flag)
            if lastvex[0] in self.__incline:
                tmp = self.__incline[lastvex[0]]
            tmp.append(tups)
            self.__incline[lastvex[0]] = tmp

    def add2neighbor(self, item, flag):
        fl = 0
        val = item[1]
        if flag == -1:
            if val > self.__nowBar.getClose():
                fl = 1
        if flag == 1:
            if val < self.__nowBar.getClose():
                fl = 1
        return fl

    # Long Time QuChi Line 
    def pairVetex(self, lists, flag):
        if len(lists) < 2:
            return None
        if flag == 1:
            self.__nowdesline = OrderedDict()
        if flag == -1:
            self.__nowincline = OrderedDict()
        neighbors = []
        nneighbor = 0
        lastvex = lists[0]
        neighbors.append(lastvex)
        for i in range(1,len(lists)):
            item = lists[i] 
            date = item[0]; val = item[1]
            self.connectPoint(date, val, lastvex, flag) 
            fl = self.add2neighbor(item, flag)
            if fl == 0 and nneighbor < 3:
                neighbors.append(item)
                nneighbor = nneighbor + 1
        # Score Desending and Ascending Line
        self.scoreQSLine(flag, neighbors, lastvex)

    # Identify Peek and Valley Index
    # connect important index to horizon line or tongdao
    def parseGD(self, dateTime, ngd, nval):
        if nval is None:
            return
        valley = [] 
        peek   = []
        sdf   = []
        index = []
        for k,v in self.__gd.iteritems():
            index.append((k,v))
            sdf.append(v)
        index.append((ngd, nval))
        self.clusterGD(dateTime, np.sort(sdf))
        for i in range(2,len(index)):
            now = index[-1 * i]
            pre = index[-1 * (i + 1)]
            nex = index[-1 * (i - 1)]
            if now[1] < nex[1] and now[1] < pre[1]:
                tups = (now[0], now[1], (pre[1] - now[1]) / now[1], (nex[1] - now[1]) / now[1])
                valley.append(tups)
            if now[1] > nex[1] and now[1] > pre[1]:
                tups = (now[0], now[1], (now[1] - pre[1]) / now[1], (now[1] - nex[1]) / now[1])
                peek.append(tups)

        self.__fvalley = self.filterGD(valley, -1)
        self.__fpeek   = self.filterGD(peek, 1)
        if self.__direct == 1:
            self.pairVetex(self.__fpeek, 1)
        if self.__direct == -1 or self.__beili == -1:
            self.pairVetex(self.__fvalley, -1)

    def setPeriod(self, value):
        period = 'day'
        if value.getFrequency() == bar.Frequency.WEEK:
            period = 'week'
        if value.getFrequency() == bar.Frequency.MONTH:
            period = 'month'
        return period

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        self.__macd.onNewValue(self.__priceDS, dateTime, value.getClose())

        self.__indicator.onNewValue(dateTime, value)
        self.__sar.onNewValue(dateTime, value)

        self.__period = self.setPeriod(value)
        self.__nowBar = value
        self.__datelow[dateTime]   = value.getLow()
        self.__datehigh[dateTime]  = value.getHigh()
        self.__dateclose[dateTime] = value.getClose()
        self.__dateopen[dateTime]  = value.getOpen()

        self.__zq = self.__zq + 1
        self.__dtzq[dateTime] = self.__zq

        (self.__fts, self.__mas) = self.__indicator.getValue()
        self.__dtmas[dateTime] = self.__mas
        change        = 0
        self.__beili  = 0 
        self.__vbeili = 0 
        nwprice = None
        if self.__macd[-1] is not None:
            hist = self.__macd.getHistogram()[-1]
            (ret, change) = self.addHist(hist, dateTime, value.getClose(), value.getLow(), value.getHigh()) 
            (now_val, now_dt) = self.parsePrevHistDay(ret, change, dateTime)
            if self.__gddt is not None:
                gdprice = self.__datelow[self.__gddt]
                nwprice = value.getLow()
                # dirct == 1 means NOW--MACD < 0 and GD is peek
                if self.__direct == 1:
                    gdprice = self.__datehigh[self.__gddt]
                    nwprice = value.getHigh()

                # Fix valley point based on BeiLi 
                # UPDATE: It's not NECESSARY for CHANGE to be happend
                self.updateGD(now_dt)
                if change == 1:
                    self.__gd[self.__gddt] = gdprice

                self.__nowgd   = now_dt
                self.__nowhist = hist
            if change == 1 or self.__beili == -1:
                self.parseGD(dateTime, self.__nowgd, nwprice) 

            # VBeiLi Buy Point
            self.__vbeili = self.setVBeiLiBuyPoint(dateTime) 
            twoline       = self.computeBarLinePosition(dateTime, value)
            hline         = self.computeHLinePosition(dateTime, value)
            (sup, prs)    = self.breakIncQSLine(dateTime, twoline)
            (ndiff, npres) = self.pressDesQSLine(dateTime, twoline)

            # 获取当前的整体的趋势
            qsxingtai = self.figureQS(dateTime)

            # 上升三角形态
            self.__xtTriangle = self.xtTriangle(dateTime, twoline, hline, sup, prs)

            # HIST趋势判定及与均线的关系
            (qsgd, qshist) = self.qsHistMAs(dateTime, hist, value)

            # 颈线形态
            self.xtNeckLine(dateTime, twoline, hline, value, now_val, now_dt)

            self.add2observed(dateTime, now_dt, value)

            self.__roc     = self.__fts[1] 
            self.__cxshort = self.__fts[3]
            mafeature      = self.__fts[4]
            klines         = self.__fts[5]
            nDIF = self.__macd[-1] 
            yDIF = self.__macd[-2]
            nDEA = self.__macd.getSignal()[-1]
            yDEA = self.__macd.getSignal()[-2]
            cDIF = 0
            cDEA = 0
            if nDIF is not None and yDIF is not None:
                cDIF = "{:.4f}".format(nDIF - yDIF)
                cDEA = "{:.4f}".format(nDEA - yDEA)

            prext = 1024 
            if len(self.__qsxt) > 1:
                prext = self.__qsxt[-2]
            
            # 非上升趋势的跳空低开,视为趋势的恶化，空仓
            tkdk = 1024
            tkdf = 1024
            if klines[0] < 0.0 and self.__direct == 1:
                tkdk = "{:.4f}".format(klines[0])
                tkdf = "{:.4f}".format(klines[1])
            self.__cxshort = (cDIF, cDEA) + self.__cxshort + \
                self.__gfbeili + qsxingtai + \
                mafeature + (prext,) + \
                (tkdk,tkdf)

            self.filter4Show(dateTime, twoline, value)

            # 长周期指标
            (lret, sarval) = self.LongPeriod(dateTime, value)
            
            buy = self.NBuySignal(dateTime, qsgd, qshist, lret, sarval, value)
            self.__NBS = (buy, self.__indicator.getMAscore()[-1][0])

            # Keep Record
            self.__prehist = hist 
            self.__preval  = value

    def LongPeriod(self, dateTime, value):
        madirect   = self.__indicator.getMAdirect() 
        mascore    = self.__indicator.getMAscore()
        sarval     = self.__sar.getValue()
        # 结合SAR的复杂进场指标，T日指标和T+1日指标(预测)
        # --------- 趋势反转 ----------------
        # 反转信号: SAR绿翻红 or macd下跌变上升 or ....
        # 辅助验证指标: 
        # 1. MA score > 0 or 大幅增加
        # 2. MAs形态较好, 长期均线朝上或者下行曲率微弱
        # 3. 收盘价距离均线, 长期均线在收盘价之下, 短期均线5,10,20距离接近
        # 4. 持续上涨则平量，近期涨幅(周线、月线)不能过大
        # 介入时机: 日线突破前期平台，再回踩动作形成时介入
        # [5, 10, 20, 30, 60, 90, 120, 250]
        # output:
        # 1. ret, 月周线上-1, 0, 1三种状态，1买入观察, 0持有, -1卖出观察
        # 2. press, 压力位，月周发出买入观察信号，则T＋1交易过程中必须突破压力位 
        # 3. support, 支撑位, 月周发出卖出观察信号，则T＋1交易过程中跌破支撑位位 
        ret = 0
        if len(mascore) > 1 and mascore[-1][0] > 100 and abs(mascore[-1][0] / mascore[-2][0]) > 0.618:
            ret = 1
            if self.__period == 'month':
                for i in range(3, 8):  
                    if len(madirect) > i and madirect[i] is not None and madirect[i] < 0:
                        ret = -1
                        break
            if self.__period == 'week':
                for i in range(4, 8):  
                    if len(madirect) > i and madirect[i] is not None and madirect[i] < 0:
                        ret = -1
                        break
        return (ret, sarval)

    def baodie(self, dateTime, klines, hline):
        if self.__direct == 1 and klines[2] == 1:
            print dateTime, 'baodie', hline

    def findGFBeiLi(self, dateTime, flag):
        nfast = self.__macd.getFast()
        nslow = self.__macd.getSlow()
        nDEA = self.__macd.getSignal()[-1]
        ret = (-1, -1)
        # 顶背离有效概率比较高
        if flag == 1:
            if len(self.__poshist_list) > 1: 
                gf1high = np.array(self.__poshigh_list[-1])
                nowhigh = np.array(self.__poshigh)
                gf = np.array(self.__poshist_list[-1])
                nw = np.array(self.__poshist)
                
                price_rate  = nowhigh.max() / gf1high.max()
                hist_rate = gf.max() / nw.max()
                if price_rate > 0.90 and hist_rate > 2.0:
                    dcprice = self.fakeCross(dateTime, nfast, nslow, nDEA)
                    dcprice = "{:.4f}".format(dcprice)
                    price_rate = (1.0 if price_rate < 1.0 else price_rate)
                    ratio   = "{:.4f}".format(hist_rate / price_rate)
                    ret = (dcprice, ratio) 
        return ret

    def filter4Show(self, dateTime, twoline, value):
        def filter(diff, fit, flag):
            keepin  = {} 
            discard = set() 
            for i in range(0, len(diff) - 1):
                for j in range(i + 1, len(diff)):
                    if abs(diff[i] - diff[j]) < 0.01:
                        if (flag * diff[i]) < (flag * diff[j]):
                            discard.add(fit[i].getKey())
                        else:
                            discard.add(fit[j].getKey())
            for i in range(0, len(diff)):
                fkey = fit[i].getKey()
                if fkey in discard:
                    continue
                if abs(diff[i]) > 0.13:
                    continue
                if flag == 1 and diff[i] > 0.08:
                    continue
                if flag == -1 and diff[i] < -0.08:
                    continue
                keepin[fkey] = fit[i].compute(self.__dtzq[dateTime] + 1)
            return keepin

        incdiff  = twoline[0]
        incqsfit = twoline[1]
        self.__ftInc = filter(incdiff, incqsfit, 1)
        desdiff  = twoline[2]
        desqsfit = twoline[3]
        self.__ftDes = filter(desdiff, desqsfit, -1)

    def add2observed(self, dateTime, now_dt, value):
        if self.__xtTriangle is not None:
            boundup = self.computeBoundUp(dateTime, now_dt, value)
            name = None
            if boundup[0] == 1:
                name = boundup[1] 
            if name is not None and name not in self.__observed: 
                val = [dateTime]
                self.__observed[name] = val 
                return
        tmp = {}
        for name,val in self.__observed.iteritems():
            nob = len(val) 
            if nob > 0 and nob < 4:
                val.append(dateTime)
                self.add2drop(dateTime, name)
            if len(val) == 4:
                print 'Handle OB:', dateTime, val 
            else:
                newval    = val
                tmp[name] = newval
        self.__observed = tmp

    def add2drop(self, dateTime, name):
        self.__dropout.append((dateTime, name))

    # 1: 反弹至新高或者新高附近，需要观察后续3个Bar，包括T日的Bar
    def computeBoundUp(self, dateTime, now_dt, bar):
        ret = 0 
        if self.__direct == -1:
            begin   = self.__dateopen[self.__gddt]
            nclose  = bar.getClose()
            zhangfu = (nclose - begin) / begin
            peekcl = self.__dateclose[now_dt]
            diff   = (nclose - peekcl) / peekcl
            if zhangfu > 0.10 and abs(diff) < 0.01:
                ret = 1
        return (ret, 'boundup')

    def computeHLinePosition(self, dateTime, bar):
        hline = None
        close = bar.getClose()
        median = [x[2] for x in self.__hlcluster] 
        tup = utils.minVertDistance(median, close) 
        if tup is not None:
            hline = (tup[1], tup[2])
        return hline

    # 颈线强势突破
    def xtNeckLine(self, dateTime, twoline, hline, bar, now_val, now_dt):
        # MACD零轴以上
        if self.__direct == 1:
            return
        # 隔峰高点位置
        peekhigh  = None
        pmax_date = None
        used_peek = None 
        for i in range(1,len(self.__poshist_list)):
            tmp = np.array(self.__poshist_list[ i * -1 ])
            sumhist = np.sum(tmp)
            if sumhist < 0.1:
                continue
            high = np.array(self.__poshigh_list[ i * -1 ])
            pmax_date = self.__posdate_list[i * -1][high.argmax()]
            used_peek = tmp
            break
        # 内峰, 必须要有一个波谷
        # self.xtInnerPeek(dateTime)
        if used_peek is not None:
            peekhigh = self.__datehigh[pmax_date]
            # print 'NeckLine:', dateTime, maxscore, maxdiff, self.__fts[0][0], now_dt, now_val, pmax_date, peekhigh, len(self.__poshigh)
        return peekhigh

    def xtInnerPeek(self, dateTime):
        print 'InnerPeek:', dateTime, self.__poshist

    def NBuySignal(self, dateTime, qsgd, qshist, lret, sarval, value):
        madirect   = self.__indicator.getMAdirect() 
        maposition = self.__indicator.getMAPosition() 
        buy = 0
        # 天级别买点
        if self.__period == 'day' \
                and len(self.__hist_tupo) > 0 \
                and len(self.__desdate_list) > 0 \
                and len(self.__incdate_list) > 1 \
                and qsgd is not None and qshist == 1:

            tupo     = self.__hist_tupo
            zhicheng = self.__now_zhicheng
            zuli     = self.__now_zuli
            nowtp    = self.__now_tupo
            upclose  = self.__incclose_list
            uphigh   = self.__inchigh_list
            downlow  = self.__deslow_list 
            downhigh = self.__deshigh_list 

            numtp    = len(tupo[-1])
            pdbars   = len(self.__desdate_list[-1])
            upbars   = len(self.__incdate_list[-1])

            if numtp == 0:
                return buy 

            valid    = []
            masigs  = mavalid.MAvalid()
            valid_1 = masigs.SPtimeperiod(tupo, zhicheng) 
            valid_2 = masigs.TPabovebar(tupo, maposition, madirect)
            valid_3 = masigs.TPnumber(tupo)
            valid_4 = masigs.ZLdirect(zuli, zhicheng, madirect)
            valid_5 = masigs.PrevIncDirect(tupo, madirect)
            valid_6 = masigs.GravityMoveUp(dateTime, upclose, uphigh, downlow, downhigh, value)
            valid_7 = masigs.SmoothMA(dateTime, madirect, maposition)
            valid_8 = masigs.NowTuPo(dateTime, nowtp, madirect)

            valid  = [valid_1, valid_2, valid_3, valid_4, valid_5, valid_6, valid_7, valid_8]
            nvalid = 6
            # valid  = [valid_1, valid_2, valid_3, valid_4, valid_5, valid_6, valid_8]
            # nvalid = 5 

            if sum(valid) >= nvalid and (upbars + pdbars) >= 7 \
                    and upbars >= 3 \
                    and (sarval[1] == 1 and sarval[2] == 1):
                # print dateTime, valid, upbars, pdbars, zuli
                buy = 1

        # 周级别买点
        if self.__period == 'week' and qshist == 1 and lret == 1:
            upbars = len(self.__now_zuli)
            if sarval[3] > 0.40:
                return buy
            zuli = self.__now_zuli[-1]
            zhch = self.__now_zhicheng[-1]
            if zuli[0] == -1 and zhch[0] > -1:
                mapindex  = self.__mapma[zhch[0]]
                if madirect[-1][mapindex] is not None and madirect[-1][mapindex] > 0:
                    buy = 1
        # 月级别买点
        if self.__period == 'month' and len(self.__desdate_list) > 0 and lret == 1:
            dnbars = -1
            upbars = -1
            if qshist == 1:
                dnbars = len(self.__desdate_list[-1])
                upbars = len(self.__now_zuli)
            if qshist == -1:
                dnbars = len(self.__now_zuli)
                upbars = len(self.__incdate_list[-1])
            zuli   = self.__now_zuli[-1]
            zhch   = self.__now_zhicheng[-1]
            if zuli[0] == -1 and zhch[0] > -1 and qshist == 1:
                mapindex  = self.__mapma[zhch[0]]
                if madirect[-1][mapindex] is not None and madirect[-1][mapindex] > 0 \
                        and (madirect[-1][0] - madirect[-2][0]) > 0:
                    buy = 1
        return buy

    def qsHistMAs(self, dateTime, hist, value):
        op = value.getOpen()
        cl = value.getClose()
        hi = value.getHigh()
        qs = 0
        gd = None
        if self.__prehist is not None:
            if hist < self.__prehist:
                qs = -1
                self.__deshist.append(hist)
                self.__desdate.append(dateTime)
                self.__deshigh.append(value.getHigh())
                self.__deslow.append(value.getLow())
                self.__desclose.append(value.getClose())
            else:
                qs = 1
                self.__incdate.append(dateTime)
                self.__inchist.append(hist)
                self.__inchigh.append(value.getHigh())
                self.__inclow.append(value.getLow())
                self.__incclose.append(value.getClose())
            if self.__preqs is None:
                self.__preqs = qs
            else:
                if self.__preqs * qs < 0:
                    gd = dateTime
                    self.__preqs = qs
        if gd is not None:
            self.__hist_zhicheng.append(self.__now_zhicheng)
            self.__hist_zuli.append(self.__now_zuli)

            self.__now_tupo  = []
            self.__now_zhicheng = []
            self.__now_zuli     = []
            if qs == -1:
                self.__desdate  = [self.__incdate[-1]] + self.__desdate
                self.__deshist  = [self.__prehist] + self.__deshist
                self.__deshigh  = [self.__inchigh[-1]] + self.__deshigh
                self.__deslow   = [self.__inclow[-1]] + self.__deslow
                self.__desclose = [self.__incclose[-1]] + self.__desclose

                self.__inchist_list.append(self.__inchist)
                self.__incdate_list.append(self.__incdate)
                self.__inchigh_list.append(self.__inchigh)
                self.__inclow_list.append(self.__inclow)
                self.__incclose_list.append(self.__incclose)

                (tp, zl, zc) = self.MASumPosition(dateTime, self.__incdate, self.__inchigh, self.__incclose, self.__inclow, 1) 
                self.__hist_tupo.append(tp)

                (zl, zc, tupo) = self.MAIterPosition(dateTime, value)
                self.__now_zhicheng.append(zc)
                self.__now_zuli.append(zl)
                self.__now_tupo.append(tupo)

                self.__inchist   = []
                self.__incdate   = []
                self.__inchigh   = []
                self.__inclow    = []
                self.__incclose  = []
            if qs == 1:
                self.__incdate  = [self.__desdate[-1]] + self.__incdate
                self.__inchist  = [self.__prehist] + self.__inchist
                self.__inchigh  = [self.__deshigh[-1]] + self.__inchigh
                self.__inclow   = [self.__deslow[-1]] + self.__inclow
                self.__incclose = [self.__desclose[-1]] + self.__incclose

                self.__deshist_list.append(self.__deshist)
                self.__desdate_list.append(self.__desdate)
                self.__deshigh_list.append(self.__deshigh)
                self.__deslow_list.append(self.__deslow)
                self.__desclose_list.append(self.__desclose)

                (tp, zl, zc) = self.MASumPosition(dateTime, self.__desdate, self.__deshigh, self.__desclose, self.__deslow, -1) 

                (zl, zc, tupo) = self.MAIterPosition(dateTime, value)
                self.__now_zhicheng.append(zc)
                self.__now_zuli.append(zl)
                self.__now_tupo.append(tupo)

                self.__deshist  = []
                self.__desdate  = []
                self.__deshigh  = []
                self.__deslow   = []
                self.__desclose = []
        else:
            (zl, zc, tupo) = self.MAIterPosition(dateTime, value)
            self.__now_zhicheng.append(zc)
            self.__now_zuli.append(zl)
            self.__now_tupo.append(tupo)

        diff = 0.01
        if self.__period == 'month':
            diff = 0.03
        if self.__period == 'week':
            diff = 0.02
        if len(self.__inchist_list) > 1 and len(self.__deshist_list) > 1:
            peek1 = -1; peek2 = -1
            if len(self.__fpeek) > 1:
                peek1 = self.__fpeek[0][1]
                peek2 = self.__fpeek[1][1]

            # valley1 = -1; valley2 = -1
            # if len(self.__fvalley) > 1:
            #     valley1 = self.__fvalley[0][1]
            #     valley2 = self.__fvalley[1][1]
            def get(vals, func):
                v1 = func(vals[-1])
                v2 = func(vals[-2])
                return (v1, v2)
            (ih1, ih2) = get(self.__inchigh_list, max)
            (dl1, dl2) = get(self.__deslow_list, min)
            # 突破
            TP = []
            # 压制
            YZ = 1024
            # 阻力线
            ZL = 1024
            for t in [ih1, ih2, peek1, peek2]:
                if op < t and cl > t:
                    TP.append(t)
                if ( (hi < t and (hi - t) / hi > -1 * diff) or hi > t) and cl < t and t < YZ:
                    YZ = t
                if (t - hi) / hi > diff and t < ZL:
                    ZL = t 

        return (gd, qs)
        # print dateTime, TP, YZ, ZL 
        # print dateTime, self.__inchigh_list[-1], self.__incdate_list[-1] 
 
    def MAIterPosition(self, dateTime, value):

        zlhold = 0.03
        zchold = 0.01
        if self.__period == 'week':
            zlhold = 0.06
            zchold = 0.02
        if self.__period == 'month':
            zlhold = 0.09
            zchold = 0.05

        wins = [5, 10, 20, 30, 60, 90, 120, 250]
        # 压力MA、支撑MA
        ZULI     = (-1, +1024) 
        ZHICHENG = (-1, -1024)
        TUPO     = (-1, -1024)
       
        opens = value.getOpen()
        high  = value.getHigh()
        low   = value.getLow()
        close = value.getClose()
        mas = self.__dtmas[dateTime]
        for w in wins:
            if w in mas:
                if (high > mas[w] and close < mas[w]) or (high < mas[w] and abs((high - mas[w]) / high) < zlhold): 
                    if mas[w] < ZULI[1]:
                        ZULI = (w, mas[w])
                if ((low < mas[w] and close > mas[w]) \
                        or ((low - mas[w]) / low > 0 and (low - mas[w]) / low < zchold)):
                    if mas[w] > ZHICHENG[1]:
                        ZHICHENG = (w, mas[w])
                if opens < mas[w] and close > mas[w] and mas[w] > TUPO[1]:
                    TUPO = (w, mas[w])

        return (ZULI, ZHICHENG, TUPO)
           
    def MASumPosition(self, dateTime, qsdt, qshigh, qsclose, qslow, qs):
        high_date      = qsdt[np.argmax(qshigh)]
        close_max_date = qsdt[np.argmax(qsclose)]
        
        low_date       = qsdt[np.argmin(qslow)]
        close_min_date = qsdt[np.argmin(qsclose)]

        wins = [5, 10, 20, 30, 60, 90, 120, 250]
        # 突破、阻力、支撑
        tpmas = [] 
        zlmas = []
        zcmas = []
        if qs == 1:
            bg = qsdt[0]
            ed = qsdt[-1]
            himas = self.__dtmas[high_date]
            clmas = self.__dtmas[close_max_date]
            bgmas = self.__dtmas[bg]
            edmas = self.__dtmas[ed]
            bgval = min(self.__dateopen[bg], self.__dateclose[bg])
            edval = max(self.__dateopen[ed], self.__dateclose[ed])
            for w in wins:
                if w in bgmas:
                    if bgval < bgmas[w] and edval > edmas[w]:
                        tpmas.append(w)
                hhigh  = self.__datehigh[high_date]
                hclose = self.__dateclose[high_date] 
                if w in himas and w in clmas:
                    if ((hhigh > himas[w] and hclose < himas[w]) \
                            or ((hhigh - himas[w]) / hhigh) < -0.01) \
                            and self.__dateclose[close_max_date] < clmas[w]:
                        zlmas.append(w)
        if qs == -1:
            clmas = self.__dtmas[close_min_date]
            lwmas = self.__dtmas[low_date]
            for w in wins:
                low   = self.__datelow[low_date]
                close = self.__dateclose[low_date] 
                if w in lwmas and w in clmas:
                    if ((low < lwmas[w] and close > lwmas[w]) \
                            or ((low - lwmas[w]) / low > 0 and (low - lwmas[w]) / low < 0.01)) \
                            and self.__dateclose[close_min_date] > clmas[w]:
                        zcmas.append(w)
        return (tpmas, zlmas, zcmas)

    # Triangle XingTai 
    def xtTriangle(self, dateTime, twoline, hline, sup, prs):
        ret = None 
        incline_t = 0.01
        incdiff  = twoline[0]
        incqsfit = twoline[1]
        # NO.1, Horizon Line + Increase Line
        fts = self.__fts
        if len(incdiff) > 0:
            absdiff = np.abs(incdiff)
            min_index = absdiff.argmin()

            # SCORE MACD
            (weakmacd, score, dcprice, gcprice) = self.scoreMACD(dateTime)
            # print 'DEBUG:', dateTime, np.min(absdiff), hline[0], fts[0][0], score, weakmacd, dcprice, gcprice

            # SCORE QUSHI
            self.__QUSHI   = self.scoreQUSHI(dateTime, twoline, sup, prs, weakmacd, fts[0][0])
            self.__DTBORAD = self.scoreDT(dateTime, weakmacd, fts[0][0], fts[8])

            # 均线动能不足,放入观察池
            if self.__prevXTscore is not None:
                reverse = (fts[0][0] - self.__prevXTscore[1]) / self.__prevXTscore[1]
                timeused = self.__dtzq[dateTime] - self.__dtzq[self.__prevXTscore[0]] 
                if self.__prevXTscore[1] < -500 \
                        and reverse < -1 \
                        and fts[0][0] > 0 \
                        and timeused < 6 \
                        and hline[0] < 0.01:
                    # print 'REVERSE:', dateTime
                    self.__prevXTscore = None

            # 即将突破
            if np.min(absdiff) < incline_t \
                    and min_index in sup \
                    and hline[0] < 0.01:
                if weakmacd < 0.6:
                    inc_pred  = incqsfit[min_index].compute(self.__dtzq[dateTime] + 1)
                    if fts[0][0] > 0:
                        ret = (fts[0], inc_pred, dcprice, gcprice, incqsfit[min_index]) 
                    if fts[0][0] < 0:
                        self.__prevXTscore = (dateTime, fts[0][0])
                else:
                    print 'drop_macd:', dateTime, self.__inst, score
            self.__prevmacd = score
        return ret

    # MACD 计算方法
    # nfast = (newval - fastval) * fastmulti + fastval 
    # nslow = (newval - slowval) * slowmulti + slowval 
    # ndiff = nfast - nslow
    # nsig =  (ndiff - sigval) * sigmulti + sigval 
    # sigmulti  = (2.0 / (9  + 1))
    def fakeCross(self, dateTime, fastval, slowval, sigval):
        fastmulti = (2.0 / (12 + 1))
        slowmulti = (2.0 / (26 + 1))
        fenzi = sigval + fastval * fastmulti - slowval * slowmulti - (fastval - slowval)
        fenmu = fastmulti - slowmulti
        fprice = fenzi / fenmu 
        # print 'FakeMACD:', dateTime, fenzi, fenmu, nopen
        return fprice 

    def scoreDT(self, dateTime, weakmacd, mascore, dt):
        ret = None 
        if weakmacd < 0.6 and mascore > 100.0 and dt[0] == 1:
            # print 'DEBUG:', dateTime, mascore, dt
            ret = (1.0, mascore)
        return ret

    # 整体趋势线的评估
    # 1. 上升趋势的支持度
    # 2. 下降趋势的压力度
    # 3. incscore > 0: 至少收盘在一个趋势线之上，且sum > 0
    def scoreQUSHI(self, dateTime, twoline, sup, prs, macdscore, mascore):

        self.__MAscore5.onNewValue(dateTime, mascore)
        self.__MAscore10.onNewValue(dateTime, mascore)
        mascore5  = self.__MAscore5.getValue()
        mascore10 = self.__MAscore10.getValue()

        incdiff  = np.array(twoline[0])
        incqsfit = twoline[1]

        desdiff  = np.array(twoline[2])
        desqsfit = twoline[3]

        threshold = 0.10
        if self.__inst[0:2] == 'ZS':
            threshold = 0.05

        def score(diff, qsfit, line):
            ss = 0.0
            ind = np.where(abs(diff) < threshold)[0]
            for i in ind:
                if i in line:
                    tmp = -1 * qsfit[i].getSlope() / diff[i]
                    ss  = ss + tmp
            return ss 
       
        incscore = score(incdiff, incqsfit, sup)
        desscore = score(desdiff, desqsfit, prs)

        # action
        # 0  == HOLD
        # 1  <  BUY
        # -1 > SELL
        upguai  = 0
        action  = 0 
        if macdscore > 0.6 and mascore < 0.0:
            action = action - 1 
            if mascore < -1000:
                self.__chaodie = 1
            if mascore < -2000:
                self.__chaodie = 1

        if incscore < 1.0 and incscore > 0.10 and mascore > 50.0 and macdscore < 0.6:
            action = action + 1 
        if mascore > 2000 and incscore > 0.00 and macdscore < 0.6:
            action = action + 1
        
        # PREVIOUS ACTION
        if len(self.__qScore) > 0:
            if self.__qScore[-1][5] == 'SELL' and (mascore < -61.8 or macdscore > 0.6):
                action = action - 1
            
            prevMA5  = self.__qScore[-1][6]
            prevMA10 = self.__qScore[-1][7]
            if mascore5 > prevMA5 and mascore10 > prevMA10:
                upguai = 1
                if self.__chaodie == 1:
                    action = action + 1
                    self.__chaodie = 0
            if prevMA5 > prevMA10 and mascore5 < mascore10:
                upguai = -1

        state = 0 
        if action >= 1:
            state = 1 
        if action <= -1:
            state = -1 

        tmp = (incscore, desscore, macdscore, mascore, action, state, mascore5, mascore10, upguai)
        self.__qScore.append(tmp)

        mascore = "{:.4f}".format(mascore)

        # print 'DEBUG:', dateTime, self.__inst, incscore, desscore, macdscore, mascore, action, state, self.__chaodie, upguai

        return (mascore, state)

    def scoreMACD(self, dateTime):
        score    = 0
        weakmacd = 0.0
        dcprice  = None 
        gcprice  = None

        nfast = self.__macd.getFast()
        nslow = self.__macd.getSlow()
        nDIF = self.__macd[-1] 
        yDIF = self.__macd[-2]
        nDEA = self.__macd.getSignal()[-1]
        yDEA = self.__macd.getSignal()[-2]
        nHist = self.__macd.getHistogram()[-1]
        # yHist = self.__macd.getHistogram()[-2]
        cdiff = nDIF - yDIF 
        cdea  = nDEA - yDEA 
        dweak = 0.0

        # MACD-恶化收敛
        if nDIF < nDEA and cdiff < 0 and cdea < 0:
            dweak = (cdiff * cdea) / (abs(yDIF) * abs(yDEA))
            score = 1000 * dweak
            if self.__prevmacd is not None:
                weakmacd = score / (0.00001 + self.__prevmacd)
                if self.__prevmacd < 0.000001 and score < 0.318:
                    gcprice = self.fakeCross(dateTime, nfast, nslow, nDEA)
                    weakmacd = 0.0

        # MACD－即将快速死叉，收盘或者盘中死叉化解, 决定是否买入
        speedDIF = abs(cdiff / yDIF)
        speedDEA = abs(cdea  / yDEA)
        strength = speedDIF / speedDEA
        if nDIF > nDEA and cdiff < 0 and cdea > 0 \
                and (strength > 5 or nHist < 0.1):
            dcprice = self.fakeCross(dateTime, nfast, nslow, nDEA)

        return (weakmacd, score, dcprice, gcprice) 

    # Score Instrument based on Current QUSHI
    def computeBarLinePosition(self, dateTime, bar):
        incdiff = []; incqsfit = []
        desdiff = []; desqsfit = []

        incdiff_high = []
        incdiff_low  = []
        desdiff_high = []
        desdiff_low  = []

        close = bar.getClose()
        high  = bar.getHigh()
        low   = bar.getLow()

        for k,val in self.__nowincline.iteritems():
            for v in val:
                qsfit = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq)
                incqsfit.append(qsfit)

                incdiff.append((qsfit.compute(self.__dtzq[dateTime]) - close) / close)
                incdiff_high.append((qsfit.compute(self.__dtzq[dateTime]) - high) / high)
                incdiff_low.append((qsfit.compute(self.__dtzq[dateTime]) - low) / low)

        for k,val in self.__nowdesline.iteritems():
            for v in val:
                qsfit = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq)
                desqsfit.append(qsfit)

                desdiff.append((qsfit.compute(self.__dtzq[dateTime]) - close) / close)
                desdiff_high.append((qsfit.compute(self.__dtzq[dateTime]) - high) / high)
                desdiff_low.append((qsfit.compute(self.__dtzq[dateTime]) - low) / low)

        return (incdiff, incqsfit, desdiff, desqsfit, incdiff_high, incdiff_low, desdiff_high, desdiff_low)

    def updateGD(self, now_dt):
        item = None
        if self.__gddt in self.__LFVbeili and self.__fix == 1:
            item = self.__LFVbeili[self.__gddt]
        if self.__gddt in self.__LFPbeili and self.__fix == 1:
            item = self.__LFPbeili[self.__gddt]
        val = item
        key = self.__gddt
        # check time of Beili; IF it happens after CURRENT MAX/MIN POINT --- NOT REPLACE
        if item is not None and val[0].date() < now_dt.date() and key in self.__gd:
            del self.__gd[key]
            self.__gd[val[0]] = val[1]
            self.__beili = -1
            self.__gddt  = val[0]

    def setVBeiLiBuyPoint(self, dateTime):
        res = 0 
        if self.__gddt in self.__LFVbeili and (self.__gddt not in self.__vbused):
            # item = self.__LFVbeili[self.__gddt]
            cdiff = self.__macd[-1] - self.__macd[-2]
            cdea  = self.__macd.getSignal()[-1] - self.__macd.getSignal()[-2]
            if np.mean(self.__neghist) < -0.05 and cdiff > 0 and cdea > 0:
                res = 1
                self.__vbused.add(self.__gddt)
        return res 

    def getValue(self):
        ret = (self.__gd, self.__nowgd, self.__nowhist, self.__hlcluster, \
               self.__fvalley, self.__fpeek, \
               self.__desline, self.__incline, \
               self.__nowdesline, self.__nowincline, \
               self.__vbeili, self.__xtTriangle, self.__roc, self.__dtzq, \
               self.__dropout, self.__ftDes, self.__ftInc, self.__observed, \
               self.__cxshort, self.__QUSHI, self.__DTBORAD, self.__NBS)
        return ret


class MacdSegment(technical.EventBasedFilter):
    def __init__(self, BarSeries, windows=250, inst=None, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, BarSeries, MacdSegEventWindow(BarSeries, windows, inst, useAdjustedValues), maxLen)
###
