from datetime import datetime
from functools import partial

from python_trader.indicators import Indicators
from python_trader.trader import Trader


class Strategy(Trader, Indicators):
    def __init__(self):
        super().__init__()

    def test(
        self, register_data, from_date, to_date, init_balance, previous_bars_count=100
    ):

        self.previous_bars_count = previous_bars_count
        self.register_data = register_data
        self.from_date = self.parse_str_datetime(from_date)
        self.to_date = self.parse_str_datetime(to_date)
        self.balance = init_balance
        # iterating throught assets, first completes one asset then goes to next.
        for asset, data in self.register_data.items():
            data["historical_data"].apply(
                partial(self._backtest, asset, data["historical_data"]), axis=1
            )

        self._on_finish()
        self.on_finish()

    def _backtest(self, asset, all_bars, bar):
        if not self._check_date(bar["DateTime"], self.from_date, self.to_date):
            return False

        index = self.get_row_index(all_bars, bar)
        if index > self.previous_bars_count:
            bars_until_now = all_bars[1 + index - self.previous_bars_count : index + 1]
        else:
            bars_until_now = all_bars[1 : index + 1]

        self.indicators_df = bars_until_now
        self.current_bar = bar
        self.current_asset = asset
        self._do_checks()
        self.on_bar_close(asset, bars_until_now.to_dict("records"))

    def _check_date(self, date, from_dt, to_dt):
        if from_dt <= date <= to_dt:
            return True
        else:
            return False

    def on_bar_close(self, asset, bar):
        pass

    def on_finish(self):
        pass

    def _on_finish(self):

        # calculating statics
        self.history = self.cumsum(self.history, "single_profit", "comulative_profit")
        com_series = self.history["comulative_profit"]
        profit_series = self.history["single_profit"]
        winner_series = profit_series.where(profit_series.gt(0)).dropna()
        losser_series = profit_series.where(profit_series.lt(0)).dropna()

        max_comulative_profit = com_series.max()
        max_drawdown = com_series.min()
        max_single_winner = winner_series.max()
        min_single_winner = winner_series.min()
        max_single_losser = losser_series.min()
        min_single_losser = losser_series.max()
        sum_of_winners = winner_series.sum()
        sum_of_lossers = losser_series.sum()
        winners_count = winner_series.size
        lossers_count = losser_series.size
        total_trades = lossers_count + winners_count
        average_winner = sum_of_winners / winners_count
        average_losser = sum_of_lossers / lossers_count
        profit_factor = abs(average_winner / average_losser)
        winrate = winners_count / total_trades
        # there is not index -1 -> profit is 0
        try:
            final_profit = self.get_row_by_index(com_series, -1)
        except IndexError:
            final_profit = 0

        dic = {
            "max_comulative_profit": max_comulative_profit,
            "max_drawdown": max_drawdown,
            "max_single_winner": max_single_winner,
            "min_single_winner": min_single_winner,
            "max_single_losser": max_single_losser,
            "min_single_losser": min_single_losser,
            "sum_of_winners": sum_of_winners,
            "sum_of_lossers": sum_of_lossers,
            "winners_count": winners_count,
            "lossers_count": lossers_count,
            "total_trades": total_trades,
            "average_winner": average_winner,
            "average_losser": average_losser,
            "profit_factor": profit_factor,
            "final_profit": float(final_profit),
            "winrate": winrate,
            "final_balance": self.balance,
        }

        self.statics = self.new_dic_record(self.statics, dic)

    def _do_checks(self):
        self._check_actives()
        self._check_pendings()

    @staticmethod
    def parse_str_datetime(t):
        try:
            return datetime.strptime(t, r"%Y.%m.%d %H:%M")
        except ValueError as e:
            raise ValueError(e)

    def indicator_index(self, df, index):
        return float(self.get_row_by_index(df, index))
