from pyalgotrade import strategy
from pyalgotrade import plotterBokeh
from pyalgotrade.tools import yahoofinance
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.stratanalyzer import sharpe
from samples import rsi2
from samples import patterns 


def main(plot):
   
    instrument = "sz00001"

    # Download the bars.
    # feed = yahoofinance.build_feed([instrument], 2011, 2012, ".")
    
    # Load From Local FIle
    feed = yahoofeed.Feed()
    feed.addBarsFromCSV("sz00001", "SZ000001.csv")
    
    strat = patterns.Patterns(feed,instrument)

    strat.run()

        
if __name__ == "__main__":
    main(True)
# -*- coding: utf-8 -*-
