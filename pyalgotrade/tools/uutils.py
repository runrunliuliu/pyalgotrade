# coding:utf-8
import sys
import os
import time
import datetime


class TimeUtils(object):

    @staticmethod
    def dt2stamp(datetime):
        ret = time.mktime(datetime.timetuple())
        return ret

    def tostring(self,datetime):
        return datetime.strftime('%Y-%m-%d')

    def string_toDatetime(self,string):
        return datetime.datetime.strptime(string, "%Y-%m-%d")

    """两个日期的比较, 当然也可以用timestamep方法比较,都可以实现."""
    def compare_dateTime(self,dateStr1,dateStr2):
        date1 = self.string_toDatetime(dateStr1)
        date2 = self.string_toDatetime(dateStr2)
        return date1.date() > date2.date()

    """把字符串转成时间戳形式"""
    def string_toTimestamp(self,strTime):
        return time.mktime(self.string_toDatetime(strTime).timetuple())

    """ 指定日期加上 一个时间段，天，小时，或分钟之后的日期 """
    def dateTime_before(self,dateStr,days=0,hours=0,minutes=0):
        date1 = self.string_toDatetime(dateStr)
        date1 = date1 - datetime.timedelta(days=days,hours=hours,minutes=minutes)
        return date1.strftime("%Y-%m-%d")


class FileUtils(object):

    def __init__(self,basedir,path,outdir):
        self.outdir  = outdir
        self.basedir = basedir
        self.path    = path
        self.doneset = set()
        self.donedict = dict()

    def loadones(self):
        self.doneset  = self.os_walk('./output/done/' + self.path)

    def checkdone(self,ymd,code):
        [year,month,day] = ymd.split('-')
        datadir = self.basedir + '/output/' + self.path + '/' + code  + '/' + year
        check = code + '-' + year + '-' + ymd + '.done'
        if check in self.doneset:
            print >> sys.stderr, check + ' ' + ymd + ' is done...'
            return [0,0]
        return [datadir,year]

    def getpath(self,files,dirs):
        tmp  = files[:-4].split('-')
        code = tmp[0]
        year = tmp[2]
        mon  = tmp[3]
        day  = tmp[4]
        ymd  = year + '-' + mon + '-' + day

        pathf = code + '/' + year + '/' + ymd + '.txt'
        pathf = dirs + '/' + pathf

        return [ymd,pathf]

    def lsfolder(self,top_dir):
        return os.listdir(top_dir)

    def doneflag(self):
        for k,v in self.donedict.iteritems():
            donedir = self.outdir + '/output/done/' + self.path + '/' + v 
            if not os.path.exists(donedir):
                os.makedirs(donedir)
            with open(donedir + '/' + k.split('/')[-1], "w") as myfile:
                myfile.close() 

    def loadfiles(self):
        codes = self.lsfolder(self.basedir)
        paths = []
        
        for c in codes:
            files = self.os_walk(self.basedir + '/' + c)
            for f in files:
                [ymd,pathf] = self.getpath(f,self.basedir)
                [datadir,year] = self.checkdone(ymd,c)
                if year == 0:
                    continue 
                paths.append(pathf)
        return paths

    def os_walk(self,top_dir):  
        output = set() 
        for parent, dirnames, filenames in os.walk(top_dir):  
            for filename in filenames:
                xfile = os.path.abspath(os.path.join(parent, filename))  
                output.add('-'.join(xfile.split('/')[-3:]))
        return output
#
