import numpy as np


# 波段的有效性指标
class DTvalid(object):

    def __init__(self, nbar):
        self.__test = 'ok'
        self.__nbar = nbar

    # 资金
    # 净买入 / 净卖出
    def money(self, rate):
        flag = -1 
        if rate is None:
            flag = 3
        else:
            if rate < 1.5 and rate > 0.80:
                flag = 1
            else:
                flag = 2
        return flag

    # 1 -- 缩量
    # 2 -- 常量
    # 3 -- 巨量
    def volume(self, dateTime, dt, incvols, desvols):
        flag = 0
        lb   = dt[1]
        lb5  = dt[2]
        lb20 = dt[3] 

        nvol = self.__nbar.getVolume()
        def stats(arrvols, nvol):
            npvols = np.array(arrvols) 

            npmax  = np.max(npvols) 
            npmed  = np.median(npvols) 
            npmean = np.mean(npvols)

            rmax  = nvol / npmax
            rmed  = nvol / npmed

            return (rmax, rmed, npmean)

        (rincmax, rincmed, incmean) = stats(incvols, nvol)
        (rdesmax, rdesmed, desmean) = stats(desvols, nvol)

        rmax = min([rincmax, rdesmax])

        if incmean / desmean < 1.0:
            return flag

        if lb < 1.0 and rmax < 1.1:
            flag = 1
        if lb > 1.0 and lb < 3.0 and rmax < 1.1:
            flag = 2
        if lb > 3.0 and lb20 > 3.0 and lb5 > 2.0 and rmax > 3.0:
            flag = 3

        return flag

    def status(self, dateTime, mascore, dt, incvols, desvols):
        ret = 0
        mflag = self.money(dt[0])
        vflag = self.volume(dateTime, dt, incvols, desvols)

        if mflag == 1 and vflag == 1:
            ret = 11
        if mflag == 1 and vflag == 2:
            ret = 12

        if mflag == 3 and vflag == 1:
            ret = 21
        if mflag == 3 and vflag == 2:
            ret = 22

        return (mascore, ret)
##
