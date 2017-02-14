from pyalgotrade.technical import szline 


class XThandle(object):

    def __init__(self):
        self.__szl = szline.SZLEventWindow()

    # 主运行
    def run(self, dateTime, value, XT):

        # PASS to Compute Signals 
        self.__szl.onNewValue(dateTime, value, XT)

#
