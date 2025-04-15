import pandas as pd
import requests

from .base import DataFetcher


class StockDataFetcher(DataFetcher):

    def get_hist_data(self) -> pd.DataFrame:
        market_code = 1 if self.symbol.startswith("6") else 0
        adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
        period_dict = {"daily": "101", "weekly": "102", "monthly": "103", "hourly": "60"}
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "klt": period_dict[self.period],
            "fqt": adjust_dict[self.adjust],
            "secid": f"{market_code}.{self.symbol}",
            "beg": self.start_date,
            "end": self.end_date,
        }
        r = requests.get(url, params=params, timeout=self.timeout)
        data_json = r.json()
        if not (data_json["data"] and data_json["data"]["klines"]):
            return pd.DataFrame()
        temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
        temp_df.columns = [
            "date",
            "open",
            "close",
            "high",
            "low",
            "volume",
            "amount",
            "amplitude",
            "rise_fall",
            "rise_fall_amount",
            "turnover_rate",
        ]
        for col in temp_df.columns[1:]:
            temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
        return temp_df
