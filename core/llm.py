import datetime
import re
from typing import Optional, Tuple

import pandas as pd
from openai import OpenAI

from core.schemas import LLMResponse
from utils.config import config

SYSTEM_PROMPT = """你是一位专业的财经内容创作者，请根据以下个股资讯与走势数据，撰写一段用于TTS语音播放的个股分析文案。请严格遵循以下要求：

- 总长度控制在300字以内；
- 第一条句子为**标题**，简洁明了，概括全文重点；
- 正文内容结构为：**开头导语 → 趋势分析（必须包含K线形态、MACD状态、布林带位置、RSI14等解读）→ 操作建议 → 风险提示**，但文案中不体现结构标题；
- 趋势分析部分需包含以下要素：  
  - K线当前形态及变化趋势  
  - MACD指标（金叉死叉 柱体增减）  
  - 布林带形态（收敛开口 价格与轨道关系）  
  - 资讯解读（简要提炼利好或利空消息，并与当前价格变化做逻辑连接）；
- 每句话需表达**一个完整独立的意思**，且中间没有空格；
- 所有句子使用**“｜”**作为分隔符；
- 内容必须**逻辑连贯、语言自然、朗读友好**，适合普通听众理解；
- 不允许使用投资建议类词语，例如“建议买入”“值得布局”等；
- 内容必须基于实际走势和数据分析，不可主观臆断或夸张判断；
- 严禁使用任何标点符号、引号、引用或动作说明；
- 表达方式需自然口语化，专业但不生硬；"""


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

    def _extract_type(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        match = re.search(r"^\[(.+?)\](.*)", text, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def get_analysis(self, name: str, symbol: str, df: pd.DataFrame) -> LLMResponse:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        messages = [
            {
                "role": "user",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"\n# 现在时间是{current_time}，{name}({symbol})走势数据如下：{df.to_dict(orient='records')}"
                + f"\n\n请联网搜索{name}({symbol})的最新资讯"
                + "\n\n请输出一段结构完整 句句独立 语义连贯的分析文案 用“｜”分隔每句话 不添加任何解释说明 不使用标点和引用",
            },
        ]

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
            if key is not None and key in result_dict:
                result_dict[key] += value
                continue
        return LLMResponse(**result_dict)
