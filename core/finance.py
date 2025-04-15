import os
import shutil

from core.fetcher.base import DataFetcher
from core.llm import FuturesLLMClient, StockLLMClient
from core.llm.base import LLMClient
from utils.chart import draw_kline
from utils.config import TTSConfig, VideoConfig
from utils.log import logger
from utils.report import generate_report_frames
from utils.video import create_video

SOURCE_DICT = {
    "stock": StockLLMClient,
    "futures": FuturesLLMClient,
}


class FinanceVideo:
    def __init__(self, fetcher: DataFetcher, source: str = "stock", output_dir: str = "output"):
        self.fetcher = fetcher
        self.output_dir = output_dir

        if source not in SOURCE_DICT:
            raise ValueError(f"Invalid source: {source}")
        self.llm: LLMClient = SOURCE_DICT[source]()

    def _create_output_dir(self, output_dir: str, floder: str):
        output_folder = os.path.join(output_dir, floder)
        os.makedirs(output_folder, exist_ok=True)
        return output_folder

    def _clean_output_dir(self, output_dir: str):
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

    async def generate_video(self, tts_config: TTSConfig, video_config: VideoConfig, force: bool = False):
        output_dir = os.path.join(self.output_dir, self.fetcher.symbol, self.fetcher.period)
        if force:
            self._clean_output_dir(output_dir)

        os.makedirs(output_dir, exist_ok=True)
        output_video_file = os.path.join(output_dir, "output.mp4")
        if os.path.exists(output_video_file):
            logger.info(f"Video already exists, skipping: {output_video_file}")
            return

        logger.info(f"Start processing stock: {self.fetcher.symbol} {self.fetcher.period}")
        df = self.fetcher.get_data()

        logger.info(f"Drawing kline for stock: {self.fetcher.symbol} {self.fetcher.period}")
        output_image_folder = self._create_output_dir(output_dir, "images")
        image_files = await draw_kline(self.fetcher.name, df, output_image_folder)

        logger.info(f"Analyzing stock: {self.fetcher.symbol} {self.fetcher.period}")
        report, contents = self.llm.get_analysis(self.fetcher.name, self.fetcher.symbol, df, output_dir)
        title = ""

        logger.info(f"Generating report image for stock: {self.fetcher.symbol} {self.fetcher.period}")
        report_image_folder = self._create_output_dir(output_dir, "reports")
        report_frames = await generate_report_frames(report, image_files[0], report_image_folder)

        logger.info(f"Generating audio for stock: {self.fetcher.symbol} {self.fetcher.period}")
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

        logger.info(f"Creating video for stock: {self.fetcher.symbol} {self.fetcher.period}")
        await create_video(report_frames, image_files, title, subtitles, video_config, output_video_file)

        logger.info(f"Video created: {output_video_file}")
