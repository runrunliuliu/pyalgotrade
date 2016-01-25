# coding:utf-8
import sys
import os
import time
import datetime


class TimeUtils(object):

    def tostring(self,datetime):
        return datetime.strftime('%Y-%m-%d')

    def string_toDatetime(self,string):
        return datetime.datetime.strptime(string, "%Y-%m-%d")

    def compare_dateTime(self,dateStr1,dateStr2):
        date1 = self.string_toDatetime(dateStr1)
        date2 = self.string_toDatetime(dateStr2)
        return date1.date() > date2.date()

    def string_toTimestamp(self,strTime):
        return time.mktime(self.string_toDatetime(strTime).timetuple())

    def diff_timestamp(self,str1,str2):
        t1 = self.string_toTimestamp(str1)
        t2 = self.string_toTimestamp(str2)
        return t1 - t2

    # from ymd to y-m-d
    def string_trans(self,dateStr):
        date1 = datetime.datetime.strptime(dateStr, "%Y%m%d")
        return date1.strftime("%Y-%m-%d")

    def dateTime_before(self,dateStr,days=0,hours=0,minutes=0):
        date1 = self.string_toDatetime(dateStr)
        date1 = date1 - datetime.timedelta(days=days,hours=hours,minutes=minutes)
        return date1.strftime("%Y-%m-%d")
#
