import re
from functools import lru_cache
from typing import Dict, Tuple

import pandas as pd
import requests

from .base import DataFetcher


class FuturesDataFetcher(DataFetcher):

    def __futures_hist_separate_char_and_numbers_em(self) -> tuple:
        char = re.findall(pattern="[\u4e00-\u9fa5a-zA-Z]+", string=self.symbol)
        numbers = re.findall(pattern=r"\d+", string=self.symbol)
        return char[0], numbers[0]

    @lru_cache()
    def __fetch_exchange_symbol_raw_em(self) -> list:
        url = "https://futsse-static.eastmoney.com/redis"
        params = {"msgid": "gnweb"}
        r = requests.get(url, params=params)
        data_json = r.json()
        all_exchange_symbol_list = []
        for item in data_json:
            params = {"msgid": str(item["mktid"])}
            r = requests.get(url, params=params)
            inner_data_json = r.json()
            for num in range(1, len(inner_data_json) + 1):
                params = {"msgid": str(item["mktid"]) + f"_{num}"}
                r = requests.get(url, params=params)
                inner_data_json = r.json()
                all_exchange_symbol_list.extend(inner_data_json)
        return all_exchange_symbol_list

    @lru_cache()
    def __get_exchange_symbol_map(self) -> Tuple[Dict, Dict, Dict, Dict]:
        all_exchange_symbol_list = self.__fetch_exchange_symbol_raw_em()
        c_contract_mkt = {}
        c_contract_to_e_contract = {}
        e_symbol_mkt = {}
        c_symbol_mkt = {}
        for item in all_exchange_symbol_list:
            c_contract_mkt[item["name"]] = item["mktid"]
            c_contract_to_e_contract[item["name"]] = item["code"]
            e_symbol_mkt[item["vcode"]] = item["mktid"]
            c_symbol_mkt[item["vname"]] = item["mktid"]
        return c_contract_mkt, c_contract_to_e_contract, e_symbol_mkt, c_symbol_mkt

    def _format_date(self, date: str) -> str:
        return date[:4] + "-" + date[4:6] + "-" + date[6:]

    def get_hist_data(self) -> pd.DataFrame:
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
        c_contract_mkt, c_contract_to_e_contract, e_symbol_mkt, c_symbol_mkt = self.__get_exchange_symbol_map()
        try:
            sec_id = f"{c_contract_mkt[self.symbol]}.{c_contract_to_e_contract[self.symbol]}"
        except KeyError:
            symbol_char, _ = self.__futures_hist_separate_char_and_numbers_em()
            if re.match(pattern="^[\u4e00-\u9fa5]+$", string=symbol_char):
                sec_id = str(c_symbol_mkt[symbol_char]) + "." + self.symbol
            else:
                sec_id = str(e_symbol_mkt[symbol_char]) + "." + self.symbol
        params = {
            "secid": sec_id,
            "klt": period_dict[self.period],
            "fqt": "1",
            "lmt": "10000",
            "end": "20500000",
            "iscca": "1",
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "forcect": "1",
        }
        r = requests.get(url, timeout=15, params=params)
        data_json = r.json()
        temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
        temp_df.columns = [
            "date",
            "open",
            "close",
            "high",
            "low",
            "volume",
            "amount",
            "-",
            "rise_fall",
            "rise_fall_amount",
            "_",
            "_",
            "open_interest",
            "_",
        ]
        temp_df = temp_df[
            [
                "date",
                "open",
                "close",
                "high",
                "low",
                "volume",
                "amount",
                "rise_fall",
                "rise_fall_amount",
                "open_interest",
            ]
        ]
        temp_df = temp_df[
            (temp_df["date"] >= self._format_date(self.start_date))
            & (temp_df["date"] <= self._format_date(self.end_date))
        ]
        for col in temp_df.columns[1:]:
            temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
        return temp_df
