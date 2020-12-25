import os
import warnings

import pandas as pd


class CsvHandler:
    standard_cols = ["Date", "Time", "Open", "High", "Low", "Close", "Volume"]

    def __init__(self, path, csv_type="standard", **kwargs):
        self.df = self._open_csv(path, csv_type)

    def _open_csv(self, path, csv_type):
        if csv_type == "mt5":
            warnings.filterwarnings("ignore")
            kw = {
                "delimiter": r"\t",
                "usecols": [0, 1, 2, 3, 4, 5, 7],
                "skiprows": lambda x: x in [0],
                "names": self.standard_cols,
            }
        elif csv_type == "mt4":
            kw = {"names": self.standard_cols}
        elif csv_type == "standard":
            kw = {"index_col": 0}
        else:
            raise KeyError

        df = pd.read_csv(path, **kw)

        if csv_type == "mt5":
            # removing seconds
            try:
                df["Time"] = df["Time"].apply(lambda x: x.rsplit(":", 1)[0])
            # mt5 daily exports doesn't have time column!!
            except AttributeError:
                # trying to add Time Column with default value
                new = [x for x in self.standard_cols if x != "Time"]
                new.append("Spread")
                df = df.rename(columns={x: y for x, y in zip(self.standard_cols, new)})
                df["Time"] = "00:00"

        df = self._merge_datetime(df)
        return df

    @staticmethod
    def _merge_datetime(df):
        df["DateTime"] = ""
        df["DateTime"] = df.apply(lambda row: f"{row['Date']} {row['Time']}", axis=1)
        df["DateTime"] = pd.to_datetime(df["DateTime"], format=r"%Y.%m.%d %H:%M")
        return df

    def save_to_csv(self, path, df=None):
        if not df:
            df = self.df
        df.to_csv(path)

    def get_df(self):
        return self.df
