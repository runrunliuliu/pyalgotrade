from pyalgotrade import strategy
from pyalgotrade import plotterBokeh
from pyalgotrade.tools import yahoofinance
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import bollinger
from pyalgotrade.stratanalyzer import sharpe
from samples import rsi2
from samples import macross


class BBands(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, bBandsPeriod):
       
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = instrument
        self.__bbands = bollinger.BollingerBands(feed[instrument].getCloseDataSeries(), bBandsPeriod, 2)
        
        self.setUseAdjustedValues(False)

    def getBollingerBands(self):
        return self.__bbands

    def onBars(self, bars):
        lower = self.__bbands.getLowerBand()[-1]
        upper = self.__bbands.getUpperBand()[-1]
        if lower is None:
            return

        shares = self.getBroker().getShares(self.__instrument)
        bar = bars[self.__instrument]
        if shares == 0 and bar.getClose() < lower:
            sharesToBuy = int(self.getBroker().getCash(False) / bar.getClose())
            self.marketOrder(self.__instrument, sharesToBuy)
        elif shares > 0 and bar.getClose() > upper:
            self.marketOrder(self.__instrument, -1 * shares)


def main(plot):
   
    instrument = "sz00001"

    # Download the bars.
    # feed = yahoofinance.build_feed([instrument], 2011, 2012, ".")
    
    # Load From Local FIle
    feed = yahoofeed.Feed()
    feed.addBarsFromCSV("sz00001", "SZ000001.csv")

# ==============================================================================
#     bBandsPeriod = 40
#     strat = BBands(feed, instrument, bBandsPeriod)
#     sharpeRatioAnalyzer = sharpe.SharpeRatio()
#     strat.attachAnalyzer(sharpeRatioAnalyzer)
# 
#     if plot:
#         plt = plotter.StrategyPlotter(strat, True, True, True)
#         plt.getInstrumentSubplot(instrument).addDataSeries("upper", strat.getBollingerBands().getUpperBand())
#         plt.getInstrumentSubplot(instrument).addDataSeries("middle", strat.getBollingerBands().getMiddleBand())
#         plt.getInstrumentSubplot(instrument).addDataSeries("lower", strat.getBollingerBands().getLowerBand())
# ==============================================================================


# ==============================================================================
#     entrySMA = 125
#     exitSMA = 10
#     rsiPeriod = 2
#     overBoughtThreshold = 90
#     overSoldThreshold = 10
#     strat = rsi2.RSI2(feed, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)
#     sharpeRatioAnalyzer = sharpe.SharpeRatio()
#     strat.attachAnalyzer(sharpeRatioAnalyzer)
# 
#     if plot:
#         plt = plotter.StrategyPlotter(strat, True, False, True)
#         plt.getInstrumentSubplot(instrument).addDataSeries("Entry SMA", strat.getEntrySMA())
#         plt.getInstrumentSubplot(instrument).addDataSeries("Exit SMA", strat.getExitSMA())
#         plt.getOrCreateSubplot("rsi").addDataSeries("RSI", strat.getRSI())
#         plt.getOrCreateSubplot("rsi").addLine("Overbought", overBoughtThreshold)
#         plt.getOrCreateSubplot("rsi").addLine("Oversold", overSoldThreshold)
# ==============================================================================
    
    ma1 = 5
    ma2 = 120
    ma3 = 10
    ma4 = 20
    strat = macross.DualMAcross(feed, instrument,ma1,ma2,ma3,ma4)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    if plot:
        plt = plotterBokeh.StrategyPlotter(strat, True, False, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("ma1", strat.getMa1())
        plt.getInstrumentSubplot(instrument).addDataSeries("ma4", strat.getMa4())
   
    strat.run()
    print "Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05)

    if plot:
        plt.plot()
        
if __name__ == "__main__":
    main(True)
# -*- coding: utf-8 -*-
