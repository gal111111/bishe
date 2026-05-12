# -*- coding: utf-8 -*-
"""
城市慧眼 4.0 - 城市公共设施舆情分析系统
==========================================
基于 Streamlit 构建的多页面 Web 应用，实现城市公共设施舆情数据的
采集、情感分析、可视化展示与智能决策支持。

主要功能模块：
    - 驾驶舱（Dashboard）：核心指标展示与整改推演
    - 数据管理中心：数据采集（Selenium/Playwright/Browser Agent）与分析
    - 创新可视化引擎：5大论文创新可视化组件
    - 智能决策助手（RAG）：基于检索增强生成的智能问答
    - 成果报告中心：学术报告生成与多格式导出

技术栈：Streamlit + Plotly + Pandas + DeepSeek API
"""
import os
import sys
import time
import functools
import logging
import pandas as pd
import streamlit as st

st.set_page_config(page_title="城市慧眼 4.0", layout="wide", page_icon="🏙️")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")


def load_custom_css():
    css_path = os.path.join(PROJECT_ROOT, "src", "static", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_custom_css()


def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.time() - start_time
            logging.getLogger(__name__).info(f"[Perf] {func.__name__} took {elapsed:.3f}s")
    return wrapper


def safe_page(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"页面加载出错: {e}")
            with st.expander("🔍 查看错误详情"):
                import traceback
                st.code(traceback.format_exc())
    return wrapper


from src.analysis.sentiment_analysis import analyze_dataframe, generate_ai_report, call_deepseek_api
from src.visualization.dashboard import generate_visualizations, plot_sankey_diagram
from src.analysis.academic_report import AcademicReportGenerator
from src.analysis.advanced_analysis import analyze_sentiment_trends
from src.visualization.advanced_viz_fixed import create_advanced_tech_page
from src.utils.data_exporter import DataExporter, AlertManager
from src.visualization.advanced_analysis_page import create_advanced_analysis_page
from src.visualization.novel_visualizations import (
    create_sentiment_flow_animation,
    create_geo_heatmap,
    create_sentiment_timeline,
    create_cross_platform_radar,
    create_data_cleaning_visualization,
)

from src.pages import show_dashboard, page_data_center, page_chatbot, page_novel_viz, page_report


@st.cache_data(show_spinner=False)
def read_csv_cached(file_path: str, mtime: float, encoding: str = "utf-8-sig", on_bad_lines: str = None):
    """带缓存的CSV读取，mtime用于自动失效"""
    read_kwargs = {"encoding": encoding}
    if on_bad_lines:
        read_kwargs["on_bad_lines"] = on_bad_lines
    return pd.read_csv(file_path, **read_kwargs)


def load_analyzed_df():
    """加载分析结果数据（不存在时返回None）"""
    analyzed_path = os.path.join(DATA_DIR, "analyzed_comments.csv")
    if not os.path.exists(analyzed_path):
        return None
    try:
        return read_csv_cached(analyzed_path, os.path.getmtime(analyzed_path), encoding="utf-8-sig")
    except Exception:
        return None


def _get_df():
    """获取当前数据：优先session_state，否则从文件加载"""
    if 'df' in st.session_state and st.session_state.df is not None:
        return st.session_state.df
    return load_analyzed_df()


def main():
    """应用主入口函数：初始化会话状态与侧边栏导航"""
    if 'simulated' not in st.session_state:
        st.session_state.simulated = False

    with st.sidebar:
        st.markdown("""
            <div style="font-size: 64px; margin-bottom: 10px;">🏙️</div>
            <h2 style="margin: 0; font-size: 24px; font-weight: 800;">城市慧眼 4.0</h2>
            <p style="margin: 5px 0 0 0; color: #8B949E; font-size: 13px;">城市公共设施舆情分析系统</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        nav = st.radio(
            "功能导航",
            ["驾驶舱", "数据中心", "创新可视化", "前沿技术", "前沿算法", "智能问答", "报告下载"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        st.caption("💡 提示")
        st.info("先在【数据中心】上传或爬取数据，然后运行分析，最后在【驾驶舱】查看可视化结果。")

    if nav == "驾驶舱":
        df = _get_df()
        if df is not None:
            show_dashboard(df, DATA_DIR)
        else:
            st.warning("请先去数据中心分析数据")
    elif nav == "数据中心":
        page_data_center(DATA_DIR, RAW_DIR, read_csv_cached)
    elif nav == "创新可视化":
        page_novel_viz(DATA_DIR, load_analyzed_df, read_csv_cached)
    elif nav == "前沿技术":
        df = _get_df()
        if df is not None:
            create_advanced_tech_page(df)
        else:
            st.warning("请先去数据中心分析数据")
    elif nav == "前沿算法":
        df = _get_df()
        if df is not None:
            create_advanced_analysis_page(df)
        else:
            st.warning("请先去数据中心分析数据")
    elif nav == "智能问答":
        page_chatbot(load_analyzed_df)
    elif nav == "报告下载":
        page_report(DATA_DIR, load_analyzed_df)


if __name__ == "__main__":
    main()
