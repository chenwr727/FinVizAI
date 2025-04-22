from typing import List, Tuple

from pyecharts import options as opts
from pyecharts.charts import Bar, Kline, Line

from core.kline.base import KlineDrawer
from utils.chart.axis import scale_nice_val
from utils.config import ChartConfig


class WindowsKlineDrawer(KlineDrawer):

    def __init__(self, stock_name: str, width: int, height: int, config: ChartConfig):
        self.volume_split_number = 2
        self.line_max = 0
        self.line_min = 0
        self.volume_max = 0
        self.volume_min = 0

        super().__init__(stock_name, width, height, config)

    def _preprocess_data(self):
        kline_max, kline_min = scale_nice_val(self.df["high"].max(), self.df["low"].min())
        bb_max, bb_min = scale_nice_val(self.df["Boll_Upper"].max(), self.df["Boll_Lower"].min())
        self.line_max = max(kline_max, bb_max)
        self.line_min = min(kline_min, bb_min)

        volume_split_number = 2
        self.volume_max, self.volume_min = scale_nice_val(
            self.df["volume"].max(), self.df["volume"].min(), volume_split_number
        )

        super()._preprocess_data()

    def get_indices_list(self, n: int) -> List[List[int]]:
        indices = []
        index = 0
        for i in range(n, self.config.windows.length - 1, -self.config.windows.step):
            indices.append([index, 0, i])
            index += 1
        for j in range(n - self.config.windows.length + 1):
            if j + self.config.windows.length == i:
                continue
            indices.append([index, j, j + self.config.windows.length])
            index += 1
        for k in range(n - self.config.windows.length - 1, -1, -self.config.windows.step):
            indices.append([index, k, n])
            index += 1
        if k != 0:
            indices.append([index, 0, n])
        return indices

    async def draw_single_kline(self, indices: List[int]) -> Tuple[Line, Bar]:
        index_start = indices[1]
        index_end = indices[2]

        dates = self.df["date"].iloc[index_start:index_end].tolist()
        kline_data = self.df[["open", "close", "low", "high"]]
        volume_data = self.df[["index", "volume", "rise"]]

        bb_lower_data = self.df["Boll_Lower"]
        bb_upper_data = self.df["Boll_Upper"]
        bb_middle_data = self.df["Boll_Mid"]

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
                    min_=self.line_min,
                    max_=self.line_max,
                    splitarea_opts=opts.SplitAreaOpts(is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)),
                ),
                title_opts=opts.TitleOpts(
                    title=f"{self.stock_name} Boll & Kline",
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
                    split_number=self.volume_split_number,
                    min_=self.volume_min,
                    max_=self.volume_max,
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

        return overlap_kline_line, bar
