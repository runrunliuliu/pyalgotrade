from pyalgotrade import strategy
from pyalgotrade import plotterBokeh
from pyalgotrade.tools import yahoofinance
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.feed import csvfeed
from pyalgotrade.stratanalyzer import sharpe
from samples import dummystrategy 
from samples import rsi2
from samples import patterns 


def main(plot):
   
    instrument = "sh600036"
    #instrument = "sz000001"
    feed = yahoofeed.Feed()
    #feed.addBarsFromCSV(instrument, "../qts/pytrade/data/SZ000001.csv")
    feed.addBarsFromCSV(instrument, "../qts/pytrade/data/SH600036.csv")
    st = dummystrategy.DummyStrategy(feed, instrument)

    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    st.attachAnalyzer(sharpeRatioAnalyzer)

    if plot:
        plt = plotterBokeh.StrategyPlotter(st, True, True, True)

    st.run()

    print "Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05)

    if plot:
        plt.plot()
        
    plt.show()

if __name__ == "__main__":
    main(True)
# -*- coding: utf-8 -*-
