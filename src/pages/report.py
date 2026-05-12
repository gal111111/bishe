# -*- coding: utf-8 -*-
"""
成果报告中心页面模块：学术报告生成与多格式导出
"""
import os
import glob
import time
import streamlit as st

from src.utils.error_handler import safe_execute


@safe_execute(default_return=None, user_message="报告中心加载出错，请稍后重试")
def page_report(data_dir, load_analyzed_df):
    """成果报告中心页面

    Args:
        data_dir: 数据目录路径
        load_analyzed_df: 加载分析数据的函数
    """
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
        <div style="font-size: 48px;">📑</div>
        <div>
            <h1 style="margin: 0; font-size: 32px; font-weight: 800;">成果报告中心</h1>
            <p style="margin: 4px 0 0 0; color: #8B949E;">一键导出完整分析报告，支持多种格式下载</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    md_files = glob.glob(os.path.join(data_dir, "academic_report_*.md"))

    if not md_files:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: #161B22; border-radius: 12px; border: 1px solid #30363D;">
            <div style="font-size: 64px; margin-bottom: 16px;">📭</div>
            <h3 style="color: #8B949E;">暂无生成的报告</h3>
            <p style="color: #6B7280;">请先在【数据中心】运行分析，系统将自动生成学术报告</p>
        </div>
        """, unsafe_allow_html=True)
        return

    md_files.sort(key=os.path.getmtime, reverse=True)
    latest_md = md_files[0]
    report_name = os.path.basename(latest_md)

    with open(latest_md, "r", encoding="utf-8") as f:
        content = f.read()

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 报告概览", "📖 在线预览", "📁 文件下载"])

    with tab1:
        _render_overview_tab(data_dir, report_name, latest_md, md_files, load_analyzed_df)

    with tab2:
        st.markdown("### 📖 报告在线预览")
        with st.container(height=700):
            st.markdown(content, unsafe_allow_html=True)

    with tab3:
        _render_download_tab(data_dir, content, md_files)


def _render_overview_tab(data_dir, report_name, latest_md, md_files, load_analyzed_df):
    """报告概览标签页"""
    col1, col2, col3, col4 = st.columns(4)

    df = load_analyzed_df()
    if df is not None:
        with col1:
            st.metric("📊 总评论数", f"{len(df):,}")
        with col2:
            if 'polarity_label' in df.columns:
                pos_rate = (df['polarity_label'] == '积极').mean() * 100
                st.metric("😊 积极评价", f"{pos_rate:.1f}%")
        with col3:
            if 'csi_score' in df.columns:
                avg_csi = df['csi_score'].mean()
                st.metric("📈 平均CSI", f"{avg_csi:.1f}")
        with col4:
            platforms = df['platform'].nunique() if 'platform' in df.columns else 1
            st.metric("🌐 数据源", f"{platforms}个平台")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #161B22 0%, #21262D 100%); border-radius: 12px; padding: 20px; border: 1px solid #30363D;">
            <h3 style="margin: 0 0 16px 0; color: #FFFFFF;">📋 报告信息</h3>
            <p style="color: #8B949E; margin: 8px 0;"><b>文件名:</b> """ + report_name + """</p>
            <p style="color: #8B949E; margin: 8px 0;"><b>生成时间:</b> """ + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(latest_md))) + """</p>
            <p style="color: #8B949E; margin: 8px 0;"><b>文件大小:</b> """ + f"{os.path.getsize(latest_md)/1024:.1f} KB" + """</p>
            <p style="color: #8B949E; margin: 8px 0;"><b>历史报告:</b> """ + f"{len(md_files)} 份" + """</p>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #161B22 0%, #21262D 100%); border-radius: 12px; padding: 20px; border: 1px solid #30363D;">
            <h3 style="margin: 0 0 16px 0; color: #FFFFFF;">📈 报告内容</h3>
            <p style="color: #3FB950; margin: 8px 0;">✅ 执行摘要</p>
            <p style="color: #3FB950; margin: 8px 0;">✅ 数据采集概况</p>
            <p style="color: #3FB950; margin: 8px 0;">✅ 情感分析深度解析</p>
            <p style="color: #3FB950; margin: 8px 0;">✅ 方面级满意度分析</p>
            <p style="color: #3FB950; margin: 8px 0;">✅ 改进建议与对策</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    viz_files = glob.glob(os.path.join(data_dir, "viz", "*"))
    if viz_files:
        st.markdown("### 🖼️ 可视化图表库")
        cols = st.columns(4)
        viz_list = [f for f in viz_files if f.endswith(('.png', '.html'))]
        for i, viz_file in enumerate(viz_list[:8]):
            with cols[i % 4]:
                viz_name = os.path.basename(viz_file)
                if viz_file.endswith('.png'):
                    st.image(viz_file, caption=viz_name, use_container_width=True)
                else:
                    st.markdown(f"📊 {viz_name}")


def _render_download_tab(data_dir, content, md_files):
    """文件下载标签页"""
    st.markdown("### 📁 文件下载中心")

    col_dl1, col_dl2, col_dl3 = st.columns(3)

    with col_dl1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2383E2 0%, #1E70C1 100%); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 16px;">
            <div style="font-size: 48px; margin-bottom: 8px;">📄</div>
            <h3 style="margin: 0; color: #FFFFFF;">Markdown 报告</h3>
            <p style="color: rgba(255,255,255,0.8); font-size: 13px;">学术研究报告</p>
        </div>
        """, unsafe_allow_html=True)
        st.download_button(
            label="⬇️ 下载 Markdown",
            data=content,
            file_name=f"舆情分析报告_{time.strftime('%Y%m%d')}.md",
            mime="text/markdown",
            type="primary",
            use_container_width=True
        )

    with col_dl2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #3FB950 0%, #2EA043 100%); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 16px;">
            <div style="font-size: 48px; margin-bottom: 8px;">📊</div>
            <h3 style="margin: 0; color: #FFFFFF;">CSV 数据</h3>
            <p style="color: rgba(255,255,255,0.8); font-size: 13px;">完整分析数据</p>
        </div>
        """, unsafe_allow_html=True)
        res_path = os.path.join(data_dir, "analyzed_comments.csv")
        if os.path.exists(res_path):
            with open(res_path, "rb") as f:
                csv_data = f.read()
            st.download_button(
                label="⬇️ 下载 CSV",
                data=csv_data,
                file_name=f"分析数据_{time.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )

    with col_dl3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 16px;">
            <div style="font-size: 48px; margin-bottom: 8px;">🖼️</div>
            <h3 style="margin: 0; color: #FFFFFF;">图表文件</h3>
            <p style="color: rgba(255,255,255,0.8); font-size: 13px;">可视化图表包</p>
        </div>
        """, unsafe_allow_html=True)
        viz_files = glob.glob(os.path.join(data_dir, "viz", "*"))
        st.info(f"共 {len(viz_files)} 个图表文件")
        st.caption("位于 data/viz/ 目录")

    st.markdown("---")

    if len(md_files) > 1:
        st.markdown("### 📚 历史报告")
        for i, md_file in enumerate(md_files[:5]):
            col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
            with col_h1:
                st.caption(f"📄 {os.path.basename(md_file)}")
            with col_h2:
                st.caption(f"📅 {time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(md_file)))}")
            with col_h3:
                with open(md_file, "r", encoding="utf-8") as f:
                    hist_content = f.read()
                st.download_button(
                    label="下载",
                    data=hist_content,
                    file_name=os.path.basename(md_file),
                    mime="text/markdown",
                    key=f"hist_{i}"
                )
