import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, List, Optional

import pandas as pd
from pyecharts.charts import Grid
from pyppeteer import launch
from pyppeteer.browser import Browser
from tqdm import tqdm

from utils.chart.kline import (
    draw_single_kline_by_bg,
    draw_single_kline_by_windows,
    get_indices_list_by_bg,
    get_indices_list_by_windows,
)
from utils.chart.snapshot import make_snapshot
from utils.config import ChartSource, config
from utils.log import logger


@asynccontextmanager
async def managed_browser() -> AsyncGenerator[Browser, None]:
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


async def draw_kline_chunk(
    indices_list: List[int],
    stock_name: str,
    df: pd.DataFrame,
    output_image_folder: str,
    browser: Browser,
    fun_draw: Callable,
) -> List[str]:
    image_files = []
    for indices in tqdm(indices_list, desc="Drawing K-line chunk"):
        name_prefix = f"{indices[0]:04d}_{indices[1]:04d}_{indices[2]:04d}"
        try:
            image_path = os.path.join(output_image_folder, f"kline_{name_prefix}.png")
            if not os.path.exists(image_path):
                grid_chart: Grid = await fun_draw(indices, stock_name, df)
                html_path = os.path.join(output_image_folder, f"render_{name_prefix}.html")
                grid_chart.js_host = config.chart.js_host
                await make_snapshot(browser, grid_chart.render(html_path), image_path)
                os.remove(html_path)
            image_files.append(image_path)
        except Exception as e:
            logger.error(e)
            raise Exception(f"Error during single K-line drawing process at index {name_prefix}: {str(e)}")
    return image_files


async def draw_kline(stock_name: str, df: pd.DataFrame, output_image_folder: str) -> Optional[List[str]]:
    if config.chart.source == ChartSource.windows:
        indices_list = get_indices_list_by_windows(len(df), config.chart.windows)
        fun_draw = draw_single_kline_by_windows
    elif config.chart.source == ChartSource.bg:
        indices_list = get_indices_list_by_bg(len(df))
        fun_draw = draw_single_kline_by_bg
    else:
        raise ValueError(f"Invalid chart source: {config.chart.source}")

    chunks = [[] for _ in range(config.chart.workers)]
    i_worker = 0
    for indices in indices_list:
        chunks[i_worker].append(indices)
        i_worker = (i_worker + 1) % config.chart.workers

    df["index"] = range(len(df))
    df["rise"] = df[["open", "close"]].apply(lambda x: 1 if x.iloc[0] < x.iloc[1] else -1, axis=1)

    image_files = []

    async with managed_browser() as browser:
        tasks = [draw_kline_chunk(chunk, stock_name, df, output_image_folder, browser, fun_draw) for chunk in chunks]
        all_image_files = await asyncio.gather(*tasks, return_exceptions=True)

        for result in all_image_files:
            if isinstance(result, Exception):
                logger.error(f"Task Error: {result}")
            else:
                image_files.extend(result)

    image_files.sort()
    return image_files
