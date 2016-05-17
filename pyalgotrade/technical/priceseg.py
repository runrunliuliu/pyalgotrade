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
        self.__inst    = inst 
        self.__priceDS = BarSeries.getCloseDataSeries()
        self.__macd = macd.MACD(self.__priceDS, 12, 26, 9, flag=0)

        self.__indicator = indicator.IndEventWindow()

        self.__bars   = BarSeries

        self.__prevmacd    = None 
        self.__prevXTscore = None

        self.__fix    = 1 
        self.__beili  = 0 
        self.__vbeili = 0 

        self.__gfbeili = (-1, -1)

        self.__xtTriangle = None 
        self.__roc = None
        self.__cxshort = None

        self.__vbused = set()
        
        # Record Trading Days FOR ZHOUQI theory
        self.__zq   = 0
        self.__dtzq = OrderedDict() 

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
            # Find GeFeng BeiLi 
            self.__gfbeili = self.findGFBeiLi(dateTime, ret)

        return (now_val, now_dt)

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

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        self.__macd.onNewValue(self.__priceDS, dateTime, value.getClose())

        self.__indicator.onNewValue(dateTime, value)

        self.__nowBar = value
        self.__datelow[dateTime]   = value.getLow()
        self.__datehigh[dateTime]  = value.getHigh()
        self.__dateclose[dateTime] = value.getClose()
        self.__dateopen[dateTime]  = value.getClose()

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
            twoline       = self.computeBarLinePosition(dateTime, value)
            hline         = self.computeHLinePosition(dateTime, value)
            (sup, prs)    = self.breakIncQSLine(dateTime, twoline)

            self.__xtTriangle = self.xtTriangle(dateTime, twoline, hline, sup, prs)
            self.xtNeckLine(dateTime, twoline, hline, value, now_val, now_dt)

            self.add2observed(dateTime, now_dt, value)

            self.__roc     = self.__fts[1] 
            self.__cxshort = self.__fts[3]
            nDIF = self.__macd[-1] 
            yDIF = self.__macd[-2]
            nDEA = self.__macd.getSignal()[-1]
            yDEA = self.__macd.getSignal()[-2]
            cDIF = 0
            cDEA = 0
            if nDIF is not None and yDIF is not None:
                cDIF = "{:.4f}".format(nDIF - yDIF)
                cDEA = "{:.4f}".format(nDEA - yDEA)
            self.__cxshort = (cDIF, cDEA) + self.__cxshort + self.__gfbeili

            self.filter4Show(dateTime, twoline, value)

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
                if flag == 1 and diff[i] > 0.03:
                    continue
                if flag == -1 and diff[i] < -0.03:
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
        incqsfit = twoline[1]
        nowx     = self.__dtzq[dateTime]
        close    = bar.getClose()
        maxscore = 0
        for i in range(0, len(incqsfit) - 1):
            qs = incqsfit[i]
            # 短期趋势度得分，分数越高，当前的趋势越好
            timediff = nowx - qs.getX1()
            if timediff < 60: 
                qscore = 1000 * qs.getSlope()
                diff = (qs.compute(nowx) - close) / close
                if qscore > 1.0 and diff < 0:
                    if qscore > maxscore:
                        maxscore = qscore
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

            (weakmacd, score, dcprice, gcprice) = self.scoreMACD(dateTime)
            # print 'DEBUG:', dateTime, np.min(absdiff), hline[0], fts[0][0], score, weakmacd, dcprice, gcprice

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
               self.__dropout, self.__ftDes, self.__ftInc, self.__observed, self.__cxshort)
        return ret


class MacdSegment(technical.EventBasedFilter):
    def __init__(self, BarSeries, windows=250, inst=None, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, BarSeries, MacdSegEventWindow(BarSeries, windows, inst, useAdjustedValues), maxLen)
###
