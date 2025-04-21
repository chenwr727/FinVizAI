import datetime
import json
import os
import random
import re
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd
from openai import OpenAI

from core.schemas import LLMResponse
from utils.config import config
from utils.log import logger


class LLMClient:
    news_prompt = ""
    trend_prompt = ""
    copywriter_prompt = ""

    def __init__(
        self,
        base_url: str = config.llm.base_url,
        api_key: str = config.llm.api_key,
        model: str = config.llm.model,
        hy_user: str = config.llm.hy_user,
        agent_id: str = config.llm.agent_id,
        chat_id: str = config.llm.chat_id,
        should_remove_conversation: bool = config.llm.should_remove_conversation,
    ):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.extra_body = {
            "hy_source": "web",
            "hy_user": hy_user,
            "agent_id": agent_id,
            "chat_id": chat_id,
            "should_remove_conversation": should_remove_conversation,
        }
        self.should_sleep = False

    def _extract_type(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        match = re.search(r"^\[(.+?)\](.*)", text, re.DOTALL)
        return (match.group(1), match.group(2)) if match else (None, None)

    def _save_response(self, response: LLMResponse, output_file: str) -> None:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response.model_dump(), f, indent=4, ensure_ascii=False)

    def _read_response(self, output_file: str) -> LLMResponse:
        with open(output_file, "r", encoding="utf-8") as f:
            return LLMResponse(**json.load(f))

    def _formatter_code(self, text: str) -> str:
        match = re.search(r"```markdown(.*?)```", text, re.DOTALL)
        content = match.group(1).strip() if match else text.strip()
        return re.sub(r"\[\^\d+\]", "", content)

    def _get_cached_or_fetch(self, method, output_file: str, *args, **kwargs) -> LLMResponse:
        if not os.path.exists(output_file):
            response = method(*args, **kwargs)
            self._save_response(response, output_file)
            if self.should_sleep:
                time.sleep(random.randint(3, 5))
        else:
            response = self._read_response(output_file)
        return response

    def _format_text(self, text: str) -> List[str]:
        contents = []
        for s in text.split("｜"):
            if s.strip():
                s = re.sub(r"\[\^\d+\]", "", s.strip())
                contents.append(s)
        return contents

    def get_response(self, messages: List[Dict[str, str]]) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            extra_body=self.extra_body,
        )

        result_dict = {k: "" for k in LLMResponse.model_fields.keys()}
        for chunk in response:
            content = chunk.choices[0].delta.content
            key, value = self._extract_type(content)
            if key and key in result_dict:
                result_dict[key] += value
        result_dict["chat_id"] = chunk.model
        if result_dict.get("search_with_text"):
            result_dict["search_with_text"] = json.loads(result_dict["search_with_text"])
        return LLMResponse(**result_dict)

    def get_news(self, name: str, symbol: str) -> LLMResponse:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        messages = [
            {"role": "user", "content": self.news_prompt.format(name=name, symbol=symbol, current_date=current_date)}
        ]
        return self.get_response(messages)

    def get_trend(self, name: str, symbol: str, df: pd.DataFrame) -> LLMResponse:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        messages = [
            {
                "role": "user",
                "content": self.trend_prompt.format(
                    current_time=current_time, name=name, symbol=symbol, datas=df.to_markdown()
                ),
            }
        ]
        return self.get_response(messages)

    def get_copywriter(self) -> LLMResponse:
        messages = [{"role": "user", "content": self.copywriter_prompt}]
        return self.get_response(messages)

    def get_analysis(self, name: str, symbol: str, df: pd.DataFrame, output_dir: str) -> Tuple[str, List[str]]:
        news_file = os.path.join(output_dir, "news.json")
        trend_file = os.path.join(output_dir, "trend.json")
        copywriter_file = os.path.join(output_dir, "copywriter.json")

        logger.info("Start fetching news...")
        self.should_sleep = True
        self.extra_body["chat_id"] = ""
        news_response = self._get_cached_or_fetch(self.get_news, news_file, name, symbol)
        report = self._formatter_code(news_response.text)

        logger.info("Start fetching trend...")
        self.extra_body["chat_id"] = news_response.chat_id
        trend_response = self._get_cached_or_fetch(self.get_trend, trend_file, name, symbol, df)
        report += "\n\n" + self._formatter_code(trend_response.text)

        logger.info("Start fetching copywriter...")
        self.should_sleep = False
        copywriter_response = self._get_cached_or_fetch(self.get_copywriter, copywriter_file)

        contents = self._format_text(copywriter_response.text)
        return report, contents
