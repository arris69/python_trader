from random import randint

from python_trader.df_tools import DFTools


class Trader(DFTools):
    def __init__(self):

        self._active_columns = [
            "id",
            "open_time",
            "type",
            "size",
            "asset",
            "open_price",
            "sl",
            "tp",
            "swap",
            "commission",
            "single_profit",
        ]

        self._history_columns = [
            "id",
            "open_time",
            "type",
            "size",
            "asset",
            "open_price",
            "sl",
            "tp",
            "close_time",
            "close_price",
            "single_profit",
            "comulative_profit",
        ]

        self._pending_columns = [
            "id",
            "open_time",
            "type",
            "size",
            "asset",
            "open_price",
            "sl",
            "tp",
            "swap",
            "commission",
            "single_profit",
        ]

        super().__init__()
        self._current_bar = None
        self._current_asset = None
        self._register_data = None
        self._balance = None

    @property
    def register_data(self):
        return self._register_data

    @register_data.setter
    def register_data(self, data):
        self._register_data = data

    @property
    def current_bar(self):
        if self._current_bar.empty:
            print("There is not candle info")
            return False
        return self._current_bar

    @current_bar.setter
    def current_bar(self, bar):
        self._current_bar = bar

    @property
    def current_asset(self):
        return self._current_asset

    @current_asset.setter
    def current_asset(self, asset):
        self._current_asset = asset

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, balance):
        self._balance = balance

    def _common_position(self, type, **kwargs):
        dic = {}
        for item, val in kwargs.items():
            if item not in self._active_columns:
                raise Exception(f"Invalid argument {item}")
            dic[item] = val

        dic["type"] = type
        dic["open_time"] = self.current_bar["DateTime"]
        dic["asset"] = self.current_asset
        # assigning random id ... unlikely will be duplicated
        dic["id"] = self._make_rand_id()

        if "size" not in dic:
            dic["size"] = 0.01

        # checking if position is already taken
        search_row = self.search_column(self.active_positions, "id", dic["id"])
        if not search_row.empty:
            print(f"position already exists id:{dic['id']}")
            return False

        # doing different things on pendings
        if ("stop" in dic["type"]) or ("limit" in dic["type"]):
            if "open_price" not in dic:
                raise Exception("Pending orders require an valid open_price")

            self.pending_orders = self.new_dic_record(self.pending_orders, dic)
        # market execution
        else:
            dic["open_price"] = self.current_bar["Close"]
            # change time on pending order filling
            self.active_positions = self.new_dic_record(self.active_positions, dic)

        self._validate_order(dic)
        return True

    def _validate_order(self, dic):
        """ Validates position based on given tp, sl, open_price"""

        open_price = dic["open_price"]
        current_close = self.current_bar["Close"]
        type = dic["type"]

        if "tp" in dic:
            tp = dic["tp"]
        else:
            tp = False

        if "sl" in dic:
            sl = dic["sl"]
        else:
            sl = False

        if type in ["buy_stop", "sell_limit"] and not open_price > current_close:
            raise Exception(f"{type} requires higher open_price")
        elif type in ["sell_stop", "buy_limit"] and not open_price < current_close:
            raise Exception(f"{type} requires lower open_price")

        if "buy" in type:
            if tp and not tp > open_price:
                raise Exception(f"{type} requires tp to be greater than open_price")
            if sl and not sl < open_price:
                raise Exception(f"{type} requires sl to be lesser than open_price")

        elif "sell" in type:
            if tp and not tp < open_price:
                raise Exception(f"{type} requires tp to be lesser than open_price")
            if sl and not sl > open_price:
                raise Exception(f"{type} requires sl to be greater than open_price")
        return True

    def buy(self, **kwargs):
        return self._common_position("buy", **kwargs)

    def sell(self, **kwargs):
        return self._common_position("sell", **kwargs)

    def buy_stop(self, **kwargs):
        return self._common_position("buy_stop", **kwargs)

    def sell_stop(self, **kwargs):
        return self._common_position("sell_stop", **kwargs)

    def buy_limit(self, **kwargs):
        return self._common_position("buy_limit", **kwargs)

    def sell_limit(self, **kwargs):
        return self._common_position("sell_limit", **kwargs)

    def _remove_active_position(self, pos_df, lot_size=None):
        # removing position from current
        id = pos_df["id"]
        self.active_positions = self.remove_record(self.active_positions, id)
        # adding position to history
        self.history = self.new_df_record(self.history, pos_df)
        return True

    def _activate_pending_position(self, pos_df, lot_size=None):
        # removing position from current
        id = pos_df["id"]
        self.pending_orders = self.remove_record(self.pending_orders, id)
        # adding position to history
        self.active_positions = self.new_df_record(self.active_positions, pos_df)
        return True

    def _remove_pending_position(self, pos_df, lot_size=None):
        # removing position from current
        id = pos_df["id"]
        self.pending_orders = self.remove_record(self.pending_orders, id)
        # adding position to history
        self.history = self.new_df_record(self.history, pos_df)
        return

    def cancel_pending(self, id):
        row = self.search_column(self.pending_orders, "id", id)
        # no such position
        if row.empty:
            return
        self._remove_pending_position(row)

    def _check_actives(self):
        for index, position in self.active_positions.iterrows():
            if position["asset"] != self.current_asset:
                continue
            if "buy" in position["type"]:
                self._check_buy_position(position)
            elif "sell" in position["type"]:
                self._check_sell_position(position)

    def _check_pendings(self):
        for index, position in self.pending_orders.iterrows():
            if position["asset"] != self.current_asset:
                continue
            self._check_pending_position(position, position["type"])

    def _check_pending_position(self, pos_df, type):
        high = self.current_bar["High"]
        low = self.current_bar["Low"]
        open_price = pos_df["open_price"]

        if high > open_price and (type == "buy_stop" or type == "sell_limit"):
            self._activate_pending_position(pos_df)
        elif low < open_price and (type == "sell_stop" or type == "buy_limit"):
            self._activate_pending_position(pos_df)

    def _check_buy_position(self, pos_df):
        high = self.current_bar["High"]
        low = self.current_bar["Low"]
        pos_id = pos_df["id"]

        if high >= pos_df["tp"]:
            pos_df = self._finalize_position(
                pos_df, self._get_profit("tp", pos_df), pos_df["tp"]
            )
            self._remove_active_position(pos_df)
        elif low <= pos_df["sl"]:
            pos_df = self._finalize_position(
                pos_df, self._get_profit("sl", pos_df), pos_df["sl"]
            )
            pos_df["single_profit"] = self._get_profit("sl", pos_df)
            self._remove_active_position(pos_df)

    def _finalize_position(self, pos_df, profit, close_price):
        pos_df["close_price"] = close_price
        pos_df["close_time"] = self.current_bar["DateTime"]
        pos_df["single_profit"] = profit
        self.balance += profit
        return pos_df

    def _check_sell_position(self, pos_df):
        high = self.current_bar["High"]
        low = self.current_bar["Low"]
        pos_id = pos_df["id"]

        if low <= pos_df["tp"]:
            pos_df = self._finalize_position(
                pos_df, self._get_profit("tp", pos_df), pos_df["tp"]
            )
            self._remove_active_position(pos_df)
        elif high >= pos_df["sl"]:
            pos_df = self._finalize_position(
                pos_df, self._get_profit("sl", pos_df), pos_df["sl"]
            )
            self._remove_active_position(pos_df)

    def close_position(self, id):
        pos_df = self.search_column(self.active_positions, "id")
        if pos_df.empty:
            return False

        pos_df["single_profit"] = self._get_profit("manual", pos_df)
        self._remove_active_position(pos_df)
        return True

    def _get_profit(self, mode, position, value=True, spread=True):
        # getting spread
        if spread:
            spread = self.register_data[self.current_asset]["spread"]
        else:
            spread = 0

        if position.empty:
            return False

        if mode == "tp":
            profit = abs(position["tp"] - position["open_price"])
        if mode == "sl":
            profit = -abs(position["sl"] - position["open_price"])
        elif mode == "manual":
            profit = self.current_bar["Close"] - position["open_price"]

        # normalizing profit
        profit = int(profit / self.register_data[self.current_asset]["point_value"])

        # subtracting spread from final profit
        profit -= spread

        if value:
            profit *= position["size"]

        return float(profit)

    @staticmethod
    def _make_rand_id(min_int=1000000, max_int=9999999):
        return randint(a=min_int, b=max_int)
