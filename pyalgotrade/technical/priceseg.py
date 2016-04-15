from pyalgotrade import technical
from pyalgotrade import dataseries
from pyalgotrade.utils import collections
from pyalgotrade.utils import qsLineFit 
from pyalgotrade.dataseries import bards
from pyalgotrade.technical import ma
from pyalgotrade.technical import macd
from pyalgotrade.technical import indicator 
from array import array
from utils import utils
from collections import OrderedDict
import numpy as np


class MacdSegEventWindow(technical.EventWindow):

    def __init__(self, BarSeries, windows, inst, useAdjustedValues):
        assert(windows > 0)
        technical.EventWindow.__init__(self, windows, dtype=object)
        self.__windows = windows
        self.__priceDS = BarSeries.getCloseDataSeries()
        self.__macd = macd.MACD(self.__priceDS, 12, 26, 9, flag=0)

        self.__indicator = indicator.IndEventWindow()

        self.__fix    = 1 
        self.__beili  = 0 
        self.__vbeili = 0 

        self.__xtTriangle = None 
        self.__roc = None

        self.__vbused = set()
        
        # Record Trading Days FOR ZHOUQI theory
        self.__zq   = 0
        self.__dtzq = OrderedDict() 

        self.__qsfilter  = set() 
        self.__qsfit     = {}
        self.__datelow   = {}
        self.__datehigh  = {}
        self.__dateclose = {}

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

        self.__posdate  = []
        self.__poshist  = []
        self.__posclose = []
        self.__poshigh  = []
        self.__poshist_list = collections.ListDeque(3)
        self.__posdate_list = collections.ListDeque(3)

        self.__neghist  = []
        self.__negdate  = []
        self.__negclose = []
        self.__neglow   = []
        self.__neghist_list = collections.ListDeque(3)
        self.__negdate_list = collections.ListDeque(3)

        self.__prehist = None
        self.__preret  = None

        self.__direct = None
        self.__gdval  = None
        self.__gddt   = None
    
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
                    self.__neghist_list.append(self.__neghist)
                    self.__negdate_list.append(self.__negdate)
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
                    self.__poshist_list.append(self.__poshist)
                    self.__posdate_list.append(self.__posdate)

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
        self.__prehist = hist 
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

        return (now_val, now_dt)

    def clusterGD(self, sdf):
        self.__hlcluster = []
        clusters = {}
        ncts = 0
        for i in range(0, len(sdf)):
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
        for i in range(0,ncts):
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
    
    # Future Peek or Valley cross the line or NOT
    def breakQSLine(self, tups, peek, valley, MVP, GDS):
        x0 = tups[0]; y0 = tups[1]; x1 = tups[2]; y1 = tups[3]
        start = self.__dtzq[x0]; end = self.__dtzq[x1]
        qfit = qsLineFit.QsLineFit(start, y0, end, y1)
        
        cross = 0
        index = []
        index.extend(valley)
        index.extend(peek)
        for p in index:
            x = self.__dtzq[p[0]]
            y = qfit.compute(x)
            if end < x:
                diff = (y - p[1]) / p[1] 
                if abs(diff) < 0.01:
                    cross = 1
                    MVP = MVP + 1 
                    cnt = 0
                    if p in GDS:
                        cnt = GDS[p]
                    cnt = cnt + 1
                    GDS[p] = cnt
        return (cross, MVP, GDS) 

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
            MVP = 0; GDS = dict() 
            for tups in lines: 
                if tups in self.__qsfilter:
                    continue
                (cross, MVP, GDS) = self.breakQSLine(tups, self.__fpeek, self.__fvalley, MVP, GDS)
                # if cross == 1:
                # print ndate, tups

                x0 = tups[0]; y0 = tups[1]; y1 = tups[3]
                # 1. remove EXPIRE QUSHI Line 
                if flag == 1 and y0 > nval * 0.95 and y1 > nval * 0.95:
                    if ndate in self.__nowdesline:
                        destmp = self.__nowdesline[ndate]
                    destmp.append(tups)
                    self.__nowdesline[ndate] = destmp
                if flag == -1 and self.__dtzq[ndate] - self.__dtzq[x0] < 120 \
                        and y0 < lastvex[1] \
                        and y1 <= lastvex[1]:
                    if ndate in self.__nowincline:
                        inctmp = self.__nowincline[ndate]
                    inctmp.append(tups)
                    self.__nowincline[ndate] = inctmp
            # print MVP, GDS

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

    # Long Time QuChi Line 
    def pairVetex(self, lists, flag):
        if len(lists) < 2:
            return None
        if flag == 1:
            self.__nowdesline = OrderedDict()
        if flag == -1:
            self.__nowincline = OrderedDict()

        neighbors = []
        lastvex = lists[0]
        neighbors.append(lastvex)
        for i in range(1,len(lists)):
            item = lists[i] 
            date = item[0]; val = item[1]
            self.connectPoint(date, val, lastvex, flag) 
            if i < 3:
                neighbors.append(item)
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
        self.clusterGD(np.sort(sdf))
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

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        self.__macd.onNewValue(self.__priceDS, dateTime, value.getClose())

        self.__indicator.onNewValue(dateTime, value)

        self.__datelow[dateTime]   = value.getLow()
        self.__datehigh[dateTime]  = value.getHigh()
        self.__dateclose[dateTime] = value.getClose()

        self.__zq = self.__zq + 1
        self.__dtzq[dateTime] = self.__zq

        self.__fts = self.__indicator.getValue()
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
            twoline = self.computeBarLinePosition(dateTime, value)
            hline   = self.computeHLinePosition(dateTime, value)
            self.__xtTriangle = self.xtTriangle(dateTime, twoline, hline)
            self.__roc = self.__fts[1] 

    def computeHLinePosition(self, dateTime, bar):
        hline = None
        close = bar.getClose()
        median = [x[2] for x in self.__hlcluster] 
        tup = utils.minVertDistance(median, close) 
        if tup is not None:
            hline = (tup[1], tup[2])
        return hline

    # Triangle XingTai 
    def xtTriangle(self, dateTime, twoline, hline):
        ret = None 
        incline_t = 0.01
        incdiff  = twoline[0]
        incqsfit = twoline[1]
        # NO.1, Horizon Line + Increase Line
        fts = self.__fts
        if len(incdiff) > 0:
            absdiff = np.abs(incdiff)
            # if np.min(absdiff) < incline_t:
            if np.min(absdiff) < incline_t and hline[0] < 0.01:
                min_index = absdiff.argmin()
                inc_pred  = incqsfit[min_index].compute(self.__dtzq[dateTime] + 1)
                ret = (fts[0], inc_pred) 
        return ret

    # Score Instrument based on Current QUSHI
    def computeBarLinePosition(self, dateTime, bar):
        incdiff = []; incqsfit = []
        desdiff = []; desqsfit = []
        close = bar.getClose()

        for k,val in self.__nowincline.iteritems():
            for v in val:
                qsfit = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq)
                incdiff.append((qsfit.compute(self.__dtzq[dateTime]) - close) / close)
                incqsfit.append(qsfit)
        for k,val in self.__nowdesline.iteritems():
            for v in val:
                qsfit = qsLineFit.QsLineFit.initFromTuples(v, self.__dtzq)
                desdiff.append((qsfit.compute(self.__dtzq[dateTime]) - close) / close)
                desqsfit.append(qsfit)
        return (incdiff, incqsfit, desdiff, desqsfit)

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
               self.__vbeili, self.__xtTriangle, self.__roc)
        return ret


class MacdSegment(technical.EventBasedFilter):
    def __init__(self, BarSeries, windows=250, inst=None, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, BarSeries, MacdSegEventWindow(BarSeries, windows, inst, useAdjustedValues), maxLen)
###
