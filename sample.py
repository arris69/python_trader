from python_trader.csv_parser import CsvHandler
from python_trader.strategy import Strategy

euruds_data = CsvHandler("sample_data/EURUSD5.csv", csv_type="mt4").get_df()

historical_data = {
    "EURUSD": {"historical_data": euruds_data, "point_value": 0.00001, "spread": 9},
}


class My(Strategy):
    def on_bar_close(self, asset, bars):

        sma0 = self.indicator_index(self.SMA(window=20), -1)
        sma1 = self.indicator_index(self.SMA(window=20), -2)

        if sma0 < sma1:
            if self.df_len(self.pending_orders) == 0:
                open_price = bars[-1]["Close"] - 0.001
                tp = open_price + 0.0005
                sl = open_price - 0.001
                self.buy_limit(open_price=open_price, tp=tp, sl=sl, size=0.01)

    def on_finish(self):
        # print(self.history)
        # print(self.pending_orders)
        # print(self.active_positions)
        print(self.statics)
        self.export_csv(self.statics, "result.csv")


if __name__ == "__main__":
    My().test(
        register_data=historical_data,
        from_date="2020.10.15 05:05",
        to_date="2020.11.10 20:05",
        init_balance=100,
    )
