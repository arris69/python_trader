import ta
from ta.momentum import *
from ta.trend import *
from ta.volatility import *


class Indicators:
    _df = None

    @property
    def indicators_df(self):
        return self._df

    @indicators_df.setter
    def indicators_df(self, df):
        self._df = df

    def BollingerBands(self, **kwargs):
        return BollingerBands(self.indicators_df["Close"], **kwargs)

    def SMA(self, **kwargs):
        return SMAIndicator(self.indicators_df["Close"], **kwargs).sma_indicator()

    def EMA(self, **kwargs):
        return EMAIndicator(self.indicators_df["Close"], **kwargs).ema_indicator()

    def MACD(self, **kwargs):
        return MACD(self.indicators_df["Close"], **kwargs)

    def RSI(self, **kwargs):
        return RSIIndicator(self.indicators_df["Close"], **kwargs).rsi()

    def ATR(self, **kwargs):
        return AverageTrueRange(
            self.indicators_df["High"],
            self.indicators_df["Low"],
            self.indicators_df["Close"],
            **kwargs
        ).average_true_range()
