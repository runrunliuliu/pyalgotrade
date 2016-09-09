import numpy as np


# 均线的有效信号判定，结合macd和sar指标
class MAvalid(object):

    def __init__(self):
        self.__mapma = {
            5: 0,
            10: 1,
            20: 2,
            30: 3,
            60: 4,
            90: 5,
            120:6,
            250:7 
        }

    # 支撑线周期级别在突破线之上
    def SPtimeperiod(self, tupo, zhicheng):
        valid_1 = 1
        for tp in tupo[-1]:
            if zhicheng[-1][0] > tp:
                valid_1 = 0
                break
        return valid_1

    # 距离最近的突破线如果在bar之上，不能拐头朝下
    def TPabovebar(self, tupo, maposition, madirect):
        valid_2 = 1
        closest = (-1, -1, -1024, 1) 
        for tp in tupo[-1]:
            ind = self.__mapma[tp]
            pos = maposition[-1][ind] 
            if pos < -0.03 and pos > closest[2]:
                closest = (tp, ind, pos, madirect[-1][ind])
        if closest[-1] < -0.005:
            valid_2 = 0
        return valid_2
    
    # 突破必须3根以上均线或者1根但周期大于等于5
    def TPnumber(self, tupo):
        valid_3  = 1 
        # numtp    = len(tupo[-1])
        # set_tupo = set(tupo[-1])
        # if numtp >= 3:
        #     valid_3 = 1
        # else:
        #     if numtp == 1 and (5 in set_tupo):
        #         valid_3 = 1
        #     if numtp == 0:
        #         valid_3 = 1
        return valid_3

    # 当前无阻力线或者阻力线的下行趋势较小
    def ZLdirect(self, zuli, zhicheng, madirect):
        valid_4  = 0
        now_zuli = zuli[-1]
        nzuli    = 0            
        if now_zuli[0] != -1:
            mapindex = self.__mapma[now_zuli[0]]
            nzuli    = madirect[-1][mapindex]
        if nzuli is not None \
                and (nzuli >= 0 or (nzuli < 0 and abs(nzuli) < 0.0005)) \
                and zhicheng[-1][0] != -1:
            valid_4 = 1
        return valid_4

    # 前升浪的突破线皆拐头朝上
    def PrevIncDirect(self, tupo, madirect):
        valid_5    = 1
        arr_direct = []
        worse = 0
        # 突破线为空
        if len(tupo[-1]) == 0:
            return valid_5

        for tp in tupo[-1]:
            ind = self.__mapma[tp]
            d0  = madirect[-1][ind]
            d1  = madirect[-2][ind]
            if d0 is None and d1 is None:
                valid_5 = 0
                continue
            if d1 > 0 and d0 < 0:
                worse = 1
            arr_direct.append(d0)
        if np.min(arr_direct) < -0.01 or worse == 1:
            valid_5 = -1
        elif np.min(arr_direct) < -0.0005:
            valid_5 = 0
        return valid_5
    
    # 重心必须上移:
    # 1. 下降浪的低点高于上升浪的起点
    # 2. 突破点的收盘价高于上升浪的终点 
    def GravityMoveUp(self, dateTime, upclose, uphigh, downlow, downhigh, bar):
        valid_6 = 0
        dnhigh0 = np.max(downhigh[-1])
        dnlow0  = np.min(downlow[-1])
        dnlow1  = np.min(downlow[-2])

        upclose0 = np.max(upclose[-1])
        uphigh0  = np.max(uphigh[-1])
        uphigh1  = np.max(uphigh[-2])

        if dnlow1 > dnlow0:
            valid_6 = -10
            return valid_6

        if (dnlow1 > dnlow0 and uphigh1 > uphigh0)\
                or bar.getHigh() < uphigh0 \
                or bar.getClose() <= upclose0 \
                or bar.getClose() <= dnhigh0:
            valid_6 = -1
            return valid_6
        if dnlow1 < dnlow0 and bar.getClose() > uphigh0:
            valid_6 = 1

        return valid_6

    # 均线的平滑度
    # ma5, ma10, ma20的均线拐头力度
    # ma5, ma10, ma20的均线间距
    def SmoothMA(self, dateTime, madirect, maposition):
        valid_7 = -1
        mp  = maposition[-1]
        md0 = madirect[-1]

        mpdiff1 = mp[1] - mp[0]
        mpdiff2 = mp[2] - mp[1]
        mprate  = mpdiff1 / mpdiff2

        if mpdiff1 > 0 and mpdiff2 > 0 \
                and (mprate < 1.618 or mprate > 0.618) \
                and (md0[0] > md0[2] and md0[1] > md0[2]):
            valid_7 = 1
        return valid_7

    # 过滤信号，如果突破下行趋势的60，90，120，250
    # 放弃买入
    def NowTuPo(self, dateTime, ntp, madirect):
        valid_8 = 0
        tp = ntp[-1]
        if tp[0] >= 60:
            ind = self.__mapma[tp[0]]
            if madirect[-1][ind] < 0:
                valid_8 = -1
        return valid_8

    # 均线多头排列
    def MABULL(self, dateTime, madirect, maposition):
        valid_9 = 0
        # 均线方向
        np_mad = np.asarray(madirect[-1])
        gtz = np.where(np_mad > 0)
        if len(gtz[0]) == len(np_mad):
            if np.max(np_mad[6:8]) > 0.001 and np.min(np_mad[0:6]) > 0.001:
                valid_9 = valid_9 + 1
        else:
            if np.min(np_mad) < -0.002 or np_mad[-1] < 0:
                valid_9 = valid_9 - 1

        # 均线位置
        np_map = np.asarray(maposition[-1])
        diff = [] 
        if np_map[4] is not None:
            diff = np_map[0:4] - np_map[1:5]
            if np.max(diff) > 0:
                valid_9 = valid_9 - 1
            else:
                valid_9 = valid_9 + 1
        return valid_9

    # 调整期间MA5-MA10间距必须缩小
    def MA5Down(self, dateTime, downmas):
        valid_10 = 0
        if len(downmas) > 1: 
            d1 = downmas[-1][0][5] - downmas[-1][0][10]
            d2 = downmas[-1][-1][5] - downmas[-1][-1][10]
            rate = d2 / d1
            if rate < 0.168:
                valid_10 = 1 
            if rate > 1.168:
                valid_10 = -4
            if rate > 1.0 and rate < 1.168:
                valid_10 = -2
            if rate > 0.8 and rate < 1.0:
                valid_10 = -1
        return valid_10

    # 最后一跌MA5要收跌活着粘合
    def MAstick(self, dateTime, madirect):
        valid_11 = 0 
        md = madirect[-2]
        if md[0] < 0 or abs(md[0]) < 0.005:
            valid_11 = 1
        return valid_11

    # 均线进攻形态, 连续三日
    def MAlong(self, dateTime, madirect, maposition):
        direct = madirect[-1]
        maposition = madirect[-1]
# 
