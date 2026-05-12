# -*- coding: utf-8 -*-
"""
前沿技术可视化模块
集成知识图谱、舆情传播、情感演化、多模态分析的可视化展示
"""
import os
import sys
import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Optional
from collections import Counter
import networkx as nx

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.analysis.knowledge_graph import KnowledgeGraphBuilder
from src.analysis.opinion_propagation import PublicOpinionAnalyzer
from src.analysis.sentiment_evolution import SentimentEvolutionAnalyzer
from src.analysis.multimodal_sentiment import MultimodalSentimentAnalyzer

def create_knowledge_graph_page(df: pd.DataFrame):
    """知识图谱可视化页面"""
    st.markdown("## 🗺️ 知识图谱分析")
    st.markdown("基于评论数据构建实体-关系知识图谱，支持舆情溯源和深度分析")
    
    if df is None or len(df) == 0:
        st.warning("⚠️ 请先加载数据")
        return
    
    with st.spinner("正在构建知识图谱..."):
        builder = KnowledgeGraphBuilder()
        builder.build_from_dataframe(df)
        insights = builder.get_insights()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 实体分布统计")
        
        entity_data = insights.get("entity_distribution", {})
        if entity_data:
            entity_df = pd.DataFrame([
                {"实体类型": k, "数量": v}
                for k, v in entity_data.items()
            ]).sort_values("数量", ascending=False)
            
            fig = px.bar(
                entity_df,
                x="数量",
                y="实体类型",
                orientation='h',
                title='各类型实体数量分布',
                color="数量",
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🏆 Top实体排行")
        
        top_entities = insights.get("top_mentioned_entities", [])
        if top_entities:
            for i, entity in enumerate(top_entities[:10], 1):
                sentiment = entity.get("avg_sentiment", 0)
                color = "#3FB950" if sentiment > 0.6 else "#F85149" if sentiment < 0.4 else "#F59E0B"
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 8px; 
                            background: #21262D; border-radius: 6px; margin-bottom: 4px;">
                    <span>{i}. {entity['text']}</span>
                    <span style="color: {color}">{entity['count']}次</span>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### ⚠️ 问题实体分析")
        criticized = insights.get("most_criticized_entities", [])
        if criticized:
            crit_df = pd.DataFrame(criticized[:10])
            if not crit_df.empty:
                fig = px.bar(
                    crit_df,
                    x="count",
                    y="text",
                    orientation='h',
                    title='被批评最多的实体',
                    color="count",
                    color_continuous_scale='Reds'
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with col4:
        st.markdown("### ✅ 优质实体分析")
        praised = insights.get("most_praised_entities", [])
        if praised:
            praise_df = pd.DataFrame(praised[:10])
            if not praise_df.empty:
                fig = px.bar(
                    praise_df,
                    x="count",
                    y="text",
                    orientation='h',
                    title='被赞扬最多的实体',
                    color="count",
                    color_continuous_scale='Greens'
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 💾 导出知识图谱")
    if st.button("导出知识图谱JSON"):
        output_path = os.path.join(PROJECT_ROOT, "data", "viz", "knowledge_graph.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        builder.save_graph(output_path)
        st.success(f"✅ 已导出到: {output_path}")

def create_propagation_page(df: pd.DataFrame):
    """舆情传播分析页面"""
    st.markdown("## 📡 舆情传播分析")
    st.markdown("分析舆情在社交网络中的传播路径和影响力节点")
    
    if df is None or len(df) == 0:
        st.warning("⚠️ 请先加载数据")
        return
    
    with st.spinner("正在分析传播网络..."):
        analyzer = PublicOpinionAnalyzer()
        analyzer.build_from_dataframe(df)
        analyzer.calculate_pagerank()
        insights = analyzer.get_insights()
    
    col1, col2, col3 = st.columns(3)
    
    network_stats = insights.get("network_stats", {})
    
    with col1:
        st.metric("节点总数", network_stats.get("total_nodes", 0))
    with col2:
        st.metric("边总数", network_stats.get("total_edges", 0))
    with col3:
        st.metric("平均度数", f"{network_stats.get('avg_degree', 0):.2f}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏆 影响力节点排行")
        top_influencers = insights.get("top_influencers", [])
        if top_influencers:
            inf_df = pd.DataFrame(top_influencers[:15])
            if not inf_df.empty and 'pagerank' in inf_df.columns:
                fig = px.bar(
                    inf_df,
                    x="pagerank",
                    y="name",
                    orientation='h',
                    title='Top 15 影响力节点 (PageRank)',
                    color="pagerank",
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=450
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 情感分布")
        sentiment_dist = insights.get("sentiment_distribution", {})
        if sentiment_dist:
            sent_df = pd.DataFrame([
                {"情感": k, "数量": v}
                for k, v in sentiment_dist.items()
            ])
            fig = px.pie(
                sent_df,
                values="数量",
                names="情感",
                title='节点情感分布',
                hole=0.4
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 📈 时间序列分析")
    time_series = insights.get("time_series", {})
    if time_series.get("time_points"):
        ts_df = pd.DataFrame({
            "时间": time_series["time_points"],
            "评论数": [time_series["data"][t]["count"] for t in time_series["time_points"]],
            "积极": [time_series["data"][t]["positive"] for t in time_series["time_points"]],
            "消极": [time_series["data"][t]["negative"] for t in time_series["time_points"]]
        })
        
        fig = make_subplots(rows=2, cols=1, subplot_titles=('评论数量趋势', '情感变化趋势'))
        
        fig.add_trace(
            go.Scatter(x=ts_df["时间"], y=ts_df["评论数"], name='评论数', line=dict(color='#2383E2')),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=ts_df["时间"], y=ts_df["积极"], name='积极', line=dict(color='#3FB950')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=ts_df["时间"], y=ts_df["消极"], name='消极', line=dict(color='#F85149')),
            row=2, col=1
        )
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            height=500,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    if st.button("导出传播分析JSON"):
        output_path = os.path.join(PROJECT_ROOT, "data", "viz", "opinion_propagation.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        analyzer.save_analysis(output_path)
        st.success(f"✅ 已导出到: {output_path}")

def create_evolution_page(df: pd.DataFrame):
    """情感动态演化分析页面"""
    st.markdown("## ⏰ 情感动态演化分析")
    st.markdown("分析舆情随时间的变化规律，检测演化阶段和新兴话题")
    
    if df is None or len(df) == 0:
        st.warning("⚠️ 请先加载数据")
        return
    
    with st.spinner("正在分析情感演化..."):
        analyzer = SentimentEvolutionAnalyzer(os.path.join(PROJECT_ROOT, "data", "viz"))
        insights = analyzer.get_evolution_insights(df)
    
    st.markdown("### 📊 演化阶段检测")
    phases = insights.get("evolution_phases", [])
    
    if phases:
        phase_data = []
        for i, phase in enumerate(phases, 1):
            phase_data.append({
                "阶段": f"阶段{i}",
                "趋势": phase.get("trend", "stable"),
                "起始CSI": phase.get("start_csi", 0),
                "结束CSI": phase.get("end_csi", 0),
                "变化幅度": phase.get("magnitude", 0)
            })
        
        phase_df = pd.DataFrame(phase_data)
        
        trend_colors = {
            "improving": "#3FB950",
            "stable": "#F59E0B",
            "declining": "#F85149"
        }
        
        cols = st.columns(len(phases) if len(phases) <= 6 else 6)
        for i, (col, phase) in enumerate(zip(cols, phases)):
            if i >= 6:
                break
            with col:
                trend = phase.get("trend", "stable")
                trend_cn = {"improving": "改善", "stable": "稳定", "declining": "恶化"}.get(trend, "稳定")
                color = trend_colors.get(trend, "#F59E0B")
                st.markdown(f"""
                <div style="background: #21262D; padding: 16px; border-radius: 8px; text-align: center;
                            border-left: 4px solid {color};">
                    <div style="color: #8B949E; font-size: 12px;">阶段 {i+1}</div>
                    <div style="font-size: 20px; font-weight: bold; color: {color};">{trend_cn}</div>
                    <div style="font-size: 12px; color: #8B949E;">
                        CSI: {phase.get('start_csi', 0):.1f} → {phase.get('end_csi', 0):.1f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔄 情感转移矩阵")
        sentiment_shift = insights.get("sentiment_shift", {})
        transition_matrix = sentiment_shift.get("transition_matrix", {})
        
        if transition_matrix:
            labels = ["积极", "中性", "消极"]
            z = []
            for from_sent in labels:
                row = []
                for to_sent in labels:
                    row.append(transition_matrix.get(from_sent, {}).get(to_sent, 0))
                z.append(row)
            
            fig = px.imshow(
                z,
                x=labels,
                y=labels,
                title='情感转移概率矩阵',
                color_continuous_scale='RdYlGn',
                text_auto='.2f'
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🔥 新兴话题检测")
        emerging_topics = insights.get("emerging_topics", {}).get("emerging_topics", [])
        
        if emerging_topics:
            for i, topic in enumerate(emerging_topics[:8], 1):
                growth = topic.get("growth_rate", 0)
                if growth == float('inf'):
                    growth_str = "∞"
                    color = "#3FB950"
                else:
                    growth_str = f"{growth:.1%}"
                    color = "#3FB950" if growth > 0 else "#F85149"
                
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 8px; 
                            background: #21262D; border-radius: 6px; margin-bottom: 4px;">
                    <span>{i}. {topic['keyword']}</span>
                    <span style="color: {color}">{growth_str}</span>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("导出演化分析JSON"):
        output_path = os.path.join(PROJECT_ROOT, "data", "viz", "sentiment_evolution.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        analyzer.save_analysis(insights, output_path)
        st.success(f"✅ 已导出到: {output_path}")

def create_multimodal_page(df: pd.DataFrame):
    """多模态情感分析页面"""
    st.markdown("## 🎨 多模态情感分析")
    st.markdown("综合分析文本、表情符号等多种模态的情感信息")
    
    analyzer = MultimodalSentimentAnalyzer()
    
    st.markdown("### 🔧 分析设置")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        text_weight = st.slider("文本权重", 0.0, 1.0, 0.6, 0.1)
    with col2:
        emoji_weight = st.slider("表情权重", 0.0, 1.0, 0.3, 0.1)
    with col3:
        image_weight = st.slider("图片权重", 0.0, 1.0, 0.1, 0.1)
    
    analyzer.set_weights(text_weight, emoji_weight, image_weight)
    
    st.markdown("---")
    
    st.markdown("### 📝 单条评论分析")
    
    test_text = st.text_area(
        "输入评论文本",
        value="迪士尼真的太好玩了！😊🎉 服务态度也很好，下次还来！❤️",
        height=100
    )
    
    if st.button("分析情感"):
        with st.spinner("分析中..."):
            result = analyzer.analyze(test_text)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            polarity = result.get("final_polarity", "中性")
            color = "#3FB950" if polarity == "积极" else "#F85149" if polarity == "消极" else "#F59E0B"
            st.markdown(f"""
            <div style="background: #21262D; padding: 20px; border-radius: 12px; text-align: center;">
                <div style="color: #8B949E; font-size: 14px;">最终情感</div>
                <div style="font-size: 32px; font-weight: bold; color: {color};">{polarity}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            score = result.get("final_score", 0)
            st.metric("情感分数", f"{score:.3f}")
        
        with col3:
            csi = result.get("csi_score", 50)
            st.metric("CSI指数", csi)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 各模态分析结果")
            
            emoji_analysis = result.get("emoji_analysis", {})
            if emoji_analysis.get("has_emoji"):
                st.markdown("**表情符号分析:**")
                emojis = emoji_analysis.get("emojis", [])
                for emoji_info in emojis:
                    st.markdown(f"- {emoji_info['emoji']}: {emoji_info['emotion']} ({emoji_info['sentiment']})")
                st.markdown(f"主导情感: {emoji_analysis.get('dominant_sentiment', 'neutral')}")
            else:
                st.info("未检测到表情符号")
        
        with col2:
            st.markdown("### ⚖️ 权重分配")
            
            weights = result.get("weights_used", {})
            modalities = result.get("modalities_used", {})
            
            weight_df = pd.DataFrame([
                {"模态": "文本", "权重": weights.get("text", 0), "是否使用": modalities.get("text", False)},
                {"模态": "表情", "权重": weights.get("emoji", 0), "是否使用": modalities.get("emoji", False)},
                {"模态": "图片", "权重": weights.get("image", 0), "是否使用": modalities.get("image", False)}
            ])
            
            fig = px.pie(
                weight_df,
                values="权重",
                names="模态",
                title='模态权重分配',
                hole=0.4
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    if df is not None and len(df) > 0:
        st.markdown("### 📈 批量分析统计")
        
        if st.button("对当前数据进行多模态分析"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            for i, (_, row) in enumerate(df.iterrows()):
                text = str(row.get("content", ""))
                result = analyzer.analyze(text)
                results.append(result.get("final_polarity", "中性"))
                progress_bar.progress((i + 1) / len(df))
                status_text.text(f"分析进度: {i+1}/{len(df)}")
            
            df["multimodal_sentiment"] = results
            
            sentiment_counts = Counter(results)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    names=list(sentiment_counts.keys()),
                    values=list(sentiment_counts.values()),
                    title='多模态情感分布',
                    hole=0.4
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**统计结果:**")
                for sentiment, count in sentiment_counts.items():
                    pct = count / len(df) * 100
                    st.markdown(f"- {sentiment}: {count} ({pct:.1f}%)")
            
            st.success("✅ 多模态分析完成！")

def create_advanced_tech_page(df: pd.DataFrame):
    """前沿技术综合展示页面"""
    st.markdown("# 🔬 前沿技术分析中心")
    st.markdown("集成知识图谱、舆情传播、情感演化、多模态分析等前沿技术")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ 知识图谱", "📡 舆情传播", "⏰ 情感演化", "🎨 多模态分析"
    ])
    
    with tab1:
        create_knowledge_graph_page(df)
    
    with tab2:
        create_propagation_page(df)
    
    with tab3:
        create_evolution_page(df)
    
    with tab4:
        create_multimodal_page(df)

if __name__ == "__main__":
    print("前沿技术可视化模块加载完成")