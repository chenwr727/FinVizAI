import pandas as pd
import requests


def get_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
    adjust: str = "",
    period: str = "daily",
    timeout: float = None,
) -> pd.DataFrame:
    market_code = 1 if symbol.startswith("6") else 0
    adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
    period_dict = {"daily": "101", "weekly": "102", "monthly": "103", "hourly": "60"}
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": period_dict[period],
        "fqt": adjust_dict[adjust],
        "secid": f"{market_code}.{symbol}",
        "beg": start_date,
        "end": end_date,
    }
    r = requests.get(url, params=params, timeout=timeout)
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
    # temp_df["date"] = pd.to_datetime(temp_df["date"], errors="coerce").dt.date
    for col in temp_df.columns[1:]:
        temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
    return temp_df


def calc_indicators(df: pd.DataFrame) -> pd.DataFrame:
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
