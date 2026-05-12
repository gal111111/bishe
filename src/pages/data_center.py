# -*- coding: utf-8 -*-
"""
数据管理中心页面模块：数据采集与分析引擎
"""
import os
import glob
import time
import pandas as pd
import streamlit as st
from datetime import datetime

from src.analysis.sentiment_analysis import analyze_dataframe, generate_ai_report
from src.visualization.dashboard import generate_visualizations, plot_sankey_diagram
from src.analysis.academic_report import AcademicReportGenerator


def page_data_center(data_dir, raw_dir, read_csv_cached):
    """数据管理中心页面

    Args:
        data_dir: 数据目录路径
        raw_dir: 原始数据目录路径
        read_csv_cached: 带缓存的CSV读取函数
    """
    st.title("📁 数据管理中心")
    st.markdown("在这里管理原始数据，并启动核心分析引擎。")

    tab1, tab2 = st.tabs(["🔍 数据采集", "📊 分析与下载"])

    with tab1:
        _render_crawl_tab(raw_dir)

    with tab2:
        _render_analysis_tab(data_dir, raw_dir, read_csv_cached)


def _render_crawl_tab(raw_dir):
    """数据采集标签页"""
    st.markdown("### **第一步：获取数据**")

    crawler_mode = st.radio(
        "🕷️ 选择爬虫技术方案：",
        [
            "🔴 Selenium（原有方案）",
            "🔵 Playwright（现代方案，推荐）",
            "🤖 Browser Agent（AI驱动，论文创新点）"
        ],
        index=0,
        help="Selenium：原有稳定方案 | Playwright：更快速、自动等待 | Browser Agent：AI智能采集"
    )
    st.markdown("---")

    if crawler_mode.startswith("🔴"):
        st.info("💡 说明：由于知乎/微博的反爬策略，建议在【终端】中运行爬虫。")
        st.code("python test_auto_crawl.py", language="shell")
        st.markdown("""
        **操作流程:**
        1. 在终端运行上述命令，根据提示输入关键词。
        2. 完成数据爬取后，回到本页面，点击下方刷新按钮。
        """)
        if st.button("🔄 我已爬完，刷新数据列表", type="primary"):
            st.cache_data.clear()
            st.success("✅ 文件列表已刷新！请重新选择文件。")
            time.sleep(1)
            st.rerun()

    elif crawler_mode.startswith("🔵"):
        _render_playwright_crawler(raw_dir)

    elif crawler_mode.startswith("🤖"):
        _render_browser_agent_crawler()


def _render_playwright_crawler(raw_dir):
    """Playwright爬虫方案"""
    st.success("🎯 Playwright方案：更快速、自动等待、反检测能力更强、Cookie自动复用")

    col_kw, col_plat, col_num = st.columns([2, 1, 1])
    with col_kw:
        search_kw = st.text_input("🔍 搜索关键词", value="上海迪士尼", key="pw_kw")
    with col_plat:
        target_plat = st.selectbox("📌 平台", ["weibo", "zhihu", "tieba", "hupu"], key="pw_plat")
    with col_num:
        target_cnt = st.number_input("📊 数量", min_value=10, max_value=200, value=30, key="pw_cnt")

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        run_btn = st.button("🚀 启动爬虫", type="primary", key="pw_run")
    with col_btn2:
        st.caption("💡 首次运行会提示登录，完成后Cookie会自动保存，下次无需再登录")

    if run_btn:
        with st.spinner(f"正在采集 {target_plat} 数据..."):
            try:
                from src.modules.platform_crawler import PlaywrightPlatformCrawler
                crawler = PlaywrightPlatformCrawler(target_plat)
                data_list = crawler.crawl_keyword(search_kw, target_cnt)

                if data_list:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{target_plat}_playwright_{search_kw.replace(' ','_')}_{timestamp}.csv"
                    filepath = os.path.join(raw_dir, filename)
                    os.makedirs(raw_dir, exist_ok=True)

                    df = pd.DataFrame(data_list)
                    df.to_csv(filepath, index=False, encoding="utf-8-sig")
                    st.success(f"✅ 成功采集 {len(data_list)} 条数据！已保存")
                    with st.expander("📋 预览数据"):
                        st.dataframe(df.head(10))
                    st.cache_data.clear()
                else:
                    st.warning("⚠️ 未采集到数据，可能是Cookie失效，请重新登录")

            except Exception as e:
                st.error(f"❌ 爬虫出错：{str(e)}")
                with st.expander("🔍 查看详情"):
                    import traceback
                    st.code(traceback.format_exc())


def _render_browser_agent_crawler():
    """Browser Agent爬虫方案（论文创新亮点）"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1F2937, #21262D); border-radius: 12px; padding: 20px; border: 1px solid #30363D;">
        <h3 style="color: #58A6FF;">🤖 Browser Agent（论文创新亮点）</h3>
        <p style="color: #8B949E;">基于大模型的AI驱动浏览器，自动识别网页元素并采集数据</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**✨ 核心特性：**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - 🎯 **自动识别元素**：无需硬编码CSS选择器
        - 🧠 **AI智能决策**：模拟人类浏览行为
        - 🔄 **自适应改版**：自动适应网页结构变化
        """)
    with col2:
        st.markdown("""
        - 🛡️ **天然反爬**：行为与真实用户一致
        - 📊 **支持复杂场景**：探索式数据采集
        - ⚡ **技术栈**：Playwright + LLM + browser-use
        """)

    from src.crawlers.browser_agent.agent_crawler import BrowserAgentCrawler
    if st.button("🧪 演示Browser Agent工作流程", type="primary"):
        agent = BrowserAgentCrawler(use_llm=False)
        df_demo = agent.crawl("微博", "上海迪士尼", 20)
        st.success("✅ Browser Agent演示完成！")
        with st.expander("📋 演示数据"):
            st.dataframe(df_demo)


def _render_analysis_tab(data_dir, raw_dir, read_csv_cached):
    """分析与下载标签页"""
    st.markdown("### **第二步：选择数据并分析**")

    raw_files = glob.glob(os.path.join(raw_dir, "*_raw_*.csv"))

    if not raw_files:
        st.warning("⚠️ 暂无原始数据，请先在【数据采集】Tab指引下完成爬取。")
        return

    raw_files.sort(key=os.path.getmtime, reverse=True)

    file_options = [os.path.basename(f) for f in raw_files]
    selected_filename = st.selectbox("选择要分析的原始数据文件：", file_options)

    if selected_filename:
        selected_filepath = os.path.join(raw_dir, selected_filename)

        try:
            df_raw = read_csv_cached(
                selected_filepath,
                os.path.getmtime(selected_filepath),
                encoding="utf-8-sig",
                on_bad_lines="skip"
            )

            with st.container():
                st.markdown("### 📋 数据预览")
                st.dataframe(df_raw.head(20), height=300)
                st.caption(f"文件预览：{selected_filename} | 共 {len(df_raw)} 条")

            col_setting1, col_setting2 = st.columns([1, 1])
            with col_setting1:
                analysis_method = st.selectbox(
                    "选择情感分析方式：",
                    [
                        "SnowNLP 快速分析（推荐，本地执行）",
                        "🤖 混合模式（SnowNLP + DeepSeek 智能结合）",
                        "DeepSeek AI 深度分析（API调用，更精确）"
                    ],
                    index=1,
                    help="混合模式：优先用SnowNLP快速分析，对长文本用DeepSeek深度分析，兼顾速度与精度"
                )
                if "SnowNLP" in analysis_method:
                    preferred_method = "snownlp"
                elif "混合模式" in analysis_method:
                    preferred_method = "hybrid"
                else:
                    preferred_method = "deepseek"

            with col_setting2:
                st.markdown("**分析说明：**")
                if preferred_method == "snownlp":
                    st.info("✅ 使用SnowNLP本地模型，快速处理，适合大规模数据")
                elif preferred_method == "hybrid":
                    st.success("🎯 混合模式：SnowNLP快速分析 + DeepSeek深度分析（约10%长文本）")
                else:
                    st.warning("⚠️ 使用DeepSeek API，分析更精确但需要网络连接")

            if preferred_method == "hybrid":
                deepseek_ratio = st.slider(
                    "DeepSeek 分析比例：",
                    min_value=0.05, max_value=0.3, value=0.1, step=0.05,
                    help="设置使用DeepSeek分析的评论比例，越高越精确但越慢"
                )
            else:
                deepseek_ratio = 0.1

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🤖 对该文件执行智能分析", type="primary"):
                    _execute_analysis(df_raw, preferred_method, deepseek_ratio, data_dir)

            with col2:
                with open(selected_filepath, "rb") as f:
                    st.download_button("💾 下载此原始数据", f, selected_filename, type="secondary")

        except Exception as e:
            st.error(f"处理文件时出错: {e}")
            import traceback
            st.error(traceback.format_exc())


def _execute_analysis(df_raw, preferred_method, deepseek_ratio, data_dir):
    """执行智能分析流程"""
    progress_bar = st.progress(0)
    status = st.empty()

    try:
        from src.analysis.sentiment_analysis import preprocess_data
        status.text("🔧 正在预处理数据...")
        df_clean = preprocess_data(df_raw)
        st.info(f"📊 数据预处理完成：原始 {len(df_raw)} 条 → 有效 {len(df_clean)} 条")
    except Exception as e:
        df_clean = df_raw
        st.warning(f"⚠️ 预处理跳过：{e}")

    def update_p(p):
        progress_bar.progress(p)
        if preferred_method == "hybrid":
            method_name = "混合模式 (SnowNLP+DeepSeek)"
        else:
            method_name = "SnowNLP" if preferred_method == "snownlp" else "DeepSeek"
        status.text(f"🤖 {method_name} 正在分析... {int(p*100)}%")

    df_res = analyze_dataframe(df_clean, preferred=preferred_method, progress_callback=update_p, deepseek_ratio=deepseek_ratio)

    df_res.to_csv(os.path.join(data_dir, "analyzed_comments.csv"), index=False, encoding="utf-8-sig")

    status.text("📊 正在生成可视化图表...")
    rep, asp, absa, detailed_absa = generate_ai_report(df_res)
    generate_visualizations(df_res, rep, asp, os.path.join(data_dir, "viz"))
    plot_sankey_diagram(df_res, os.path.join(data_dir, "viz"))

    status.text("📝 正在生成学术报告...")
    AcademicReportGenerator(df_res, data_dir).generate_full_report()

    st.session_state.df = df_res

    st.markdown("---")
    st.markdown("### 📈 分析结果统计")

    if preferred_method == "hybrid" and 'analysis_method' in df_res.columns:
        method_counts = df_res['analysis_method'].value_counts()
        col_method1, col_method2, col_method3 = st.columns(3)
        with col_method1:
            st.metric("SnowNLP分析", method_counts.get('snownlp', 0))
        with col_method2:
            st.metric("DeepSeek分析", method_counts.get('deepseek', 0))
        with col_method3:
            deepseek_pct = method_counts.get('deepseek', 0) / len(df_res) * 100
            st.metric("DeepSeek占比", f"{deepseek_pct:.1f}%")
        st.markdown("---")

    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("总评论数", len(df_res))
    with col_stat2:
        pos_count = len(df_res[df_res['polarity_label'] == '积极'])
        st.metric("积极评论", pos_count, f"{pos_count/len(df_res)*100:.1f}%")
    with col_stat3:
        neu_count = len(df_res[df_res['polarity_label'] == '中性'])
        st.metric("中性评论", neu_count, f"{neu_count/len(df_res)*100:.1f}%")
    with col_stat4:
        neg_count = len(df_res[df_res['polarity_label'] == '消极'])
        st.metric("消极评论", neg_count, f"{neg_count/len(df_res)*100:.1f}%")

    status.success("✅ 分析完成！请前往【驾驶舱】查看结果。")
    st.balloons()
