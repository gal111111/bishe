# -*- coding: utf-8 -*-
"""
创新可视化引擎页面模块：5大论文创新可视化组件
"""
import os
import streamlit as st

from src.visualization.novel_visualizations import (
    create_sentiment_flow_animation,
    create_geo_heatmap,
    create_sentiment_timeline,
    create_cross_platform_radar,
    create_data_cleaning_visualization,
)
from src.utils.error_handler import safe_execute
from src.utils.chart_config import apply_dark_theme


@safe_execute(default_return=None, user_message="创新可视化加载出错，请稍后重试")
def page_novel_viz(data_dir, load_analyzed_df, read_csv_cached):
    """创新可视化引擎页面

    Args:
        data_dir: 数据目录路径
        load_analyzed_df: 加载分析数据的函数
        read_csv_cached: 带缓存的CSV读取函数
    """
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
        <div style="font-size: 48px;">🎨</div>
        <div>
            <h1 style="margin: 0; font-size: 32px; font-weight: 800;">创新可视化引擎</h1>
            <p style="margin: 4px 0 0 0; color: #8B949E;">5大论文创新可视化 · 多维度舆情洞察</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df = None
    if 'df' in st.session_state and st.session_state.df is not None:
        df = st.session_state.df
    else:
        df = load_analyzed_df()

    if df is None:
        st.warning("⚠️ 请先在【数据中心】运行分析，生成数据后再查看可视化。")
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌊 舆情流动画", "🗺️ 地理热力图", "📈 情感时间线", "📊 跨平台雷达", "🧹 清洗可视化"
    ])

    with tab1:
        st.markdown("### 🌊 实时舆情流动画")
        st.caption("创新点：用动态气泡流展示舆情数据的实时流动，气泡大小=互动量，颜色=情感，位置=时间轴")
        fig_flow = create_sentiment_flow_animation(df)
        apply_dark_theme(fig_flow, height=400)
        st.plotly_chart(fig_flow, use_container_width=True)

    with tab2:
        st.markdown("### 🗺️ 上海迪士尼舆情地理热力图")
        st.caption("创新点：将舆情数据映射到地理空间，展示不同区域的情感强度分布")
        fig_geo = create_geo_heatmap(df)
        apply_dark_theme(fig_geo, height=400)
        st.plotly_chart(fig_geo, use_container_width=True)

    with tab3:
        st.markdown("### 📈 情感演化时间线")
        st.caption("创新点：用面积图+趋势线展示情感的时间演化，识别舆情爆发点与转折点")
        fig_timeline = create_sentiment_timeline(df)
        apply_dark_theme(fig_timeline, height=400)
        st.plotly_chart(fig_timeline, use_container_width=True)

    with tab4:
        st.markdown("### 📊 跨平台舆情对比雷达图")
        st.caption("创新点：将不同平台的舆情特征在多维度上对比，直观展示平台差异")
        if 'platform' in df.columns:
            fig_radar = create_cross_platform_radar(df)
            apply_dark_theme(fig_radar, height=400)
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("💡 需要包含 platform 列的数据才能展示跨平台对比。请合并多平台数据后重试。")

    with tab5:
        _render_cleaning_tab(df, data_dir, read_csv_cached)


def _render_cleaning_tab(df, data_dir, read_csv_cached):
    """数据清洗可视化标签页"""
    st.markdown("### 🧹 智能数据清洗可视化（5大创新点）")
    st.caption("创新点：将数据清洗过程可视化，直观展示SimHash去重、噪声检测、可信度评分、文本修复、事件聚合的效果")

    cleaned_path = os.path.join(data_dir, "cleaned_intelligent_上海迪士尼.csv")
    if os.path.exists(cleaned_path):
        df_cleaned = read_csv_cached(cleaned_path, os.path.getmtime(cleaned_path), encoding="utf-8-sig")
        fig_clean = create_data_cleaning_visualization(df, df_cleaned)
        apply_dark_theme(fig_clean, height=400)
        st.plotly_chart(fig_clean, use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("原始数据", f"{len(df)} 条")
        with col2:
            st.metric("清洗后", f"{len(df_cleaned)} 条")
        with col3:
            removed = len(df) - len(df_cleaned)
            st.metric("去除量", f"{removed} 条")
        with col4:
            retention = len(df_cleaned) / max(len(df), 1) * 100
            st.metric("保留率", f"{retention:.1f}%")
    else:
        st.info("💡 暂无智能清洗数据。请先运行智能数据清洗流程生成 `cleaned_intelligent_上海迪士尼.csv`。")
        if st.button("🚀 立即运行智能清洗", type="primary"):
            with st.spinner("正在运行5步智能清洗流程..."):
                try:
                    from src.preprocessing.intelligent_data_cleaner import IntelligentDataCleaner
                    cleaner = IntelligentDataCleaner()
                    df_cleaned = cleaner.clean_pipeline(df)
                    cleaner.save_results(df_cleaned, os.path.join(data_dir, "cleaned_intelligent_上海迪士尼.csv"))
                    st.success(f"✅ 清洗完成！{len(df)} → {len(df_cleaned)} 条（保留率 {len(df_cleaned)/max(len(df),1)*100:.1f}%）")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 清洗出错：{e}")
