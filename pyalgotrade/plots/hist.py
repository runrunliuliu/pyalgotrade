# -*- coding: utf-8 -*-
import numpy as np
import scipy.special
from bokeh.charts import Bar
from bokeh.plotting import figure, show, output_file, vplot


class Hist(object):

    def __init__(self, data, title='test', xlabel='test', ylabel='test'):
        self.__data = data
        self.__p1   = figure(title=title,tools="save",background_fill="#E8DDCB")
        self.__p1.legend.location = "top_left"
        self.__p1.xaxis.axis_label = xlabel 
        self.__p1.yaxis.axis_label = ylabel 
        output_file('histogram.html', title=title)

    def shows(self):
        hist, edges = np.histogram(self.__data, density=False, bins=1000)
        self.__p1.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],fill_color="#036564", line_color="#033649")
        show(vplot(self.__p1))
# 
