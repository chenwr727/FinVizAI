from typing import List, Tuple

from pyecharts import options as opts
from pyecharts.charts import Bar, Kline, Line

from core.kline.base import KlineDrawer


class BgKlineDrawer(KlineDrawer):

    def get_indices_list(self, n: int) -> List[List[int]]:
        return [[0, 0, i] for i in range(0, n + 1)]

    async def draw_single_kline(self, indices: List[int]) -> Tuple[Line, Bar]:
        index = indices[-1]

        dates = self.df["date"].tolist()
        kline_data = self.df[["open", "close", "low", "high"]]
        volume_data = self.df[["index", "volume", "rise"]]

        bb_lower_data = self.df["Boll_Lower"]
        bb_upper_data = self.df["Boll_Upper"]
        bb_middle_data = self.df["Boll_Mid"]

        current_kline = kline_data.iloc[:index]
        current_volume = volume_data.iloc[:index]

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
                    title=f"{self.stock_name} Boll & Kline",
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

        return overlap_kline_line, bar
