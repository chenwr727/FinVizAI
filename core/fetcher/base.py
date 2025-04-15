from abc import ABC, abstractmethod

import pandas as pd


class DataFetcher(ABC):
    def __init__(self, name: str, symbol: str, start_date: str, end_date: str, period: str = "daily", adjust: str = ""):
        self.name = name
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.adjust = adjust
        self.period = period
        self.timeout = None

    def calc_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["index"] = pd.to_datetime(df["date"])
        df.set_index("index", inplace=True)

        df["MA5"] = df["close"].rolling(5).mean()
        df["MA20"] = df["close"].rolling(20).mean()
        df["MA60"] = df["close"].rolling(60).mean()
        df["MA120"] = df["close"].rolling(120).mean()

        df["Boll_Mid"] = df["close"].rolling(20).mean()
        df["Boll_Std"] = df["close"].rolling(20).std()
        df["Boll_Upper"] = df["Boll_Mid"] + 2 * df["Boll_Std"]
        df["Boll_Lower"] = df["Boll_Mid"] - 2 * df["Boll_Std"]

        df["EMA12"] = df["close"].ewm(span=12, adjust=False).mean()
        df["EMA26"] = df["close"].ewm(span=26, adjust=False).mean()
        df["DIF"] = df["EMA12"] - df["EMA26"]

        df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
        df["MACD"] = (df["DIF"] - df["DEA"]) * 2

        df["change"] = df["close"].diff()
        df["gain"] = df["change"].apply(lambda x: x if x > 0 else 0)
        df["loss"] = df["change"].apply(lambda x: -x if x < 0 else 0)

        window = 14
        df["avg_gain"] = df["gain"].rolling(window).mean()
        df["avg_loss"] = df["loss"].rolling(window).mean()
        df["RSI14"] = 100 - (100 / (1 + (df["avg_gain"] / df["avg_loss"])))

        df["VOL5"] = df["volume"].rolling(5).mean()
        df["VOL10"] = df["volume"].rolling(10).mean()

        return df[
            [
                "date",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "MA5",
                "MA20",
                "MA60",
                "MA120",
                "Boll_Upper",
                "Boll_Mid",
                "Boll_Lower",
                "DIF",
                "DEA",
                "MACD",
                "RSI14",
            ]
        ]

    @abstractmethod
    def get_hist_data(self) -> pd.DataFrame:
        pass

    def get_data(self) -> pd.DataFrame:
        df = self.get_hist_data()
        df = self.calc_indicators(df)
        return df
