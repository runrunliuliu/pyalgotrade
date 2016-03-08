# PyAlgoTrade
#
# Copyright 2016 liuliu.tju@gmail.com
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

from pyalgotrade.barfeed import csvfeed
from pyalgotrade.barfeed import common
from pyalgotrade.utils import dt
from pyalgotrade import bar
from pyalgotrade import dataseries
from pyalgotrade import marketsession 
from pyalgotrade.utils import csvutils
from pyalgotrade.barfeed import membf
import pandas as pd
import numpy as np
import datetime


######################################################################
# Yahoo Finance CSV parser
# Each bar must be on its own line and fields must be separated by comma (,).
#
# Bars Format:
# Date,Open,High,Low,Close,Volume,Adj Close
#
# The csv Date column must have the following format: YYYY-MM-DD

def parse_date(date, freq):
    if freq == bar.Frequency.DAY:
        year = int(date[0:4])
        month = int(date[5:7])
        day = int(date[8:10])
        ret = datetime.datetime(year, month, day)

    if freq == bar.Frequency.MINUTE:
        year  = int(date[0:4])
        month = int(date[5:7])
        day   = int(date[8:10])
        hour  = int(date[11:13])
        mint  = int(date[14:16])
        secs  = int(date[17:19])
        ret = datetime.datetime(year, month, day, hour, mint, secs)
    return ret


class RowParser(object):
    def __init__(self, dailyBarTime, frequency, timezone=None, sanitize=False, market=None):
        self.__dailyBarTime = dailyBarTime
        self.__frequency = frequency
        self.__timezone = timezone
        self.__sanitize = sanitize
        self.__market   = market 

    def __parseDate(self, dateString):
        ret = parse_date(dateString,self.__frequency)
        # Time on Yahoo! Finance CSV files is empty. If told to set one, do it.
        if self.__frequency == bar.Frequency.DAY and self.__dailyBarTime is not None:
            ret = datetime.datetime.combine(ret, self.__dailyBarTime)
        # Localize the datetime if a timezone was given.
        if self.__timezone:
            ret = dt.localize(ret, self.__timezone)
        return ret

    def getFieldNames(self):
        # It is expected for the first row to have the field names.
        return None

    def getDelimiter(self):
        return ","

    def getKeys(self):
        return self.__keys

    def setKeys(self,keys):
        self.__keys = keys[2:]

    def parseBar(self, csvRowDict):
        dateTime = self.__parseDate(csvRowDict["Date"])
        code     = csvRowDict["code"]
        kvs = dict()
        for k in self.__keys:
            kvs[k] = float(csvRowDict[k])

        return [code,bar.IndicatorBar(dateTime, kvs)]


class Feed(membf.BarFeed):
    def __init__(self, frequency=bar.Frequency.DAY, timezone=None, maxLen=dataseries.DEFAULT_MAX_LEN):
        if isinstance(timezone, int):
            raise Exception("timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

        if frequency not in [bar.Frequency.DAY, bar.Frequency.WEEK, bar.Frequency.MINUTE]:
            raise Exception("Invalid frequency.")

        membf.BarFeed.__init__(self, frequency, maxLen)

        self.__dict = {}
        self.__bars = {}
        self.__name = None
        self.__timezone = timezone
        self.__sanitizeBars = False
        self.__dailyTime = None
        self.__frequency = frequency

    def getInst(self, inst):
        return self.__bars[inst]

    def getBars(self):
        return self.__bars

    def getFrequency(self):
        return self.__frequency

    def getDailyBarTime(self):
        return self.__dailyTime

    def barsHaveAdjClose(self):
        return True

    def getMatch(self, inst, ndate):
        ret   = {}
        code  = None
        key = (ndate,inst)
        for f in self.__fields:
            if f in self.__dict and key in self.__dict[f]:
                code   = inst
                val    = self.__dict[f][key]
                ret[f] = val
        return (code,ret) 

    def addBarsFromSequence(self, instrument, bars, market=None):

        barCmp = lambda x, y: cmp(x.getDateTime(), y.getDateTime())
        self.__bars[instrument] = bars
        self.__bars[instrument].sort(barCmp)
        self.registerInstrument(instrument)

    def addBarsFromCSV(self, name, path, timezone=None,market=None):
        if isinstance(timezone, int):
            raise Exception("timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

        if timezone is None:
            timezone = self.__timezone

        # add to pandas frame
        self.__df   = pd.read_csv(path,dtype = {'code':np.str})

        self.__name = name
        rowParser   = RowParser(self.getDailyBarTime(), self.getFrequency(), timezone, self.__sanitizeBars)
        reader      = csvutils.FastDictReader(open(path, "r"), fieldnames=rowParser.getFieldNames(), delimiter=rowParser.getDelimiter())
        self.__fields = reader.getFiledNames()
        rowParser.setKeys(reader.getFiledNames())

        for f in rowParser.getKeys():
            self.__dict[f] = self.__df.set_index(['Date','code'])[f].to_dict()

        for row in reader:
            [instrument, bar_] = rowParser.parseBar(row)
            if bar_ is not None:
                loadedBars = []
                if instrument in self.__bars:
                    loadedBars = self.__bars[instrument]
                loadedBars.append(bar_)
                self.addBarsFromSequence(instrument, loadedBars)
##
