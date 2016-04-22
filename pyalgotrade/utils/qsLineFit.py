
class QsLineFit(object):

    def __init__(self, x0, y0, x1, y1, desc=''):
        self.__x0 = x0
        self.__y0 = y0
        self.__x1 = x1
        self.__y1 = y1

        slope = (y1 - y0) / (x1 - x0)
        self.__slope = slope
        self.__b     = y0 - self.__slope * x0 

        self.__desc = desc

    @classmethod
    def initFromTuples(cls, tups, dtzq):
        x0 = tups[0]; start = dtzq[x0]
        y0 = tups[1] 
        x1 = tups[2]; end = dtzq[x1]
        y1 = tups[3]
        
        desc = 'Start:' + x0.strftime('%Y-%m-%d') \
            + ' x0:'  + str(start) \
            + ' End:' + x1.strftime('%Y-%m-%d') \
            + ' x1:'  + str(end)

        return cls(start, y0, end, y1, desc)

    def getWindows(self):
        return self.__x1 - self.__x0

    def getX1(self):
        return self.__x1

    def compute(self, x):
        return x * self.__slope + self.__b

    def getSlope(self):
        return self.__slope / self.__y0

    def setDesc(self, startday, enday):
        self.__desc = 'Start:' + startday.strftime('%Y-%m-%d') \
            + ' x0:' + str(self.__x0) \
            + ' End:' + enday.strftime('%Y-%m-%d') \
            + ' x1:' + str(self.__x1)

    def toString(self):
        return self.__desc
#
