from math import pi
import pandas as pd
from datetime import datetime
from bokeh.plotting import figure, show, output_file
from bokeh.models import HoverTool
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.cbook as cbook
import matplotlib.ticker as ticker
from matplotlib.finance import candlestick_ohlc
import matplotlib.dates as mdates


class CandlePlot(object):

    def __init__(self, data):
        self.__data = data
        output_file("candle.html")

    def getXY(self, dicts, baseday):
        X = []
        Y = []
        for k,v in dicts.iteritems():
            dt = datetime.strptime(baseday, '%Y-%m-%d')
            if k > dt:
                X.append(k)
                Y.append(v)
        return (X, Y)

    def shows(self, lines, baseday='2015-01-01'):

        (lineX, lineY) = self.getXY(lines, baseday)

        df = self.__data
        df = self.__data[self.__data.Date > baseday]

        df["Date"]  = pd.to_datetime(df["Date"])
        mids = (df.Open + df.Close) / 2
        spans = abs(df.Close-df.Open)
        inc = df.Close >= df.Open
        dec = df.Close <  df.Open
        w = 12*60*60*1000
        TOOLS = "pan,wheel_zoom,box_zoom,hover,crosshair,reset,save"
        p = figure(x_axis_type="datetime", tools=TOOLS, plot_width=1000, toolbar_location="left")
        hover = HoverTool()
        p.add_tools(hover)

        p.title = "MSFT Candlestick"
        p.xaxis.major_label_orientation = pi/4
        p.grid.grid_line_alpha = 0.5

        p.segment(df.Date[inc], df.High[inc], df.Date[inc], df.Low[inc], color="red")
        p.rect(df.Date[inc], mids[inc], w, spans[inc], fill_color="red", line_color="red")

        p.segment(df.Date[dec], df.High[dec], df.Date[dec], df.Low[dec], color="green")
        p.rect(df.Date[dec], mids[dec], w, spans[dec], fill_color="green", line_color="green")

        p.line(lineX, lineY, line_width=2, color='navy')
        
        show(p)
#
