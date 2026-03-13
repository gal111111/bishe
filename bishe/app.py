# -*- coding: utf-8 -*-
import os
import sys
import glob
import time
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

try:
    from streamlit import components
except ImportError:
    components = None

st.set_page_config(page_title="城市慧眼 3.0", layout="wide", page_icon="🏙️")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")

from src.analysis.sentiment_analysis import analyze_dataframe, generate_ai_report, call_deepseek_api
from src.visualization.dashboard import generate_visualizations, plot_sankey_diagram
from src.analysis.academic_report import AcademicReportGenerator
from src.analysis.advanced_analysis import analyze_sentiment_trends
from src.visualization.advanced_viz_fixed import create_advanced_tech_page
from src.utils.data_exporter import DataExporter, AlertManager
from src.visualization.advanced_analysis_page import create_advanced_analysis_page

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0E1117 0%, #161B22 100%);
    color: #FFFFFF;
}
.stSidebar {
    background: linear-gradient(180deg, #161B22 0%, #0D1117 100%);
    border-right: 1px solid #30363D;
}
.stButton > button {
    background: linear-gradient(135deg, #2383E2 0%, #1E70C1 100%);
    color: white;
    border-radius: 8px;
    border: none;
    box-shadow: 0 4px 12px rgba(35, 131, 226, 0.3);
    transition: all 0.3s ease;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1E70C1 0%, #195E9E 100%);
    box-shadow: 0 6px 16px rgba(35, 131, 226, 0.4);
    transform: translateY(-2px);
}
.stMetric {
    background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #30363D;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
.stMetric label {
    color: #8B949E;
    font-size: 14px;
    font-weight: 500;
}
.stMetric [data-testid="stMetricValue"] {
    color: #FFFFFF;
    font-size: 28px;
    font-weight: 700;
}
.stMetric [data-testid="stMetricDelta"] {
    font-size: 14px;
    font-weight: 600;
}
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
}
div[data-testid="stExpander"] {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
}
div[data-testid="stTab"] {
    background: #161B22;
}
div[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px;
}
div[data-testid="stTabs"] [aria-selected="true"] {
    background: linear-gradient(135deg, #2383E2 0%, #1E70C1 100%) !important;
    border-radius: 8px !important;
}
.stProgress > div > div {
    background: linear-gradient(90deg, #2383E2 0%, #3FB950 100%);
    border-radius: 4px;
}
.card {
    background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}
.stat-card {
    background: linear-gradient(135deg, #1F2937 0%, #111827 100%);
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    border: 1px solid #374151;
}
.stat-card h3 {
    color: #9CA3AF;
    font-size: 14px;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.stat-card .value {
    color: #FFFFFF;
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 4px;
}
.stat-card .sub {
    color: #6B7280;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

def show_dashboard(df):
    """驾驶舱：核心数据展示 + 整改推演"""
    col_title, col_time = st.columns([3, 1])
    with col_title:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 16px;">
            <div style="font-size: 48px;">🏙️</div>
            <div>
                <h1 style="margin: 0; font-size: 32px; font-weight: 800;">城市舆情态势感知中心</h1>
                <p style="margin: 4px 0 0 0; color: #8B949E;">实时监控城市公共设施服务质量与市民满意度</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_time:
        st.caption(f"最后更新: {pd.to_datetime('today').strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(f"数据来源: {df['platform'].unique()[0] if 'platform' in df.columns else '多平台'}")
    
    st.markdown("---")
    
    if 'csi_score' not in df.columns:
        st.warning("数据缺少 CSI 指标，请重新分析")
        return
    
    avg_csi = df['csi_score'].mean()
    total = len(df)
    urgent = len(df[df.get('urgency_score', 0) >= 7])
    neg_rate = (df['polarity_label'] == '消极').mean() * 100
    pos_rate = (df['polarity_label'] == '积极').mean() * 100
    neu_rate = (df['polarity_label'] == '中性').mean() * 100
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <h3>CSI 满意度指数</h3>
            <div class="value">{avg_csi:.1f}</div>
            <div class="sub">综合评价</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <h3>全网舆情样本</h3>
            <div class="value">{total:,}</div>
            <div class="sub">有效评论</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <h3>高危预警事件</h3>
            <div class="value">{urgent}</div>
            <div class="sub">需紧急关注</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="stat-card">
            <h3>正面评价</h3>
            <div class="value" style="color: #3FB950;">{pos_rate:.1f}%</div>
            <div class="sub">积极情绪</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="stat-card">
            <h3>中性评价</h3>
            <div class="value" style="color: #F59E0B;">{neu_rate:.1f}%</div>
            <div class="sub">中立态度</div>
        </div>
        """, unsafe_allow_html=True)
    with c6:
        st.markdown(f"""
        <div class="stat-card">
            <h3>负面评价</h3>
            <div class="value" style="color: #F85149;">{neg_rate:.1f}%</div>
            <div class="sub">需要改进</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.container():
        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ 模拟整改生效", type="primary"):
                    st.session_state.simulated = True
                    st.rerun()
            with col_btn2:
                if st.button("🔄 重置为现状"):
                    st.session_state.simulated = False
                    st.rerun()
        with col_info:
            if st.session_state.simulated:
                st.success("📊 推演结果：预期满意度将提升 15%，高危投诉将显著减少。")
            else:
                st.info("💡 点击'模拟整改生效'按钮查看政策实施后的预期效果。")
    
    st.markdown("---")
    
    tab_overview, tab_facility, tab_aspect, tab_advanced, tab_detail = st.tabs([
        "📊 概览分析", "🏢 设施类型分析", "📋 方面维度分析", "🔬 深度分析", "📝 详细数据"
    ])
    
    with tab_overview:
        col1, col2 = st.columns([1, 1])
        with col1:
            with st.container():
                st.markdown("### 😊 情感分布")
                if 'polarity_label' in df.columns:
                    sentiment_counts = df['polarity_label'].value_counts()
                    fig = px.pie(
                        values=sentiment_counts.values,
                        names=sentiment_counts.index,
                        hole=0.4,
                        color_discrete_map={'积极': '#3FB950', '中性': '#F59E0B', '消极': '#F85149'},
                        title='情感倾向占比'
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=350,
                        margin=dict(t=50, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("等待数据...")
        with col2:
            with st.container():
                st.markdown("### 📈 满意度分布")
                if 'csi_score' in df.columns:
                    fig = px.histogram(
                        df,
                        x='csi_score',
                        nbins=20,
                        title='CSI满意度指数分布',
                        color_discrete_sequence=['#2383E2'],
                        marginal='box'
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=350,
                        margin=dict(t=50, b=20, l=20, r=20)
                    )
                    fig.update_xaxes(range=[0, 100])
                    st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        col3, col4 = st.columns([1, 1])
        with col3:
            with st.container():
                st.markdown("### ⚡ 紧急度分布")
                if 'urgency_score' in df.columns:
                    urgency_counts = df['urgency_score'].value_counts().sort_index()
                    fig = px.bar(
                        x=urgency_counts.index,
                        y=urgency_counts.values,
                        title='问题紧急度分布',
                        color_discrete_sequence=['#F85149']
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=300,
                        margin=dict(t=50, b=20, l=20, r=20),
                        xaxis_title='紧急度',
                        yaxis_title='数量'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        with col4:
            with st.container():
                st.markdown("### 📊 满意度 vs 紧急度")
                if 'csi_score' in df.columns and 'urgency_score' in df.columns:
                    fig = px.scatter(
                        df,
                        x='csi_score',
                        y='urgency_score',
                        color='polarity_label',
                        size='urgency_score',
                        hover_data=['content'],
                        title='满意度与紧急度关系',
                        color_discrete_map={'积极': '#3FB950', '中性': '#F59E0B', '消极': '#F85149'}
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=300,
                        margin=dict(t=50, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab_facility:
        col1, col2 = st.columns([1, 1])
        with col1:
            with st.container():
                st.markdown("### 🏢 各设施类型满意度")
                if 'facility_type' in df.columns and 'csi_score' in df.columns:
                    facility_avg = df.groupby('facility_type')['csi_score'].mean().sort_values(ascending=False)
                    fig = px.bar(
                        x=facility_avg.values,
                        y=facility_avg.index,
                        orientation='h',
                        title='各设施类型平均CSI指数',
                        color=facility_avg.values,
                        color_continuous_scale='RdYlGn',
                        range_color=[50, 100]
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=400,
                        margin=dict(t=50, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
        with col2:
            with st.container():
                st.markdown("### 📊 设施类型情感构成")
                if 'facility_type' in df.columns and 'polarity_label' in df.columns:
                    crosstab = pd.crosstab(df['facility_type'], df['polarity_label'])
                    crosstab_pct = crosstab.div(crosstab.sum(axis=1), axis=0) * 100
                    fig = px.bar(
                        crosstab_pct,
                        orientation='h',
                        title='各设施类型情感占比',
                        color_discrete_map={'积极': '#3FB950', '中性': '#F59E0B', '消极': '#F85149'}
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=400,
                        margin=dict(t=50, b=20, l=20, r=20),
                        barmode='stack'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        with st.container():
            st.markdown("### 🎻 各设施类型满意度分布（小提琴图）")
            if 'facility_type' in df.columns and 'csi_score' in df.columns:
                fig = px.violin(
                    df,
                    x='facility_type',
                    y='csi_score',
                    color='facility_type',
                    box=True,
                    title='各设施类型满意度分布',
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=450,
                    margin=dict(t=50, b=20, l=20, r=20)
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab_aspect:
        col1, col2 = st.columns([1, 1])
        with col1:
            with st.container():
                st.markdown("### 📋 各方面满意度对比")
                if 'aspect' in df.columns and 'csi_score' in df.columns:
                    aspect_avg = df.groupby('aspect')['csi_score'].mean().sort_values(ascending=False)
                    fig = px.bar(
                        x=aspect_avg.index,
                        y=aspect_avg.values,
                        title='各方面平均CSI指数',
                        color=aspect_avg.values,
                        color_continuous_scale='RdYlGn',
                        range_color=[50, 100]
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=350,
                        margin=dict(t=50, b=50, l=20, r=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
        with col2:
            with st.container():
                st.markdown("### 🎯 方面综合表现雷达图")
                if 'aspect' in df.columns and 'csi_score' in df.columns:
                    aspect_avg = df.groupby('aspect')['csi_score'].mean()
                    if len(aspect_avg) >= 3:
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(
                            r=aspect_avg.values,
                            theta=aspect_avg.index,
                            fill='toself',
                            name='各方面满意度',
                            line=dict(color='#2383E2'),
                            fillcolor='rgba(35, 131, 226, 0.3)'
                        ))
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(visible=True, range=[0, 100]),
                                angularaxis=dict(showticklabels=True)
                            ),
                            showlegend=False,
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            height=350,
                            margin=dict(t=50, b=20, l=20, r=20),
                            title='各方面满意度综合表现'
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        with st.container():
            st.markdown("### 🔥 设施类型-方面热力图")
            if 'facility_type' in df.columns and 'aspect' in df.columns and 'csi_score' in df.columns:
                heatmap_data = df.groupby(['facility_type', 'aspect'])['csi_score'].mean().unstack()
                fig = px.imshow(
                    heatmap_data,
                    title='设施类型-方面满意度热力图',
                    color_continuous_scale='RdYlGn',
                    range_color=[50, 100],
                    text_auto='.1f'
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=500,
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab_advanced:
        col1, col2 = st.columns([1, 1])
        with col1:
            with st.container():
                st.markdown("### 🔄 归因流向桑基图")
                viz_dir = os.path.join(DATA_DIR, "viz")
                sankey_path = os.path.join(viz_dir, "sankey_flow.html")
                if os.path.exists(sankey_path) and components:
                    with open(sankey_path, 'r', encoding='utf-8') as f:
                        st.components.v1.html(f.read(), height=400)
                else:
                    st.info("请先运行分析以生成桑基图")
        with col2:
            with st.container():
                st.markdown("### 🔻 情感漏斗图")
                viz_dir = os.path.join(DATA_DIR, "viz")
                funnel_path = os.path.join(viz_dir, "funnel_chart.png")
                if os.path.exists(funnel_path):
                    st.image(funnel_path, use_container_width=True)
                else:
                    st.info("请先运行分析以生成漏斗图")
        
        st.markdown("---")
        
        col3, col4 = st.columns([1, 1])
        with col3:
            with st.container():
                st.markdown("### ☁️ 评论关键词词云")
                viz_dir = os.path.join(DATA_DIR, "viz")
                wordcloud_path = os.path.join(viz_dir, "wordcloud.png")
                if os.path.exists(wordcloud_path):
                    st.image(wordcloud_path, use_container_width=True)
                else:
                    st.info("请先运行分析以生成词云图")
        with col4:
            with st.container():
                st.markdown("### 📐 极坐标分布图")
                viz_dir = os.path.join(DATA_DIR, "viz")
                polar_path = os.path.join(viz_dir, "polar_chart.png")
                if os.path.exists(polar_path):
                    st.image(polar_path, use_container_width=True)
                else:
                    st.info("请先运行分析以生成极坐标图")
        
        st.markdown("---")
        
        col5, col6 = st.columns([1, 1])
        with col5:
            with st.container():
                st.markdown("### 📈 面积趋势图")
                viz_dir = os.path.join(DATA_DIR, "viz")
                area_path = os.path.join(viz_dir, "area_chart.png")
                if os.path.exists(area_path):
                    st.image(area_path, use_container_width=True)
                else:
                    st.info("请先运行分析以生成面积图")
        with col6:
            with st.container():
                st.markdown("### 🎻 更多图表")
                chart_files = glob.glob(os.path.join(DATA_DIR, "viz", "*.png"))
                if chart_files:
                    st.markdown("**可用图表列表:**")
                    for chart in sorted(chart_files):
                        st.caption(f"📊 {os.path.basename(chart)}")
                else:
                    st.info("暂无图表文件")
    
    with tab_detail:
        st.markdown("### 📝 详细数据列表")
        
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        with col_filter1:
            if 'facility_type' in df.columns:
                facilities = ['全部'] + sorted(df['facility_type'].unique().tolist())
                selected_facility = st.selectbox('筛选设施类型', facilities)
            else:
                selected_facility = '全部'
        with col_filter2:
            if 'polarity_label' in df.columns:
                sentiments = ['全部'] + sorted(df['polarity_label'].unique().tolist())
                selected_sentiment = st.selectbox('筛选情感倾向', sentiments)
            else:
                selected_sentiment = '全部'
        with col_filter3:
            if 'aspect' in df.columns:
                aspects = ['全部'] + sorted(df['aspect'].unique().tolist())
                selected_aspect = st.selectbox('筛选评论方面', aspects)
            else:
                selected_aspect = '全部'
        
        filtered_df = df.copy()
        if selected_facility != '全部' and 'facility_type' in df.columns:
            filtered_df = filtered_df[filtered_df['facility_type'] == selected_facility]
        if selected_sentiment != '全部' and 'polarity_label' in df.columns:
            filtered_df = filtered_df[filtered_df['polarity_label'] == selected_sentiment]
        if selected_aspect != '全部' and 'aspect' in df.columns:
            filtered_df = filtered_df[filtered_df['aspect'] == selected_aspect]
        
        display_cols = ['content']
        if 'polarity_label' in df.columns:
            display_cols.append('polarity_label')
        if 'csi_score' in df.columns:
            display_cols.append('csi_score')
        if 'facility_type' in df.columns:
            display_cols.append('facility_type')
        if 'aspect' in df.columns:
            display_cols.append('aspect')
        if 'urgency_score' in df.columns:
            display_cols.append('urgency_score')
        if 'specific_emotion' in df.columns:
            display_cols.append('specific_emotion')
        
        st.dataframe(
            filtered_df[display_cols],
            use_container_width=True,
            height=500
        )
        
        st.caption(f"共显示 {len(filtered_df)} 条评论（总计 {len(df)} 条）")
        
        st.markdown("---")
        
        with st.container():
            st.markdown("### 🚨 高危预警评论")
            urgent_df = df[df.get('urgency_score', 0) >= 7].sort_values('urgency_score', ascending=False)
            if not urgent_df.empty:
                for idx, row in urgent_df.head(10).iterrows():
                    with st.expander(f"🚨 紧急度 {row.get('urgency_score', 0)} - {row.get('facility_type', '未分类')}"):
                        st.markdown(f"**评论内容:** {row['content']}")
                        if 'polarity_label' in row:
                            st.markdown(f"**情感倾向:** {row['polarity_label']}")
                        if 'csi_score' in row:
                            st.markdown(f"**CSI指数:** {row['csi_score']:.1f}")
                        if 'aspect' in row:
                            st.markdown(f"**评论方面:** {row['aspect']}")
            else:
                st.success("✅ 当前无高危预警评论")

def page_data_center():
    st.title("📁 数据管理中心")
    st.markdown("在这里管理原始数据，并启动核心分析引擎。")

    tab1, tab2 = st.tabs(["🔍 数据采集", "📊 分析与下载"])

    with tab1:
        st.markdown("### **第一步：获取数据**")
        with st.container():
            st.info("💡 说明：由于知乎/微博的反爬策略，建议在【终端】中运行爬虫。")
            st.code("python test_auto_crawl.py", language="shell")
            st.markdown("""
            **操作流程:**
            1.  在终端运行上述命令，根据提示输入关键词。
            2.  完成数据爬取后，回到本页面，点击下方刷新按钮。
            """)
            if st.button("🔄 我已爬完，刷新数据列表", type="primary"):
                st.cache_data.clear()
                st.success("✅ 文件列表已刷新！请重新选择文件。")
                time.sleep(1)
                st.rerun()

    with tab2:
        st.markdown("### **第二步：选择数据并分析**")
        
        raw_files = glob.glob(os.path.join(RAW_DIR, "*_raw_*.csv"))

        if not raw_files:
            st.warning("⚠️ 暂无原始数据，请先在【数据采集】Tab指引下完成爬取。")
            return

        raw_files.sort(key=os.path.getmtime, reverse=True)
        
        file_options = [os.path.basename(f) for f in raw_files]
        selected_filename = st.selectbox("选择要分析的原始数据文件：", file_options)

        if selected_filename:
            selected_filepath = os.path.join(RAW_DIR, selected_filename)
            
            try:
                df_raw = pd.read_csv(selected_filepath, encoding="utf-8-sig", on_bad_lines='skip')
                
                with st.container():
                    st.markdown("### 📋 数据预览")
                    st.dataframe(df_raw.head(20), height=300)
                    st.caption(f"文件预览：{selected_filename} | 共 {len(df_raw)} 条")

                st.markdown("---")
                st.markdown("### ⚙️ 分析设置")
                
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
                
                # 混合模式设置
                if preferred_method == "hybrid":
                    deepseek_ratio = st.slider(
                        "DeepSeek 分析比例：",
                        min_value=0.05,
                        max_value=0.3,
                        value=0.1,
                        step=0.05,
                        help="设置使用DeepSeek分析的评论比例，越高越精确但越慢"
                    )
                else:
                    deepseek_ratio = 0.1

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🤖 对该文件执行智能分析", type="primary"):
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
                        
                        df_res.to_csv(os.path.join(DATA_DIR, "analyzed_comments.csv"), index=False, encoding="utf-8-sig")
                        
                        status.text("📊 正在生成可视化图表...")
                        rep, asp, absa = generate_ai_report(df_res)
                        generate_visualizations(df_res, rep, asp, os.path.join(DATA_DIR, "viz"))
                        plot_sankey_diagram(df_res, os.path.join(DATA_DIR, "viz"))
                        
                        status.text("📝 正在生成学术报告...")
                        AcademicReportGenerator(df_res, DATA_DIR).generate_full_report()
                        
                        st.session_state.df = df_res
                        
                        # 显示分析结果统计
                        st.markdown("---")
                        st.markdown("### 📈 分析结果统计")
                        
                        # 如果是混合模式，显示分析方式统计
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
                with col2:
                    with open(selected_filepath, "rb") as f:
                        st.download_button("💾 下载此原始数据", f, selected_filename, type="secondary")
            
            except Exception as e:
                st.error(f"处理文件时出错: {e}")
                import traceback
                st.error(traceback.format_exc())

def page_chatbot():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🤖 智能决策助手 (RAG)")
    with col2:
        if st.button("🔄 清除聊天记录"):
            if "messages" in st.session_state:
                del st.session_state.messages
            st.rerun()

    res_path = os.path.join(DATA_DIR, "analyzed_comments.csv")
    if not os.path.exists(res_path):
        st.error("⚠️ 请先在【数据管理中心】运行分析！")
        return
    df = pd.read_csv(res_path)

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "我是基于当前数据的 AI 顾问，请问有什么可以帮您？"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("例如：哪些设施的卫生问题最严重？"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🔍 检索分析中..."):
                try:
                    search_content = df['content'].astype(str)
                    if len(prompt) < 2:
                        ctx = df.head(10)
                    else:
                        key = prompt[:2]
                        ctx = df[search_content.str.contains(key, na=False, case=False)].head(10)
                        if ctx.empty:
                            ctx = df.head(10)

                    txt_context = "\n".join([f"- {t}" for t in ctx['content'].astype(str).tolist()])

                    sys_msg = "你是城市数据分析师。根据给定的【评论数据】回答用户问题。如果数据中没有答案，请根据常识推断并说明。"
                    user_msg = f"【评论数据片段】:\n{txt_context}\n\n【用户问题】: {prompt}"

                    res = call_deepseek_api([
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": user_msg}
                    ])

                    ans = res.get("content", "抱歉，AI 服务连接超时，请重试。")
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    
                    with st.expander("📊 查看 AI 参考的数据源"):
                        display_cols = ['content']
                        if 'sentiment_label' in df.columns:
                            display_cols.append('sentiment_label')
                        if 'facility_type' in df.columns:
                            display_cols.append('facility_type')
                        if 'csi_score' in df.columns:
                            display_cols.append('csi_score')
                        st.dataframe(ctx[display_cols])

                except Exception as e:
                    err_msg = f"系统处理出错: {e}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})

def page_report():
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
        <div style="font-size: 48px;">📑</div>
        <div>
            <h1 style="margin: 0; font-size: 32px; font-weight: 800;">成果报告中心</h1>
            <p style="margin: 4px 0 0 0; color: #8B949E;">一键导出完整分析报告，支持多种格式下载</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    md_files = glob.glob(os.path.join(DATA_DIR, "academic_report_*.md"))
    
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
        col1, col2, col3, col4 = st.columns(4)
        
        res_path = os.path.join(DATA_DIR, "analyzed_comments.csv")
        if os.path.exists(res_path):
            df = pd.read_csv(res_path)
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
        
        viz_files = glob.glob(os.path.join(DATA_DIR, "viz", "*"))
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
    
    with tab2:
        st.markdown("### 📖 报告在线预览")
        with st.container(height=700):
            st.markdown(content, unsafe_allow_html=True)
    
    with tab3:
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

def main():
    if 'simulated' not in st.session_state:
        st.session_state.simulated = False
    
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-size: 64px; margin-bottom: 10px;">🏙️</div>
            <h2 style="margin: 0; font-size: 24px; font-weight: 800;">城市慧眼 3.0</h2>
            <p style="margin: 5px 0 0 0; color: #8B949E; font-size: 13px;">城市公共设施舆情分析系统</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        nav = st.radio(
            "功能导航",
            ["驾驶舱", "数据中心", "前沿技术", "前沿算法", "智能问答", "报告下载"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        st.caption("💡 提示")
        st.info("先在【数据中心】上传或爬取数据，然后运行分析，最后在【驾驶舱】查看可视化结果。")

    if nav == "驾驶舱":
        if 'df' in st.session_state and st.session_state.df is not None:
            show_dashboard(st.session_state.df)
        else:
            path = os.path.join(DATA_DIR, "analyzed_comments.csv")
            if os.path.exists(path):
                show_dashboard(pd.read_csv(path))
            else:
                st.warning("请先去数据中心分析数据")
    elif nav == "数据中心":
        page_data_center()
    elif nav == "前沿技术":
        if 'df' in st.session_state and st.session_state.df is not None:
            create_advanced_tech_page(st.session_state.df)
        else:
            path = os.path.join(DATA_DIR, "analyzed_comments.csv")
            if os.path.exists(path):
                create_advanced_tech_page(pd.read_csv(path))
            else:
                st.warning("请先去数据中心分析数据")
    elif nav == "前沿算法":
        if 'df' in st.session_state and st.session_state.df is not None:
            create_advanced_analysis_page(st.session_state.df)
        else:
            path = os.path.join(DATA_DIR, "analyzed_comments.csv")
            if os.path.exists(path):
                create_advanced_analysis_page(pd.read_csv(path))
            else:
                st.warning("请先去数据中心分析数据")
    elif nav == "智能问答":
        page_chatbot()
    elif nav == "报告下载":
        page_report()

if __name__ == "__main__":
    main()
