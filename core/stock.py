import json
import os
import re
import shutil
from typing import List

import pandas as pd

from core.llm import LLMClient
from core.schemas import LLMResponse, StockBase
from utils.chart import draw_kline
from utils.config import TTSConfig, VideoConfig
from utils.data import calc_indicators, get_stock_data
from utils.log import logger
from utils.video import create_video


class StockVideo:
    def __init__(self, llm: LLMClient, output_dir: str = "output"):
        self.llm = llm
        self.stock = None
        self.output_dir = output_dir

    def get_hist_data(self, stock: StockBase) -> pd.DataFrame:
        self.stock = stock
        df = get_stock_data(
            symbol=self.stock.symbol,
            start_date=self.stock.start_date,
            end_date=self.stock.end_date,
            adjust=self.stock.adjust,
            period=self.stock.period,
        )
        df = calc_indicators(df)
        self.output_dir = os.path.join(self.output_dir, self.stock.symbol, self.stock.period)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        return df

    def llm_analysis(self, df: pd.DataFrame) -> LLMResponse:
        response = self.llm.get_analysis(self.stock.name, self.stock.symbol, df)
        output_response_file = os.path.join(self.output_dir, "llm_response.json")
        with open(output_response_file, "w") as f:
            json.dump(response.model_dump(), f, indent=4, ensure_ascii=False)
        return response

    def _format_text(self, text: str) -> List[str]:
        contents = []
        for s in text.split("｜"):
            if s.strip():
                s = re.sub(r"\[\^\d+\]", "", s.strip())
                contents.append(s)
        return contents

    def _clean_output_dir(self, output_dir: str):
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

    async def generate_video(self, stock: StockBase, tts_config: TTSConfig, video_config: VideoConfig):
        logger.info(f"Start processing stock: {stock.symbol} {stock.period}")
        df = self.get_hist_data(stock)

        logger.info(f"Analyzing stock: {stock.symbol} {stock.period}")
        response = self.llm_analysis(df)
        contents = self._format_text(response.text)
        title = contents.pop(0)

        logger.info(f"Drawing kline for stock: {stock.symbol} {stock.period}")
        output_image_folder = os.path.join(self.output_dir, "images")
        self._clean_output_dir(output_image_folder)
        image_files = await draw_kline(self.stock.name, df, output_image_folder)

        logger.info(f"Generating audio for stock: {stock.symbol} {stock.period}")
        output_audio_folder = os.path.join(self.output_dir, "audios")
        self._clean_output_dir(output_audio_folder)
        if tts_config.source == "dashscope":
            from core.tts.dashscope import DashscopeTextToSpeechConverter

            converter = DashscopeTextToSpeechConverter(
                tts_config.dashscope.api_key,
                tts_config.dashscope.model,
                tts_config.dashscope.voices,
                output_audio_folder,
            )
        elif tts_config.source == "hailuo":
            from core.tts.hailuo import HaiLuoTextToSpeechConverter

            converter = HaiLuoTextToSpeechConverter(
                tts_config.hailuo.api_key,
                tts_config.hailuo.base_url,
                tts_config.hailuo.voices,
                output_audio_folder,
            )
        else:
            raise ValueError(f"Invalid tts source: {tts_config.source}")
        subtitles = await converter.text_to_speech(contents)

        logger.info(f"Creating video for stock: {stock.symbol} {stock.period}")
        output_video_file = os.path.join(self.output_dir, "output.mp4")
        await create_video(image_files, title, subtitles, video_config, output_video_file)
