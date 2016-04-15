# -*- coding: utf-8 -*-
from bokeh.charts import Bar, output_file, show, hplot, vplot
import numpy as np


class BarPlot(object):

    def __init__(self, data, valuekey, labelkey, title='test', legend='test'):
        self.__data = data
        self.__title = title
        self.__legend = legend
        self.__vkey = valuekey
        self.__lkey = labelkey 
        output_file("stacked_bar.html")

    def shows(self):
        bars = []
        for i in range(0, len(self.__vkey)):
            bar = Bar(self.__data[i], values=self.__vkey[i], label=self.__lkey[i], agg='sum', title=self.__title[i], legend=self.__legend, width=1000)
            bars.append(bar)
        
        show(vplot(*bars))
# 
