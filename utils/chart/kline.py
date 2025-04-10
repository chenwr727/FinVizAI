import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar, Grid, Kline, Line
from pyppeteer import launch
from pyppeteer.browser import Browser
from tqdm import tqdm

from utils.chart.snapshot import make_snapshot
from utils.config import config
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


async def draw_single_kline(i: int, stock_name: str, df: pd.DataFrame, output_image_folder: str, browser: Browser):
    try:
        dates = df["date"].tolist()
        kline_data = df[["open", "close", "low", "high"]]
        volume_data = df[["index", "volume", "rise"]]

        bb_lower_data = df["Boll_Lower"].round(2)
        bb_upper_data = (df["Boll_Upper"] - df["Boll_Lower"]).round(2)
        bb_middle_data = df["Boll_Mid"].round(2)

        current_kline = kline_data.iloc[: i + 1]
        current_volume = volume_data.iloc[: i + 1]

        bb_line = (
            Line()
            .add_xaxis(dates)
            .add_yaxis(
                series_name="Boll Lower",
                y_axis=bb_lower_data.tolist(),
                is_smooth=True,
                is_symbol_show=False,
                linestyle_opts=opts.LineStyleOpts(opacity=0),
                stack="Boll",
                symbol=None,
            )
            .add_yaxis(
                series_name="Boll Upper",
                y_axis=bb_upper_data.tolist(),
                is_smooth=True,
                is_symbol_show=False,
                linestyle_opts=opts.LineStyleOpts(opacity=0),
                areastyle_opts=opts.AreaStyleOpts(color="#ccc", opacity=0.2),
                stack="Boll",
                symbol=None,
            )
            .add_yaxis(
                series_name="Boll Middle",
                y_axis=bb_middle_data.tolist(),
                is_smooth=True,
                is_symbol_show=False,
                linestyle_opts=opts.LineStyleOpts(opacity=0.2),
                itemstyle_opts=opts.ItemStyleOpts(color="#999"),
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(is_scale=True),
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitarea_opts=opts.SplitAreaOpts(is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)),
                ),
                title_opts=opts.TitleOpts(
                    title=f"{stock_name} Boll & Kline",
                    subtitle=f"{dates[0]}~{dates[-1]}",
                    pos_top="1%",
                    pos_left="center",
                ),
                visualmap_opts=opts.VisualMapOpts(
                    is_show=False,
                    dimension=2,
                    series_index=5,
                    is_piecewise=True,
                    pieces=[
                        {"value": 1, "color": "rgba(239, 35, 42, 0.2)"},
                        {"value": -1, "color": "rgba(20, 177, 67, 0.2)"},
                    ],
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                ),
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )

        kline = (
            Kline()
            .add_xaxis(dates)
            .add_yaxis(
                series_name="",
                y_axis=kline_data.values.tolist(),
                itemstyle_opts=opts.ItemStyleOpts(
                    color="rgba(239, 35, 42, 0.2)",
                    color0="rgba(20, 177, 67, 0.2)",
                    border_color="rgba(239, 35, 42, 0.3)",
                    border_color0="rgba(20, 177, 67, 0.3)",
                ),
            )
            .add_yaxis(
                series_name="",
                y_axis=current_kline.values.tolist(),
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#ef232a",
                    color0="#14b143",
                    border_color="#ef232a",
                    border_color0="#14b143",
                ),
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    grid_index=0,
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=0,
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )

        overlap_kline_line = bb_line.overlap(kline)

        bar = (
            Bar()
            .add_xaxis(dates)
            .add_yaxis(
                series_name="volume",
                y_axis=volume_data.values.tolist(),
                xaxis_index=1,
                yaxis_index=1,
                label_opts=opts.LabelOpts(is_show=False),
                bar_width="50%",
                gap="-100%",
            )
            .add_yaxis(
                series_name="volume",
                y_axis=current_volume.values.tolist(),
                xaxis_index=1,
                yaxis_index=1,
                label_opts=opts.LabelOpts(is_show=False),
                bar_width="50%",
                gap="-100%",
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    is_scale=True,
                    grid_index=1,
                    boundary_gap=True,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                    axislabel_opts=opts.LabelOpts(is_show=False),
                    min_="dataMin",
                    max_="dataMax",
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=1,
                    is_scale=True,
                    split_number=2,
                    axislabel_opts=opts.LabelOpts(is_show=False),
                    axisline_opts=opts.AxisLineOpts(is_show=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                ),
                legend_opts=opts.LegendOpts(is_show=False),
                visualmap_opts=opts.VisualMapOpts(
                    is_show=False,
                    dimension=2,
                    series_index=6,
                    is_piecewise=True,
                    pieces=[
                        {"value": 1, "color": "#ef232a"},
                        {"value": -1, "color": "#14b143"},
                    ],
                ),
            )
        )

        grid_chart = Grid(
            init_opts=opts.InitOpts(
                animation_opts=opts.AnimationOpts(animation=False),
                width=f"{config.video.width // 2}px",
                height=f"{config.video.height // 2}px",
                bg_color="#fff",
            )
        )
        grid_chart.add(
            overlap_kline_line, grid_opts=opts.GridOpts(pos_left="10%", pos_top="8%", pos_right="8%", height="50%")
        )
        grid_chart.add(bar, grid_opts=opts.GridOpts(pos_left="10%", pos_top="60%", pos_right="8%", height="16%"))

        image_path = os.path.join(output_image_folder, f"kline_{i+1:03d}.png")
        html_path = os.path.join(output_image_folder, f"render_{i+1:03d}.html")
        grid_chart.js_host = config.js.js_host
        await make_snapshot(browser, grid_chart.render(html_path), image_path)

        return image_path

    except Exception as e:
        raise Exception(f"Error during single K-line drawing process at index {i}: {str(e)}")


async def draw_kline_chunk(
    indices: List[int], stock_name: str, df: pd.DataFrame, output_image_folder: str, browser: Browser
) -> List[str]:
    image_files = []
    for i in tqdm(indices, desc=f"Drawing K-line chunk {indices[0]}"):
        try:
            image_path = await draw_single_kline(i, stock_name, df, output_image_folder, browser)
            if image_path:
                image_files.append(image_path)
        except Exception as e:
            logger.error(e)
    return image_files


async def draw_kline(
    stock_name: str, df: pd.DataFrame, output_image_folder: str, workers: int = 4
) -> Optional[List[str]]:
    chunks = [[] for _ in range(workers)]
    i_worker = 0
    for i in range(-1, len(df)):
        chunks[i_worker].append(i)
        i_worker = (i_worker + 1) % workers

    df["index"] = range(len(df))
    df["rise"] = df[["open", "close"]].apply(lambda x: 1 if x.iloc[0] < x.iloc[1] else -1, axis=1)

    image_files = []

    async with managed_browser() as browser:
        tasks = [draw_kline_chunk(chunk, stock_name, df, output_image_folder, browser) for chunk in chunks]
        all_image_files = await asyncio.gather(*tasks, return_exceptions=True)

        for result in all_image_files:
            if isinstance(result, Exception):
                logger.error(f"Task Error: {result}")
            else:
                image_files.extend(result)

    image_files.sort()
    return image_files
