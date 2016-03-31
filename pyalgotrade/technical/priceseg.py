from pyalgotrade import technical
from pyalgotrade import dataseries
from pyalgotrade.utils import collections
from pyalgotrade.dataseries import bards
from pyalgotrade.technical import ma
from pyalgotrade.technical import macd
from array import array
from collections import OrderedDict
import numpy as np


class MacdSegEventWindow(technical.EventWindow):

    def __init__(self, BarSeries, windows, inst, useAdjustedValues):
        assert(windows > 0)
        technical.EventWindow.__init__(self, windows, dtype=object)
        self.__windows = windows
        self.__priceDS = BarSeries.getCloseDataSeries()
        self.__macd = macd.MACD(self.__priceDS, 12, 26, 9, flag=0)

        self.__fix = 1 

        self.__datelow   = {}
        self.__datehigh  = {}
        self.__dateclose = {}

        self.__fvalley = []
        self.__fpeek   = []
        self.__desline = OrderedDict()
        self.__incline = OrderedDict()

        self.__gd       = OrderedDict()
        self.__LFVbeili = OrderedDict()
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
                else:
                    # Valley BeiLi Check
                    self.findBeiLi(dateTime, 1)

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
                if nex > pre * 0.618 * 0.618:
                    res.append(p)
            cnt = cnt + 1
        return res

    # Long Time QuChi Line 
    def pairVetex(self, lists, flag):
        if len(lists) < 2:
            return None
        lastvex = lists[0]
        for i in range(1,len(lists)):
            k = lists[i] 
            # Connect Higher Peek point to plot descending Line
            if flag == 1:
                date = k[0]
                val  = k[1]
                # remove ineffective Pre-Peek which has been "break through"
                if (val - lastvex[1]) / lastvex[1] > 0.05:
                    tmp  = []
                    tups = (date, val, lastvex[0], lastvex[1])
                    if lastvex[0] in self.__desline:
                        tmp = self.__desline[lastvex[0]]
                    tmp.append(tups)
                    self.__desline[lastvex[0]] = tmp
            if flag == -1:
                date = k[0]
                val  = k[1]
                if (lastvex[1] - val) / val > 0.05:
                    tmp  = []
                    tups = (date, val, lastvex[0], lastvex[1])
                    if lastvex[0] in self.__incline:
                        tmp = self.__incline[lastvex[0]]
                    tmp.append(tups)
                    self.__incline[lastvex[0]] = tmp

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
        if self.__direct == -1:
            self.pairVetex(self.__fvalley, -1)

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        self.__macd.onNewValue(self.__priceDS, dateTime, value.getClose())

        self.__datelow[dateTime]   = value.getLow()
        self.__datehigh[dateTime]  = value.getHigh()
        self.__dateclose[dateTime] = value.getClose()

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

                print dateTime, self.__LFVbeili, now_val, now_dt
                # Fix valley point based on BeiLi 
                # UPDATE: It's not NECESSARY for CHANGE to be happend
                if len(self.__LFVbeili) > 0 and self.__fix == 1:
                    item = self.__LFVbeili.popitem()
                    key  = item[0]
                    val  = item[1]
                    # check time of Beili 
                    # if it happens after CURRENT MAX POINT --- NOT REPLACE
                    if val[0].date() < now_dt.date():
                        del self.__gd[key]
                        self.__gd[val[0]] = val[1]
                    else:
                        print 'false', val[0], self.__gddt

                self.__gd[self.__gddt] = gdprice
                self.__nowgd   = now_dt
                self.__nowhist = hist
            if change == 1:
                self.parseGD(dateTime, self.__nowgd, nwprice) 

    def getValue(self):
        ret = (self.__gd, self.__nowgd, self.__nowhist, self.__hlcluster, \
               self.__fvalley, self.__fpeek, \
               self.__desline, self.__incline)
        return ret


class MacdSegment(technical.EventBasedFilter):
    def __init__(self, BarSeries, windows=250, inst=None, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, BarSeries, MacdSegEventWindow(BarSeries, windows, inst, useAdjustedValues), maxLen)
###
