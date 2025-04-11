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

NEWS_PROMPT = """你是一位财经分析师助理，系统性搜索并提炼出“{name}({symbol})”最新资讯与行业相关信息，内容应涵盖以下几个维度：

### 📌 输出格式：

请使用以下结构输出信息，不使用多余描述：

```markdown
# {name}综合分析报告

**最新公告摘要**：（近7日）
- 

**行业动态**：（近1个月，与该公司相关）
- 

**上下游变动或供需逻辑信息**：
- 

**财报或业绩快报要点**：（如有）
- 

**媒体报道亮点**：（包括利好或争议）
- 

**政策或监管信息**：（若有）
- 
```

### 📌 搜索范围与建议关键词：

请使用以下关键词组合搜索相关内容：

- 【公司简称】+ 公告｜新闻｜最新动态｜股吧消息
- 【行业名】+ 行情｜政策｜监管｜扩产｜原材料价格
- 【公司简称】+ 上游｜下游｜产业链｜供需
- 【公司简称】+ 业绩快报｜财报｜营收｜净利润
- 【公司简称】+ 投资者关系｜媒体｜热点｜解读

### 📌 输出要求：

- 信息必须**简洁、准确、可直接用于分析写作**
- 每条内容控制在1-2句话内，避免堆砌
- 不得引用全文、不得加入无关评论
- 内容必须为**近一个月内信息**
- 内容**严禁使用引用编号“”**
- 内容**严禁使用分隔线“---”**
- 内容**严禁输出结构中括号内的备注（近7日、如有等）**"""

TREND_PROMPT = """你是一位财经分析师助理，请根据以下个股信息趋势分析，输出结构化、简洁、准确的趋势分析内容。

### 📌 输出结构如下：  
（仅输出内容本身，括号内为指导备注，不得在结果中体现）

```markdown
**趋势分析**（根据提供的近一年走势数据，从技术面角度综合分析，必须包含以下内容）：
- K线形态（如：多头排列、阴阳交替、高位震荡、孕线等）  
- MACD状态（是否金叉或死叉、柱体放大或缩小）  
- 布林带（是否收口或开口、价格所处位置）  
- RSI14状态（是否超买、超卖、背离等）  
- 均线系统（短中长期均线的排列、支撑阻力情况）  
- 成交量变化（是否放量、缩量、量价配合）
```

### 📌 输出要求：

- 每条内容控制在1-2句话内，避免堆砌
- 不得出现括号内的备注文字或任何提示语；
- 所有数据分析基于你所提供的信息进行判断，不主观推测；
- “趋势分析”部分为**纯技术面解读，不含主观预测词汇**；

现在时间是{current_time}，{name}({symbol})走势数据如下：{datas}"""

COPYWIRTER_PROMPT = """你是一位财经内容创作者  
请根据上文的个股资讯分析与趋势分析内容  
生成一段**用于播客的个股分析文案**

---

### 📌 输出结构（共四段）：

1. **开篇导语**：简洁介绍公司及所属方向  
2. **资讯摘要**：概括公司最新公告、行业动态、财报、上下游或政策信息  
3. **趋势分析**：从技术面角度解读K线形态、MACD状态、布林带位置、RSI指标、量能等  
4. **走势提示**：以中性语气对整体走势节奏做简短总结，**不得使用投资建议性语言**

---

### 📌 输出格式规范：

- 总长度不得超过**300字**  
- 每句话需表达**一个完整独立的意思**  
- 每句话之间用中文竖线 **“｜”** 分隔  
- 每句话中间不得出现空格  
- 所有内容需逻辑连贯、口语化、朗读自然、听感友好  
- 内容必须**完全基于提供的信息撰写**，禁止添加主观判断或投资倾向  
- 严禁出现任何引用、括号、动作说明等  
- 返回结果中**仅包含播客文案内容本身**，不包含任何解释说明或结构标记
"""


class LLMClient:

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
        messages = [{"role": "user", "content": NEWS_PROMPT.format(name=name, symbol=symbol)}]
        return self.get_response(messages)

    def get_trend(self, name: str, symbol: str, df: pd.DataFrame) -> LLMResponse:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        messages = [
            {
                "role": "user",
                "content": TREND_PROMPT.format(
                    current_time=current_time, name=name, symbol=symbol, datas=df.to_markdown()
                ),
            }
        ]
        return self.get_response(messages)

    def get_copywriter(self) -> LLMResponse:
        messages = [{"role": "user", "content": COPYWIRTER_PROMPT}]
        return self.get_response(messages)

    def get_analysis(self, name: str, symbol: str, df: pd.DataFrame, output_dir: str) -> Tuple[str, str]:
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
        return report, copywriter_response.text
