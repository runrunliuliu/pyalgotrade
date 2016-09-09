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
            if rate > 0.80:
                flag = 1
            else:
                flag = 2
        return flag

    # 1 -- 缩量
    # 2 -- 常量
    # 3 -- 巨量
    def volume(self, dateTime, dt, tup):
        
        incvols = tup[0]
        desvols = tup[1]
        incfb   = tup[2]
        desfb   = tup[3]

        flag = 0
        lb   = dt[1]
        lb5  = dt[2]
        lb20 = dt[3] 

        nvol = self.__nbar.getVolume()
        def stats(arrvols, nvol, fb):
            npvols = [] 
            for i in range(0, len(arrvols)):
                if fb[i] == 0:
                    npvols.append(arrvols[i])
            npvols = np.array(npvols)

            npmax  = np.max(npvols) 
            npmed  = np.median(npvols) 
            npmean = np.mean(npvols)

            rmax  = nvol / npmax
            rmed  = nvol / npmed

            return (rmax, rmed, npmean)

        (rincmax, rincmed, incmean) = stats(incvols, nvol, incfb)
        (rdesmax, rdesmed, desmean) = stats(desvols, nvol, desfb)

        rmax = min([rincmax, rdesmax])
        
        if len(incvols) > len(desvols):
            sums = []
            for i in range(1, len(desvols) + 1):
                if incfb[i * -1] == 0:
                    sums.append(incvols[i * -1])
            incmean = np.mean(sums)
            # incmean = np.mean(incvols[-1 * len(desvols):])

        # print dateTime, incmean, desmean, len(incvols), len(desvols)
        # print dateTime, incvols, desvols, incfb, desfb

        if incmean / desmean < 1.0:
            return flag

        if lb < 1.0 and rmax < 1.1:
            flag = 1
        if lb > 1.0 and lb < 3.0 and rmax < 2.0:
            flag = 2
        if lb > 3.0 and lb20 > 3.0 and lb5 > 2.0 and rmax > 3.0:
            flag = 3

        return flag

    def status(self, dateTime, mascore, dt, tup):

        ret = 0
        mflag = self.money(dt[0])
        vflag = self.volume(dateTime, dt, tup)
        
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
