# -*- coding: utf-8 -*-
"""
Plotly暗色主题统一配置
消除各页面重复的图表样式代码，提供统一的暗色主题布局和更新方法
"""

PLOTLY_DARK_LAYOUT = {
    "template": "plotly_dark",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
}

DEFAULT_MARGIN = dict(t=50, b=20, l=20, r=20)

COLOR_MAP_SENTIMENT = {'积极': '#3FB950', '中性': '#F59E0B', '消极': '#F85149'}

COLOR_SEQUENCES = {
    "primary": ['#2383E2'],
    "danger": ['#F85149'],
    "qualitative": ['#2383E2', '#3FB950', '#F59E0B', '#F85149', '#A371F7', '#79C0FF'],
}


def dark_layout(height=350, margin=None, **extra):
    """生成统一的Plotly暗色主题布局配置

    Args:
        height: 图表高度，默认350
        margin: 边距配置，默认使用DEFAULT_MARGIN
        **extra: 额外的布局参数，如title、xaxis_title等

    Returns:
        dict: 可直接传给fig.update_layout()的配置字典
    """
    layout = {
        **PLOTLY_DARK_LAYOUT,
        "height": height,
        "margin": margin or DEFAULT_MARGIN,
    }
    layout.update(extra)
    return layout


def apply_dark_theme(fig, height=350, margin=None, **extra):
    """对Plotly图表应用暗色主题

    Args:
        fig: plotly.graph_objects.Figure 或 plotly.express图表对象
        height: 图表高度
        margin: 边距配置
        **extra: 额外的布局参数

    Returns:
        应用主题后的fig对象（支持链式调用）
    """
    fig.update_layout(**dark_layout(height=height, margin=margin, **extra))
    return fig
