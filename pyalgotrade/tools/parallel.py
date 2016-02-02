import multiprocessing.dummy as mp


# Applied For Parallel Excute Programs
class Parallel:

    def __init__(self,cores):
        self.__cores = cores

    def div4Parallel(self,length):
        div = dict()

        keylen = length
        cores  = self.__cores

        block = keylen / cores 
        left  = keylen % cores 
        start = 0
        for x in range(cores):
            div[x] = (start,block * (x + 1)) 
            start  = start + block
        end = div[cores - 1][1] + left
        div[cores - 1] = (div[cores - 1][0],end)
        return div

    def handleCombineRet(self,func,*args_):
        result_list = []
        def log_result(result):
            result_list.append(result)

        def apply_async_with_callback():
            pool = mp.Pool(self.__cores)
            for i in range(self.__cores):
                pool.apply_async(func, args = (i,) + args_, callback = log_result)
            pool.close()
            pool.join()
        apply_async_with_callback()
        return result_list
#
