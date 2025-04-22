import asyncio
import os
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional, Tuple

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar, Grid, Line
from pyppeteer import launch
from pyppeteer.browser import Browser
from tqdm import tqdm

from utils.chart.snapshot import make_snapshot
from utils.config import ChartConfig
from utils.log import logger


class KlineDrawer(ABC):
    def __init__(self, stock_name: str, width: int, height: int, config: ChartConfig):
        self.stock_name = stock_name
        self.df = None
        self.output_image_folder = None
        self.indices_list = None

        self.width = width
        self.height = height
        self.config = config

    def _preprocess_data(self):
        self.df["index"] = range(len(self.df))
        self.df["rise"] = self.df[["open", "close"]].apply(lambda x: 1 if x.iloc[0] < x.iloc[1] else -1, axis=1)
        self.df["Boll_Lower"] = self.df["Boll_Lower"].round(2)
        self.df["Boll_Upper"] = (self.df["Boll_Upper"] - self.df["Boll_Lower"]).round(2)
        self.df["Boll_Mid"] = self.df["Boll_Mid"].round(2)

        self.indices_list = self.get_indices_list(len(self.df))

    @abstractmethod
    def get_indices_list(self, n: int) -> List[List[int]]:
        pass

    @abstractmethod
    async def draw_single_kline(self, indices: List[int]) -> Tuple[Line, Bar]:
        pass

    @asynccontextmanager
    async def managed_browser(self) -> AsyncGenerator[Browser, None]:
        browser = None
        try:
            browser = await launch({"headless": True}, args=["--no-sandbox"])
            yield browser
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception as e:
                    logger.error(f"Error while closing browser: {str(e)}")

    async def draw_kline_chunk(self, chunk: List[List[int]], browser: Browser) -> List[str]:
        image_files = []
        for indices in tqdm(chunk, desc="Drawing K-line chunk"):
            name_prefix = f"{indices[0]:04d}_{indices[1]:04d}_{indices[2]:04d}"

            try:
                image_path = os.path.join(self.output_image_folder, f"kline_{name_prefix}.png")

                if not os.path.exists(image_path):
                    overlap_kline_line, bar = await self.draw_single_kline(indices)
                    grid_chart = Grid(
                        init_opts=opts.InitOpts(
                            animation_opts=opts.AnimationOpts(animation=False),
                            width=f"{self.width // 2}px",
                            height=f"{self.height // 2}px",
                            bg_color="#fff",
                        )
                    )
                    grid_chart.add(
                        overlap_kline_line,
                        grid_opts=opts.GridOpts(
                            pos_left="10%",
                            pos_top="8%",
                            pos_right="8%",
                            height="50%",
                        ),
                    )
                    grid_chart.add(
                        bar,
                        grid_opts=opts.GridOpts(
                            pos_left="10%",
                            pos_top="60%",
                            pos_right="8%",
                            height="16%",
                        ),
                    )
                    grid_chart.js_host = self.config.js_host

                    html_path = os.path.join(self.output_image_folder, f"render_{name_prefix}.html")
                    await make_snapshot(browser, grid_chart.render(html_path), image_path)
                    os.remove(html_path)

                image_files.append(image_path)

            except Exception as e:
                logger.error(e)
                raise Exception(f"Error during single K-line drawing process at index {name_prefix}: {str(e)}")

        return image_files

    async def draw_kline(self, df: pd.DataFrame, output_image_folder: str) -> Optional[List[str]]:
        self.df = df
        self.output_image_folder = output_image_folder
        self._preprocess_data()

        chunks = [[] for _ in range(self.config.workers)]
        i_worker = 0
        for indices in self.indices_list:
            chunks[i_worker].append(indices)
            i_worker = (i_worker + 1) % self.config.workers

        image_files = []

        async with self.managed_browser() as browser:
            tasks = [self.draw_kline_chunk(chunk, browser) for chunk in chunks]
            all_image_files = await asyncio.gather(*tasks, return_exceptions=True)

            for result in all_image_files:
                if isinstance(result, Exception):
                    logger.error(f"Task Error: {result}")
                else:
                    image_files.extend(result)

        image_files.sort()
        return image_files
