import pandas as pd


class DFTools:
    _active_columns = []
    _history_columns = []
    _pending_columns = []
    _static_columns = []

    def __init__(self):
        self._history_df = self.new_df(self._history_columns)
        self._active_df = self.new_df(self._active_columns)
        self._pending_df = self.new_df(self._pending_columns)
        self._static_df = self.new_df(self._static_columns)

    @property
    def active_positions(self):
        return self._active_df

    @active_positions.setter
    def active_positions(self, df):
        self._active_df = df

    @property
    def history(self):
        return self._history_df

    @history.setter
    def history(self, df):
        self._history_df = df

    @property
    def pending_orders(self):
        return self._pending_df

    @pending_orders.setter
    def pending_orders(self, df):
        self._pending_df = df

    @property
    def statics(self):
        return self._static_df

    @statics.setter
    def statics(self, df):
        self._static_df = df

    def new_df(self, col_list):
        return pd.DataFrame(columns=col_list)

    def new_dic_record(self, df, dic):
        df = df.append(dic, ignore_index=True)
        return df

    def new_df_record(self, df_src, df):
        df_src = df_src.append(df)
        return df_src

    def search_column(self, df, col, kw):
        row = df.loc[df[col] == kw]
        return row

    def remove_record(self, df, id):
        df = df[df.id != id]
        return df

    def df_len(self, df):
        return df.shape[0]

    def get_history(self):
        return self.history_df

    def col_values(self, df, col):
        return df[col]

    def get_row_index(self, df, row):
        return df.index[df["DateTime"] == row["DateTime"]].tolist()[0]

    def get_row_by_index(self, df, index):
        return df.iloc[[index]]

    def cumsum(self, df, col, new_col):
        series = self.col_values(df, col)
        df[new_col] = series.cumsum()
        return df

    def export_csv(self, df, path, **kwargs):
        df.to_csv(path, **kwargs)
