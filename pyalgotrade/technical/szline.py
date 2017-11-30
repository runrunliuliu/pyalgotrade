# coding:utf-8

from pyalgotrade import technical
from pyalgotrade.utils import collections


# 速阻线信号
class SZLEventWindow(technical.EventWindow):

    def __init__(self):
        technical.EventWindow.__init__(self, 1, dtype=object)
        self.__xt_list = collections.ListDeque(60)

    def onNewValue(self, dateTime, value, XT):
        technical.EventWindow.onNewValue(self, dateTime, value)
        self.__xt_list.append(XT)
        values = self.getValues()
        # print dateTime, XT, values[-1].getClose()

# END
