from math import pi

import pandas as pd

from bokeh.sampledata.stocks import _load_stock
from bokeh.plotting import figure, show, output_file,vplot

df = pd.DataFrame(_load_stock('SZ000001.csv'))
df["date"] = pd.to_datetime(df["date"])

mids = (df.open + df.close)/2
spans = abs(df.close-df.open)

inc = df.close > df.open
dec = df.open > df.close
w = 12*60*60*1000 # half day in ms

output_file("candlestick.html", title="candlestick.py example")

TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

p = figure(x_axis_type="datetime", tools=TOOLS, plot_width=1000, toolbar_location="left")

p.segment(df.date, df.high, df.date, df.low, color="black")
p.rect(df.date[inc], mids[inc], w, spans[inc], fill_color="#FF4136", line_color="#FF4136")
p.rect(df.date[dec], mids[dec], w, spans[dec], fill_color="#3D9970", line_color="#3D9970")

p.title = "SZ000001 Candlestick"
p.xaxis.major_label_orientation = pi/4
p.grid.grid_line_alpha=0.3

show(p)  # open a browser


x = list(range(11))
y0 = x
y1 = [10 - i for i in x]
y2 = [abs(i - 5) for i in x]

# create a new plot
s1 = figure(width=250, plot_height=250, title=None)
s1.circle(x, y0, size=10, color="navy", alpha=0.5)

# create another one
s2 = figure(width=250, height=250, title=None)
s2.triangle(x, y1, size=10, color="firebrick", alpha=0.5)

# create and another
s3 = figure(width=250, height=250, title=None)
s3.square(x, y2, size=10, color="olive", alpha=0.5)

# put all the plots in a VBox
p = vplot(s1, s2, s3)

# show the results
show(p)


p = figure(x_axis_type="datetime")
p.rect([d1,d2,d3], [1,5,3], [1,2,3], [5,1,2])
show(p)