# coding:utf-8
import numpy as np


class MA(object):

    def __init__(self):
        self.__bull = None

    def initTup(self, dateTime, tup):
        self.__nowdt = dateTime
        self.__madirect   = tup[0]
        self.__maposition = tup[1]

    # 返回结果
    def toDict(self):
        ret = dict()
        if self.__bull is not None:
            ret['bull'] = self.__bull

        return ret

    # 执行
    def run(self):
        self.__bull = self.MABull()
        
    def MABull(self):
        ret = 0
        # 均线方向
        np_mad = np.asarray(self.__madirect[-1])
        gtz    = np.where(np_mad > 0)

        if len(gtz[0]) == len(np_mad):
            if np.max(np_mad[6:8]) > 0.001 and np.min(np_mad[0:6]) > 0.001:
                ret = ret + 1
        else:
            if np.min(np_mad) < -0.002 or np_mad[-1] < 0:
                ret = ret - 1

        # 均线位置
        np_map = np.asarray(self.__maposition[-1])
        diff = [] 
        if np_map[4] is not None:
            diff = np_map[0:4] - np_map[1:5]
            if np.max(diff) > 0:
                ret = ret - 1
            else:
                ret = ret + 1

        return ret
