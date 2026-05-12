# -*- coding: utf-8 -*-
"""
驾驶舱页面模块：核心数据展示 + 整改推演
"""
import os
import glob
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.utils.chart_config import apply_dark_theme, COLOR_MAP_SENTIMENT, COLOR_SEQUENCES

try:
    from streamlit import components
except ImportError:
    components = None


def show_dashboard(df, data_dir):
    """驾驶舱：核心数据展示 + 整改推演

    Args:
        df: 已完成情感分析的数据框
        data_dir: 数据目录路径
    """
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
        _render_overview_tab(df)

    with tab_facility:
        _render_facility_tab(df)

    with tab_aspect:
        _render_aspect_tab(df)

    with tab_advanced:
        _render_advanced_tab(df, data_dir)

    with tab_detail:
        _render_detail_tab(df)


def _render_overview_tab(df):
    """概览分析：情感分布饼图 + 满意度直方图"""
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
                    color_discrete_map=COLOR_MAP_SENTIMENT,
                    title='情感倾向占比'
                )
                apply_dark_theme(fig, height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("等待数据...")
    with col2:
        with st.container():
            st.markdown("### 📈 满意度分布")
            if 'csi_score' in df.columns:
                fig = px.histogram(
                    df, x='csi_score', nbins=20,
                    title='CSI满意度指数分布',
                    color_discrete_sequence=COLOR_SEQUENCES["primary"],
                    marginal='box'
                )
                apply_dark_theme(fig, height=350, yaxis_title="数量")
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
                    x=urgency_counts.index, y=urgency_counts.values,
                    title='问题紧急度分布',
                    color_discrete_sequence=COLOR_SEQUENCES["danger"]
                )
                apply_dark_theme(fig, height=300, xaxis_title='紧急度', yaxis_title='数量')
                st.plotly_chart(fig, use_container_width=True)
    with col4:
        with st.container():
            st.markdown("### 📊 满意度 vs 紧急度")
            if 'csi_score' in df.columns and 'urgency_score' in df.columns:
                fig = px.scatter(
                    df, x='csi_score', y='urgency_score',
                    color='polarity_label', size='urgency_score',
                    hover_data=['content'], title='满意度与紧急度关系',
                    color_discrete_map=COLOR_MAP_SENTIMENT
                )
                apply_dark_theme(fig, height=300)
                st.plotly_chart(fig, use_container_width=True)


def _render_facility_tab(df):
    """设施类型分析：各设施满意度柱状图 + 情感构成堆叠图 + 小提琴图"""
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.container():
            st.markdown("### 🏢 各设施类型满意度")
            if 'facility_type' in df.columns and 'csi_score' in df.columns:
                facility_avg = df.groupby('facility_type')['csi_score'].mean().sort_values(ascending=False)
                fig = px.bar(
                    x=facility_avg.values, y=facility_avg.index,
                    orientation='h', title='各设施类型平均CSI指数',
                    color=facility_avg.values,
                    color_continuous_scale='RdYlGn', range_color=[50, 100]
                )
                apply_dark_theme(fig, height=400)
                st.plotly_chart(fig, use_container_width=True)
    with col2:
        with st.container():
            st.markdown("### 📊 设施类型情感构成")
            if 'facility_type' in df.columns and 'polarity_label' in df.columns:
                crosstab = pd.crosstab(df['facility_type'], df['polarity_label'])
                crosstab_pct = crosstab.div(crosstab.sum(axis=1), axis=0) * 100
                fig = px.bar(
                    crosstab_pct, orientation='h', title='各设施类型情感占比',
                    color_discrete_map=COLOR_MAP_SENTIMENT
                )
                apply_dark_theme(fig, height=400, barmode='stack')
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    with st.container():
        st.markdown("### 🎻 各设施类型满意度分布（小提琴图）")
        if 'facility_type' in df.columns and 'csi_score' in df.columns:
            fig = px.violin(
                df, x='facility_type', y='csi_score',
                color='facility_type', box=True,
                title='各设施类型满意度分布',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            apply_dark_theme(fig, height=450)
            st.plotly_chart(fig, use_container_width=True)


def _render_aspect_tab(df):
    """方面维度分析：各方面满意度对比 + 雷达图 + 热力图"""
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.container():
            st.markdown("### 📋 各方面满意度对比")
            if 'aspect' in df.columns and 'csi_score' in df.columns:
                aspect_avg = df.groupby('aspect')['csi_score'].mean().sort_values(ascending=False)
                fig = px.bar(
                    x=aspect_avg.index, y=aspect_avg.values,
                    title='各方面平均CSI指数',
                    color=aspect_avg.values,
                    color_continuous_scale='RdYlGn', range_color=[50, 100]
                )
                apply_dark_theme(fig, height=350, margin=dict(t=50, b=50, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
    with col2:
        with st.container():
            st.markdown("### 🎯 方面综合表现雷达图")
            if 'aspect' in df.columns and 'csi_score' in df.columns:
                aspect_avg = df.groupby('aspect')['csi_score'].mean()
                if len(aspect_avg) >= 3:
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=aspect_avg.values, theta=aspect_avg.index,
                        fill='toself', name='各方面满意度',
                        line=dict(color='#2383E2'),
                        fillcolor='rgba(35, 131, 226, 0.3)'
                    ))
                    apply_dark_theme(fig, height=350, title='各方面满意度综合表现',
                                     polar=dict(
                                         radialaxis=dict(visible=True, range=[0, 100]),
                                         angularaxis=dict(showticklabels=True)
                                     ),
                                     showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    with st.container():
        st.markdown("### 🔥 设施类型-方面热力图")
        if 'facility_type' in df.columns and 'aspect' in df.columns and 'csi_score' in df.columns:
            heatmap_data = df.groupby(['facility_type', 'aspect'])['csi_score'].mean().unstack()
            fig = px.imshow(
                heatmap_data, title='设施类型-方面满意度热力图',
                color_continuous_scale='RdYlGn', range_color=[50, 100],
                text_auto='.1f'
            )
            apply_dark_theme(fig, height=500, margin=dict(t=50, b=50, l=50, r=50))
            st.plotly_chart(fig, use_container_width=True)


def _render_advanced_tab(df, data_dir):
    """深度分析：桑基图 + 漏斗图 + 词云 + 极坐标图 + 面积趋势图"""
    viz_dir = os.path.join(data_dir, "viz")

    col1, col2 = st.columns([1, 1])
    with col1:
        with st.container():
            st.markdown("### 🔄 归因流向桑基图")
            sankey_path = os.path.join(viz_dir, "sankey_flow.html")
            if os.path.exists(sankey_path) and components:
                with open(sankey_path, 'r', encoding='utf-8') as f:
                    st.components.v1.html(f.read(), height=400)
            else:
                st.info("请先运行分析以生成桑基图")
    with col2:
        with st.container():
            st.markdown("### 🔻 情感漏斗图")
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
            wordcloud_path = os.path.join(viz_dir, "wordcloud.png")
            if os.path.exists(wordcloud_path):
                st.image(wordcloud_path, use_container_width=True)
            else:
                st.info("请先运行分析以生成词云图")
    with col4:
        with st.container():
            st.markdown("### 📐 极坐标分布图")
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
            area_path = os.path.join(viz_dir, "area_chart.png")
            if os.path.exists(area_path):
                st.image(area_path, use_container_width=True)
            else:
                st.info("请先运行分析以生成面积图")
    with col6:
        with st.container():
            st.markdown("### 🎻 更多图表")
            chart_files = glob.glob(os.path.join(viz_dir, "*.png"))
            if chart_files:
                st.markdown("**可用图表列表:**")
                for chart in sorted(chart_files):
                    st.caption(f"📊 {os.path.basename(chart)}")
            else:
                st.info("暂无图表文件")


def _render_detail_tab(df):
    """详细数据列表：支持按设施类型、情感倾向、评论方面筛选"""
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
    for col in ['polarity_label', 'csi_score', 'facility_type', 'aspect', 'urgency_score', 'specific_emotion']:
        if col in df.columns:
            display_cols.append(col)

    page_size = 100
    total_rows = len(filtered_df)
    if total_rows > page_size:
        total_pages = (total_rows - 1) // page_size + 1
        page_num = st.number_input("页码", min_value=1, max_value=total_pages, value=1, key="detail_page")
        start_idx = (page_num - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        st.dataframe(
            filtered_df[display_cols].iloc[start_idx:end_idx],
            use_container_width=True, height=500
        )
        st.caption(f"第 {page_num}/{total_pages} 页 | 显示 {start_idx+1}-{end_idx} 条（总计 {total_rows} 条）")
    else:
        st.dataframe(filtered_df[display_cols], use_container_width=True, height=500)
        st.caption(f"共显示 {total_rows} 条评论（总计 {len(df)} 条）")

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
