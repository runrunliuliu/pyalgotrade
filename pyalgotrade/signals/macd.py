# coding:utf-8
import numpy as np


class MACD(object):

    def __init__(self):
        self.__qshist = None
        self.__change = None
        self.__hist   = None

    def initTup(self, dateTime, tup):
        self.__nowdt   = dateTime
        self.__qshist  = tup[0]
        self.__change  = tup[1]
        self.__hist    = tup[2]
        self.__prehist = tup[3]

    # 返回结果
    def toDict(self):
        ret = dict()
        if self.__hist is not None:
            ret['qs']     = self.__qshist 
            ret['change'] = self.__change
            ret['hist']   = float("{:.4f}".format(self.__hist))
            ret['ratio']  = float("{:.4f}".format(abs((self.__hist - self.__prehist) / self.__prehist)))
        return ret

    # 执行
    def run(self):
        pass
