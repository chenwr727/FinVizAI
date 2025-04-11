import os
import re
import shutil
from typing import List

import pandas as pd

from core.llm import LLMClient
from core.schemas import StockBase
from utils.chart import draw_kline
from utils.config import TTSConfig, VideoConfig
from utils.data import calc_indicators, get_stock_data
from utils.log import logger
from utils.report import generate_report_frames
from utils.video import create_video


class StockVideo:
    def __init__(self, llm: LLMClient, output_dir: str = "output"):
        self.llm = llm
        self.output_dir = output_dir

    def get_hist_data(self, stock: StockBase) -> pd.DataFrame:
        df = get_stock_data(
            symbol=stock.symbol,
            start_date=stock.start_date,
            end_date=stock.end_date,
            adjust=stock.adjust,
            period=stock.period,
        )
        df = calc_indicators(df)
        return df

    def _format_text(self, text: str) -> List[str]:
        contents = []
        for s in text.split("｜"):
            if s.strip():
                s = re.sub(r"\[\^\d+\]", "", s.strip())
                contents.append(s)
        return contents

    def _create_output_dir(self, output_dir: str, floder: str):
        output_folder = os.path.join(output_dir, floder)
        os.makedirs(output_folder, exist_ok=True)
        return output_folder

    def _clean_output_dir(self, output_dir: str):
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

    async def generate_video(
        self, stock: StockBase, tts_config: TTSConfig, video_config: VideoConfig, force: bool = False
    ):
        if force:
            self._clean_output_dir(self.output_dir)

        output_dir = os.path.join(self.output_dir, stock.symbol, stock.period)
        os.makedirs(output_dir, exist_ok=True)
        output_video_file = os.path.join(output_dir, "output.mp4")
        if os.path.exists(output_video_file):
            logger.info(f"Video already exists, skipping: {output_video_file}")
            return

        logger.info(f"Start processing stock: {stock.symbol} {stock.period}")
        df = self.get_hist_data(stock)

        logger.info(f"Analyzing stock: {stock.symbol} {stock.period}")
        report, copywriter = self.llm.get_analysis(stock.name, stock.symbol, df, output_dir)
        contents = self._format_text(copywriter)
        title = ""

        logger.info(f"Drawing kline for stock: {stock.symbol} {stock.period}")
        output_image_folder = self._create_output_dir(output_dir, "images")
        image_files = await draw_kline(stock.name, df, output_image_folder)

        logger.info(f"Generating report image for stock: {stock.symbol} {stock.period}")
        report_image_folder = self._create_output_dir(output_dir, "reports")
        report_frames = await generate_report_frames(report, image_files[0], report_image_folder)

        logger.info(f"Generating audio for stock: {stock.symbol} {stock.period}")
        output_audio_folder = self._create_output_dir(output_dir, "audios")
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
        await create_video(report_frames, image_files, title, subtitles, video_config, output_video_file)

        logger.info(f"Video created: {output_video_file}")
