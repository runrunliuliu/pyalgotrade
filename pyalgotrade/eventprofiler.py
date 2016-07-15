# -*- coding: utf-8 -*-
# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import numpy as np
import matplotlib.pyplot as plt
from pyalgotrade import utils
from pyalgotrade.technical import roc
from pyalgotrade import dispatcher
from prettytable import PrettyTable
from pyalgotrade.plots import barplot 
from collections import Counter


class Results(object):
    """Results from the profiler."""
    def __init__(self, eventsDict, lookBack, lookForward):
        assert(lookBack > 0)
        assert(lookForward > 0)
        self.__lookBack = lookBack
        self.__lookForward = lookForward
        self.__values = [[] for i in xrange(lookBack+lookForward+1)]
        self.__dtimes = [[] for i in xrange(lookBack+lookForward+1)]
        self.__insts  = [[] for i in xrange(lookBack+lookForward+1)]
        self.__eventCount = 0

        # Process events.
        for instrument, events in eventsDict.items():
            for event in events:
                # Skip events which are on the boundary or for some reason are not complete.
                if event.isComplete():
                    event_time = event.getDateTime()
                    instrument = event.getInstrument()
                    self.__eventCount += 1
                    # Compute cumulative returns: (1 + R1)*(1 + R2)*...*(1 + Rn)
                    values = np.cumprod(event.getValues() + 1)
                    # Normalize everything to the time of the event
                    values = values / values[event.getLookBack()]

                    for t in range(event.getLookBack()*-1, event.getLookForward()+1):
                        self.setValue(t, values[t+event.getLookBack()], event_time, instrument)

    def __mapPos(self, t):
        assert(t >= -1*self.__lookBack and t <= self.__lookForward)
        return t + self.__lookBack

    def mapPos(self, t):
        assert(t >= -1*self.__lookBack and t <= self.__lookForward)
        return t + self.__lookBack

    def setValue(self, t, value, dateTime, instrument):
        if value is None:
            raise Exception("Invalid value at time %d" % (t))
        pos = self.__mapPos(t)
        self.__values[pos].append(value)
        self.__dtimes[pos].append(dateTime)
        self.__insts[pos].append(instrument)

    def getDateTimes(self,t):
        pos = self.__mapPos(t)
        return self.__dtimes[pos]

    def getInstruments(self,t):
        pos = self.__mapPos(t)
        return self.__insts[pos]

    def getValues(self, t):
        pos = self.__mapPos(t)
        return self.__values[pos]

    def getLookBack(self):
        return self.__lookBack

    def getLookForward(self):
        return self.__lookForward

    def getEventCount(self):
        """Returns the number of events occurred. Events that are on the boundary are skipped."""
        return self.__eventCount


class Predicate(object):
    """Base class for event identification. You should subclass this to implement
    the event identification logic."""

    def eventOccurred(self, instrument, bards):
        """Override (**mandatory**) to determine if an event took place in the last bar (bards[-1]).

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param bards: The BarDataSeries for the given instrument.
        :type bards: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
        :rtype: boolean.
        """
        raise NotImplementedError()


class Event(object):
    def __init__(self, lookBack, lookForward, dateTime, instrument):
        assert(lookBack > 0)
        assert(lookForward > 0)
        self.__lookBack    = lookBack
        self.__lookForward = lookForward
        self.__values      = np.empty((lookBack + lookForward + 1))
        self.__values[:]   = np.NAN
        self.__dateTime    = dateTime
        self.__inst        = instrument

    def __mapPos(self, t):
        assert(t >= -1*self.__lookBack and t <= self.__lookForward)
        return t + self.__lookBack

    def isComplete(self):
        return not any(np.isnan(self.__values))

    def getLookBack(self):
        return self.__lookBack

    def getLookForward(self):
        return self.__lookForward

    def setValue(self, t, value):
        if value is not None:
            pos = self.__mapPos(t)
            self.__values[pos] = value

    def getValue(self, t):
        pos = self.__mapPos(t)
        return self.__values[pos]

    def getValues(self):
        return self.__values

    def getDateTime(self):
        return self.__dateTime

    def getInstrument(self):
        return self.__inst


class Profiler(object):
    """This class is responsible for scanning over historical data and analyzing returns before
    and after the events.

    :param predicate: A :class:`Predicate` subclass responsible for identifying events.
    :type predicate: :class:`Predicate`.
    :param lookBack: The number of bars before the event to analyze. Must be > 0.
    :type lookBack: int.
    :param lookForward: The number of bars after the event to analyze. Must be > 0.
    :type lookForward: int.
    """

    def __init__(self, predicate, lookBack, lookForward):
        assert(lookBack > 0)
        assert(lookForward > 0)
        self.__predicate = predicate
        self.__lookBack = lookBack
        self.__lookForward = lookForward
        self.__feed = None
        self.__rets = {}
        self.__futureRets = {}
        self.__events = {}

    def __addPastReturns(self, instrument, event):
        begin = (event.getLookBack() + 1) * -1
        for t in xrange(begin, 0):
            try:
                ret = self.__rets[instrument][t]
                if ret is not None:
                    event.setValue(t+1, ret)
            except IndexError:
                pass

    def __addCurrentReturns(self, instrument):
        nextTs = []
        for event, t in self.__futureRets[instrument]:
            event.setValue(t, self.__rets[instrument][-1])
            if t < event.getLookForward():
                t += 1
                nextTs.append((event, t))
        self.__futureRets[instrument] = nextTs

    def __onBars(self, dateTime, bars):
        for instrument in bars.getInstruments():
            self.__addCurrentReturns(instrument)
            eventOccurred = self.__predicate.eventOccurred(instrument, self.__feed[instrument])
            if eventOccurred:
                event = Event(self.__lookBack, self.__lookForward, dateTime, instrument)
                self.__events[instrument].append(event)
                self.__addPastReturns(instrument, event)
                # Add next return for this instrument at t=1.
                self.__futureRets[instrument].append((event, 1))

    def getResults(self):
        """Returns the results of the analysis.

        :rtype: :class:`Results`.
        """
        return Results(self.__events, self.__lookBack, self.__lookForward)

    def run(self, feed, rc=1, useAdjustedCloseForReturns=True):
        """Runs the analysis using the bars supplied by the feed.

        :param barFeed: The bar feed to use to run the analysis.
        :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
        :param useAdjustedCloseForReturns: True if adjusted close values should be used to calculate returns.
        :type useAdjustedCloseForReturns: boolean.
        """

        if useAdjustedCloseForReturns:
            assert feed.barsHaveAdjClose(), "Feed doesn't have adjusted close values"

        try:
            self.__feed = feed
            self.__rets = {}
            self.__futureRets = {}
            for instrument in feed.getRegisteredInstruments():
                self.__events.setdefault(instrument, [])
                self.__futureRets[instrument] = []
                if useAdjustedCloseForReturns:
                    ds = feed[instrument].getAdjCloseDataSeries()
                else:
                    ds = feed[instrument].getCloseDataSeries()

                if rc == 1:
                    self.__rets[instrument] = roc.RateOfChange(ds, 1)
                if rc == 2:
                    bars = feed.getDataSeries(instrument)
                    self.__rets[instrument] = roc.RateOfBarChange(bars, 1)

            feed.getNewValuesEvent().subscribe(self.__onBars)
            disp = dispatcher.Dispatcher()
            disp.addSubject(feed)
            disp.run()
        finally:
            feed.getNewValuesEvent().unsubscribe(self.__onBars)


def build_plot(profilerResults):
    # Calculate each value.
    x = []
    y = []
    std = []
    for t in xrange(profilerResults.getLookBack()*-1, profilerResults.getLookForward()+1):
        x.append(t)
        values = np.asarray(profilerResults.getValues(t))
        y.append(values.mean())
        std.append(values.std())

    # Plot
    plt.clf()
    plt.plot(x, y, color='#0000FF')
    eventT = profilerResults.getLookBack()
    # stdBegin = eventT + 1
    # plt.errorbar(x[stdBegin:], y[stdBegin:], std[stdBegin:], alpha=0, ecolor='#AAAAFF')
    plt.errorbar(x[eventT+1:], y[eventT+1:], std[eventT+1:], alpha=0, ecolor='#AAAAFF')
    # plt.errorbar(x, y, std, alpha=0, ecolor='#AAAAFF')
    plt.axhline(y=y[eventT], xmin=-1*profilerResults.getLookBack(), xmax=profilerResults.getLookForward(), color='#000000')
    plt.xlim(profilerResults.getLookBack()*-1-0.5, profilerResults.getLookForward()+0.5)
    plt.xlabel('Time')
    plt.ylabel('Cumulative returns')


def plot(profilerResults):
    """Plots the result of the analysis.

    :param profilerResults: The result of the analysis
    :type profilerResults: :class:`Results`.
    """
    build_plot(profilerResults)
    plt.show()


def printStats(profilerResults, base=1.0, plot=False):
    tab = PrettyTable(['T日', '平均值', '方差', '最大值', '最小值', '中值', '胜率'])
    tab.float_format = '.4'
    tday = ''
    # loseday  = []
    losebk  = {}
    winbk   = {}
    winnday  = []
    winmonth = []
    for t in xrange(profilerResults.getLookBack()*-1, profilerResults.getLookForward()+1):
        values = np.asarray(profilerResults.getValues(t))
        dtimes = np.asarray(profilerResults.getDateTimes(t))
        insts  = np.asarray(profilerResults.getInstruments(t))

        posvec = np.nonzero(values > base)[0]
        negvec = np.nonzero(values < base)[0]

        pos = len(posvec)
        neg = len(negvec)

        # Get Hist plot
        if profilerResults.mapPos(t) == 2:
            if neg > 0:
                # loseday = map(lambda x: x.strftime('%Y-%m-%d'), dtimes[negvec])
                losebk     = Counter(map(lambda x: utils.getStockCate(x), insts[negvec]))
                loseMcount = Counter(map(lambda x: x.strftime('%Y-%m'), dtimes[negvec]))
            if pos > 0:
                winbk    = Counter(map(lambda x: utils.getStockCate(x), insts[posvec]))
                winnday  = map(lambda x: x.strftime('%Y-%m-%d'), dtimes[posvec])
                winmonth = map(lambda x: x.strftime('%Y-%m'), dtimes[posvec])
                winMcount = Counter(map(lambda x: x.strftime('%Y-%m'), dtimes[posvec]))

        if pos == 0 and neg == 0:
            win = 0.0
        else: 
            win = pos / (pos + neg + 0.0) 
        if t > 0 or t == 0:
            tday = '+'
        tab.add_row([ 'T' + tday + str(t), values.mean(), values.std(), values.max(), values.min(), np.median(values), win])
    tab.align = 'l'
    print tab

    # plots
    datalist = []
    if len(winnday) > 0 and plot is True:
        data1 = dict()
        data1['day']   = winnday
        data1['winday']   = np.zeros(len(winnday)) + 1

        data2 = dict()
        data2['month'] = winmonth
        data2['winmonth'] = np.zeros(len(winmonth)) + 1

        data3 = dict()
        data3['bk']    = winbk.keys()
        data3['winbk']  = np.array(utils.getWinRate(winbk.keys(), winbk, losebk))
 
        data4 = dict()
        data4['mdist']    = winMcount.keys()
        data4['winMdist'] = np.array(utils.getWinRate(winMcount.keys(), winMcount, loseMcount))
       
        datalist = [data1, data2, data3, data4]
        lkey = ['day', 'month', 'bk', 'mdist']
        vkey = ['winday', 'winmonth', 'winbk', 'winMdist']
        title = ['获胜时间分布', '获胜时间分布', '版块胜率分布', '月份胜率分布']
        bplot = barplot.BarPlot(datalist, vkey, lkey, title, False)
        bplot.shows()
###
