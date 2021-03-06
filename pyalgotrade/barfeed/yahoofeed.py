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

from pyalgotrade.barfeed import csvfeed
from pyalgotrade.barfeed import common
from pyalgotrade.utils import dt
from pyalgotrade import bar
from pyalgotrade import dataseries
from pyalgotrade import marketsession 

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
    if freq == bar.Frequency.DAY or freq == bar.Frequency.WEEK or bar.Frequency.MONTH:
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

    if freq == bar.Frequency.MIN15:
        year  = int(date[0:4])
        month = int(date[5:7])
        day   = int(date[8:10])
        hour  = int(date[11:13])
        mint  = int(date[14:16])
        ret = datetime.datetime(year, month, day, hour, mint)

    if freq == bar.Frequency.MIN30:
        year  = int(date[0:4])
        month = int(date[5:7])
        day   = int(date[8:10])
        hour  = int(date[11:13])
        mint  = int(date[14:16])
        ret = datetime.datetime(year, month, day, hour, mint)

    if freq == bar.Frequency.MIN60:
        year  = int(date[0:4])
        month = int(date[5:7])
        day   = int(date[8:10])
        hour  = int(date[11:13])
        mint  = int(date[14:16])
        ret = datetime.datetime(year, month, day, hour, mint)

    return ret


class RowParser(csvfeed.RowParser):
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

    def parseBar(self, csvRowDict):
        dateTime = self.__parseDate(csvRowDict["Date"])
        close = float(csvRowDict["Close"])
        open_ = float(csvRowDict["Open"])
        high = float(csvRowDict["High"])
        low = float(csvRowDict["Low"])
        volume = float(csvRowDict["Volume"])
        adjClose = float(csvRowDict["Adj Close"])

        if self.__sanitize:
            open_, high, low, close = common.sanitize_ohlc(open_, high, low, close)

        return bar.BasicBar(dateTime, open_, high, low, close, volume, adjClose, self.__frequency)


class Feed(csvfeed.BarFeed):
    """A :class:`pyalgotrade.barfeed.csvfeed.BarFeed` that loads bars from CSV files downloaded from Yahoo! Finance.

    :param frequency: The frequency of the bars. Only **pyalgotrade.bar.Frequency.DAY** or **pyalgotrade.bar.Frequency.WEEK**
        are supported.
    :param timezone: The default timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
    :type timezone: A pytz timezone.
    :param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.

    .. note::
        Yahoo! Finance csv files lack timezone information.
        When working with multiple instruments:

            * If all the instruments loaded are in the same timezone, then the timezone parameter may not be specified.
            * If any of the instruments loaded are in different timezones, then the timezone parameter must be set.
    """

    def __init__(self, frequency=bar.Frequency.DAY, timezone=None, maxLen=dataseries.DEFAULT_MAX_LEN):
        if isinstance(timezone, int):
            raise Exception("timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

        if frequency not in [bar.Frequency.DAY, bar.Frequency.WEEK, \
                             bar.Frequency.MINUTE, bar.Frequency.MONTH, \
                             bar.Frequency.MIN15, bar.Frequency.MIN30, \
                             bar.Frequency.MIN60]:
            raise Exception("Invalid frequency.")

        csvfeed.BarFeed.__init__(self, frequency, maxLen)
        self.__timezone = timezone
        self.__sanitizeBars = False

    def sanitizeBars(self, sanitize):
        self.__sanitizeBars = sanitize

    def barsHaveAdjClose(self):
        return True

    def addBarsFromCSV(self, instrument, path, timezone=None,market=None):
        """Loads bars for a given instrument from a CSV formatted file.
        The instrument gets registered in the bar feed.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param path: The path to the CSV file.
        :type path: string.
        :param timezone: The timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
        :type timezone: A pytz timezone.
        """

        if isinstance(timezone, int):
            raise Exception("timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

        if timezone is None:
            timezone = self.__timezone

        rowParser = RowParser(self.getDailyBarTime(), self.getFrequency(), timezone, self.__sanitizeBars)
        csvfeed.BarFeed.addBarsFromCSV(self, instrument, path, rowParser,market)
