import pandas as pd
import numpy as np


class InstrumentInfo(object):

    def __init__(self, path):
        df = pd.read_csv(path, dtype={'code':np.str}, encoding='utf8') 
        index = 'code'
        key   = 'name'
        self.__codename = df.set_index(index)[key].to_dict() 

    def getName(self, code):
        name = None
        key = code
        if len(code) > 6:
            key = code[2:len(code)]            
        if key in self.__codename:
            name = self.__codename[key]
        return name 
# 
