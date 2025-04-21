from typing import List

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar, Grid, Kline, Line

from utils.config import config


def get_indices_list_by_windows(n: int, windows: int = 100, step: int = 3) -> List[List[int]]:
    indices = []
    index = 0
    for i in range(n, windows - 1, -step):
        indices.append([index, 0, i])
        index += 1
    for j in range(n - windows + 1):
        if j + windows == i:
            continue
        indices.append([index, j, j + windows])
        index += 1
    for k in range(n - windows - 1, -1, -step):
        indices.append([index, k, n])
        index += 1
    if k != 0:
        indices.append([index, 0, n])
    return indices


async def draw_single_kline_by_windows(indices: List[int], stock_name: str, df: pd.DataFrame) -> Grid:
    index_start = indices[1]
    index_end = indices[2]

    dates = df["date"].iloc[index_start:index_end].tolist()
    kline_data = df[["open", "close", "low", "high"]]
    volume_data = df[["index", "volume", "rise"]]

    bb_lower_data = df["Boll_Lower"].round(2)
    bb_upper_data = (df["Boll_Upper"] - df["Boll_Lower"]).round(2)
    bb_middle_data = df["Boll_Mid"].round(2)

    current_kline = kline_data.iloc[index_start:index_end]
    current_volume = volume_data.iloc[index_start:index_end]

    current_bb_lower_data = bb_lower_data.iloc[index_start:index_end]
    current_bb_upper_data = bb_upper_data.iloc[index_start:index_end]
    current_bb_middle_data = bb_middle_data.iloc[index_start:index_end]

    bb_line = (
        Line()
        .add_xaxis(dates)
        .add_yaxis(
            series_name="Boll Lower",
            y_axis=current_bb_lower_data.tolist(),
            is_smooth=True,
            is_symbol_show=False,
            linestyle_opts=opts.LineStyleOpts(opacity=0),
            stack="Boll",
            symbol=None,
        )
        .add_yaxis(
            series_name="Boll Upper",
            y_axis=current_bb_upper_data.tolist(),
            is_smooth=True,
            is_symbol_show=False,
            linestyle_opts=opts.LineStyleOpts(opacity=0),
            areastyle_opts=opts.AreaStyleOpts(color="#ccc", opacity=0.2),
            stack="Boll",
            symbol=None,
        )
        .add_yaxis(
            series_name="Boll Middle",
            y_axis=current_bb_middle_data.tolist(),
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
                series_index=4,
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
    return grid_chart
