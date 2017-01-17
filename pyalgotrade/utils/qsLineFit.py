
class QsLineFit(object):

    def __init__(self, x0, y0, x1, y1, desc='', key='', days=None):
        self.__x0 = x0
        self.__y0 = y0
        self.__x1 = x1
        self.__y1 = y1

        slope = (y1 - y0) / (x1 - x0)
        self.__slope = slope
        self.__b     = y0 - self.__slope * x0 

        self.__desc = desc

        self.__key  = key

        if days is None:
            self.__start = '' 
            self.__end   = ''
        else:
            self.__start = days[0]
            self.__end   = days[1]

    @classmethod
    def initFromTuples(cls, tups, dtzq, formats='%Y-%m-%d'):
        x0 = tups[0]; start = dtzq[x0]
        y0 = tups[1] 
        x1 = tups[2]; end = dtzq[x1]
        y1 = tups[3]

        desc = 'Start|' + x0.strftime(formats) \
            + ' x0|'  + str(start) \
            + ' End|' + x1.strftime(formats) \
            + ' x1|'  + str(end)

        dstart = x0.strftime(formats)
        dend   = x1.strftime(formats)
        key = dstart + '|' + dend

        tmp = (dstart, dend)
        return cls(start, y0, end, y1, desc, key, tmp)

    def getWindows(self):
        return self.__x1 - self.__x0

    def getX1(self):
        return self.__x1

    def compute(self, x):
        return x * self.__slope + self.__b

    def getSlope(self):
        return self.__slope / self.__y0

    def getKey(self):
        return self.__key

    def setDesc(self, startday, enday):
        self.__desc = 'Start|' + startday.strftime('%Y-%m-%d') \
            + ' x0|' + str(self.__x0) \
            + ' End|' + enday.strftime('%Y-%m-%d') \
            + ' x1|' + str(self.__x1)

    def toDICT(self, nind):
        out = {} 
        p1  = {}
        p2  = {}

        p1['d'] = self.__start
        p1['v'] = self.__y0
        
        p2['d'] = self.__end
        p2['v'] = self.__y1

        out['p1'] = p1
        out['p2'] = p2
        out['np'] = float("{:.4f}".format(self.compute(nind)))

        return out

    def toString(self):
        return self.__desc
#
