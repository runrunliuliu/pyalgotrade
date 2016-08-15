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
        numtp    = len(tupo[-1])
        set_tupo = set(tupo[-1])
        valid_3 = 0
        if numtp >= 3:
            valid_3 = 1
        else:
            if numtp == 1 and (5 in set_tupo):
                valid_3 = 1
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
        upclose1 = np.max(upclose[-1])
        uphigh1  = np.max(uphigh[-1])

        if dnlow1 > dnlow0 or uphigh1 > bar.getHigh() or bar.getClose() <= upclose1 \
                or bar.getClose() <= dnhigh0:
            valid_6 = -1
            return valid_6
        if dnlow1 < dnlow0 and bar.getClose() > uphigh1:
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
# 
