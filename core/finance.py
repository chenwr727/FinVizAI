import os
import shutil

from core.fetcher.base import DataFetcher
from core.llm import FuturesLLMClient, StockLLMClient
from utils.config import ChartSource, Config, TTSSource
from utils.log import logger
from utils.report import generate_report_frames
from utils.video import create_video


class FinanceVideo:
    def __init__(self, fetcher: DataFetcher, config: Config, source: str = "stock", output_dir: str = "output"):
        self.fetcher = fetcher
        self.config = config
        self.output_dir = output_dir

        self.drawer = None
        self.llm = None
        self.tts = None

        self._preprocess_by_config(source)

    def _preprocess_by_config(self, source: str):
        if self.config.chart.source == ChartSource.bg:
            from core.kline.bg import BgKlineDrawer

            drawer = BgKlineDrawer
        elif self.config.chart.source == ChartSource.windows:
            from core.kline.windows import WindowsKlineDrawer

            drawer = WindowsKlineDrawer
        else:
            raise ValueError(f"Invalid chart source: {self.config.chart.source}")
        self.drawer = drawer(self.fetcher.name, self.config.video.width, self.config.video.height, self.config.chart)

        if source == "stock":
            llm_client = StockLLMClient
        elif source == "futures":
            llm_client = FuturesLLMClient
        else:
            raise ValueError(f"Invalid llm source: {source}")
        self.llm = llm_client(self.config.llm)

        if self.config.tts.source == TTSSource.dashscope:
            from core.tts.dashscope import DashscopeTextToSpeechConverter

            self.tts = DashscopeTextToSpeechConverter(self.config.tts.dashscope)
        elif self.config.tts.source == TTSSource.hailuo:
            from core.tts.hailuo import HaiLuoTextToSpeechConverter

            self.tts = HaiLuoTextToSpeechConverter(self.config.tts.hailuo)
        else:
            raise ValueError(f"Invalid tts source: {self.config.tts.source}")

    def _create_output_dir(self, output_dir: str, floder: str):
        output_folder = os.path.join(output_dir, floder)
        os.makedirs(output_folder, exist_ok=True)
        return output_folder

    def _clean_output_dir(self, output_dir: str):
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

    async def generate_video(self, force: bool = False):
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
        image_files = await self.drawer.draw_kline(df, output_image_folder)

        logger.info(f"Analyzing stock: {self.fetcher.symbol} {self.fetcher.period}")
        report, contents = self.llm.get_analysis(self.fetcher.name, self.fetcher.symbol, df, output_dir)
        title = contents.pop(0)

        logger.info(f"Generating report image for stock: {self.fetcher.symbol} {self.fetcher.period}")
        report_image_folder = self._create_output_dir(output_dir, "reports")
        report_frames = await generate_report_frames(report, image_files[0], report_image_folder)

        logger.info(f"Generating audio for stock: {self.fetcher.symbol} {self.fetcher.period}")
        output_audio_folder = self._create_output_dir(output_dir, "audios")
        subtitles = await self.tts.text_to_speech(contents, output_audio_folder)

        logger.info(f"Creating video for stock: {self.fetcher.symbol} {self.fetcher.period}")
        await create_video(report_frames, image_files, title, subtitles, self.config.video, output_video_file)

        logger.info(f"Video created: {output_video_file}")
