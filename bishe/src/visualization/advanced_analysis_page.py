# -*- coding: utf-8 -*-
"""
前沿分析可视化页面
展示Transformer时序预测、动态主题模型、因果分析、对比学习等前沿技术
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
from datetime import datetime
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.analysis.advanced_algorithms import (
    AdvancedAnalysisPipeline,
    TransformerTimeSeriesPredictor,
    DynamicTopicModel,
    CausalAnalyzer,
    ContrastiveSentimentEnhancer
)

def create_advanced_analysis_page(df: pd.DataFrame):
    """
    创建前沿分析页面
    
    包含：Transformer预测、动态主题、因果分析、对比学习
    """
    st.markdown("# 🚀 前沿算法分析中心")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <p style="color: #8B949E; margin: 0;">
            集成前沿NLP与机器学习算法，包括 <b>Transformer时序预测</b>、<b>动态主题模型</b>、
            <b>因果推断</b>、<b>对比学习</b> 等先进技术
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if df is None or len(df) == 0:
        st.warning("⚠️ 请先加载数据")
        return
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Transformer预测", "🔄 动态主题模型", "🔗 因果分析", "🎯 对比学习"
    ])
    
    with tab1:
        create_transformer_prediction_tab(df)
    
    with tab2:
        create_dtm_tab(df)
    
    with tab3:
        create_causal_analysis_tab(df)
    
    with tab4:
        create_contrastive_learning_tab(df)


def create_transformer_prediction_tab(df: pd.DataFrame):
    """Transformer时序预测标签页"""
    st.markdown("## 📈 Transformer时序预测")
    st.markdown("""
    <div style="color: #8B949E; margin-bottom: 16px;">
        使用Transformer架构预测未来满意度趋势，对比传统统计模型（ARIMA/Prophet）与深度学习模型的性能差异
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ⚙️ 模型配置")
        
        seq_length = st.slider("序列长度", 3, 30, 7, help="用于预测的历史数据天数")
        predict_steps = st.slider("预测天数", 1, 30, 7, help="预测未来多少天")
        
        target_col = st.selectbox(
            "预测目标",
            options=['csi_score', 'urgency_score'] if 'urgency_score' in df.columns else ['csi_score'],
            help="选择要预测的指标"
        )
        
        if st.button("🚀 训练Transformer模型", type="primary"):
            with st.spinner("训练中..."):
                predictor = TransformerTimeSeriesPredictor()
                train_result = predictor.train(df, target_col=target_col, seq_length=seq_length)
                
                if "error" in train_result:
                    st.error(f"训练失败: {train_result['error']}")
                else:
                    st.session_state['transformer_predictor'] = predictor
                    st.session_state['train_result'] = train_result
                    
                    st.success("✅ 模型训练完成！")
                    
                    metrics = train_result.get("metrics", {})
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric("训练损失", f"{metrics.get('train_loss', metrics.get('train_mse', 0)):.4f}")
                    with col_m2:
                        st.metric("测试损失", f"{metrics.get('test_loss', metrics.get('test_mse', 0)):.4f}")
    
    with col2:
        st.markdown("### 📊 预测结果")
        
        if 'transformer_predictor' in st.session_state:
            predictor = st.session_state['transformer_predictor']
            
            prediction = predictor.predict(steps=predict_steps)
            
            if "error" not in prediction:
                predictions = prediction["predictions"]
                dates = prediction["dates"]
                trend = prediction["trend"]
                
                trend_color = "#3FB950" if trend == "上升" else "#F85149" if trend == "下降" else "#F59E0B"
                
                st.markdown(f"""
                <div style="background: #21262D; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                    <span style="color: #8B949E;">预测趋势:</span>
                    <span style="color: {trend_color}; font-size: 20px; font-weight: bold;">{trend}</span>
                </div>
                """, unsafe_allow_html=True)
                
                fig = go.Figure()
                
                if 'csi_score' in df.columns:
                    historical = df['csi_score'].tail(30).values
                    historical_dates = pd.date_range(end=datetime.now(), periods=len(historical))
                    
                    fig.add_trace(go.Scatter(
                        x=historical_dates,
                        y=historical,
                        mode='lines',
                        name='历史数据',
                        line=dict(color='#2383E2')
                    ))
                
                pred_dates = pd.to_datetime(dates)
                fig.add_trace(go.Scatter(
                    x=pred_dates,
                    y=predictions,
                    mode='lines+markers',
                    name='预测数据',
                    line=dict(color='#F59E0B', dash='dash'),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title='满意度指数预测',
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=400,
                    xaxis_title="日期",
                    yaxis_title="CSI得分"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 预测详情"):
                    pred_df = pd.DataFrame({
                        "日期": dates,
                        "预测CSI": [round(p, 1) for p in predictions]
                    })
                    st.dataframe(pred_df, use_container_width=True)
        else:
            st.info("请先训练模型")


def create_dtm_tab(df: pd.DataFrame):
    """动态主题模型标签页"""
    st.markdown("## 🔄 动态主题模型")
    st.markdown("""
    <div style="color: #8B949E; margin-bottom: 16px;">
        分析主题随时间的演化，识别新兴问题和衰退话题，支持时间切片分析
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ⚙️ 分析配置")
        
        n_topics = st.slider("主题数量", 3, 15, 5)
        time_slices = st.slider("时间切片数", 2, 10, 4)
        
        if st.button("🔍 分析主题演化", type="primary"):
            with st.spinner("分析中..."):
                dtm = DynamicTopicModel()
                result = dtm.analyze_topic_evolution(df, n_topics=n_topics, time_slices=time_slices)
                
                if "error" in result:
                    st.error(f"分析失败: {result['error']}")
                else:
                    st.session_state['dtm_result'] = result
                    st.success("✅ 分析完成！")
    
    with col2:
        st.markdown("### 📊 主题演化结果")
        
        if 'dtm_result' in st.session_state:
            result = st.session_state['dtm_result']
            
            topic_changes = result.get("topic_changes", [])
            
            if topic_changes:
                st.markdown("#### 🔥 话题变化检测")
                
                for change in topic_changes[:6]:
                    change_type = change["type"]
                    color = "#3FB950" if change_type == "新兴话题" else "#F85149"
                    words = ", ".join(change["words"][:3])
                    
                    st.markdown(f"""
                    <div style="background: #21262D; padding: 12px; border-radius: 8px; margin-bottom: 8px;
                                border-left: 4px solid {color};">
                        <span style="color: {color}; font-weight: bold;">{change_type}</span>
                        <span style="color: #8B949E;"> ({change["from"]} → {change["to"]})</span><br>
                        <span style="color: #FFFFFF;">{words}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            topics = result.get("topics", {})
            
            if topics:
                st.markdown("#### 📋 各时期热门话题")
                
                for period, topic_data in topics.items():
                    with st.expander(f"📅 {period} ({topic_data.get('doc_count', 0)} 条评论)"):
                        top_words = topic_data.get("top_words", [])[:10]
                        
                        word_df = pd.DataFrame(top_words)
                        if not word_df.empty:
                            fig = px.bar(
                                word_df,
                                x="count",
                                y="word",
                                orientation='h',
                                title=f'{period} 热门词汇',
                                color="count",
                                color_continuous_scale='Blues'
                            )
                            fig.update_layout(
                                template="plotly_dark",
                                paper_bgcolor="rgba(0,0,0,0)",
                                height=300,
                                yaxis={'categoryorder': 'total ascending'}
                            )
                            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("请先运行主题演化分析")


def create_causal_analysis_tab(df: pd.DataFrame):
    """因果分析标签页"""
    st.markdown("## 🔗 因果推断分析")
    st.markdown("""
    <div style="color: #8B949E; margin-bottom: 16px;">
        从相关性分析提升到因果推断，识别满意度变化的潜在驱动因素，支持Granger因果检验
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ⚙️ 分析配置")
        
        analysis_type = st.radio(
            "分析类型",
            ["因果因素分析", "Granger因果检验"],
            horizontal=True
        )
        
        if st.button("🔬 执行因果分析", type="primary"):
            with st.spinner("分析中..."):
                analyzer = CausalAnalyzer()
                
                if analysis_type == "因果因素分析":
                    result = analyzer.analyze_causal_factors(df)
                else:
                    result = analyzer.granger_causality_test(
                        df, 
                        col1='urgency_score' if 'urgency_score' in df.columns else 'csi_score',
                        col2='csi_score'
                    )
                
                st.session_state['causal_result'] = result
                st.success("✅ 分析完成！")
    
    with col2:
        st.markdown("### 📊 因果分析结果")
        
        if 'causal_result' in st.session_state:
            result = st.session_state['causal_result']
            
            if analysis_type == "因果因素分析":
                factors = result.get("factors", {})
                
                for factor_name, factor_data in factors.items():
                    st.markdown(f"#### 📌 {factor_name}")
                    
                    if factor_name == "platform":
                        platform_df = pd.DataFrame([
                            {"平台": k, "平均CSI": v["mean_outcome"], "因果效应": v["causal_effect"]}
                            for k, v in factor_data.items()
                        ])
                        
                        fig = px.bar(
                            platform_df,
                            x="平台",
                            y="因果效应",
                            title='平台对满意度的因果效应',
                            color="因果效应",
                            color_continuous_scale='RdYlGn'
                        )
                        fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            height=350
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif factor_name == "polarity_label":
                        for sentiment, data in factor_data.items():
                            st.markdown(f"""
                            <div style="background: #21262D; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                                <b>{sentiment}</b>: 平均CSI {data['mean_outcome']} ({data['sample_size']} 样本)
                            </div>
                            """, unsafe_allow_html=True)
                    
                    else:
                        if "correlation" in factor_data:
                            st.markdown(f"""
                            <div style="background: #21262D; padding: 16px; border-radius: 8px;">
                                <p style="margin: 0;"><b>相关系数:</b> {factor_data['correlation']}</p>
                                <p style="margin: 0;"><b>P值:</b> {factor_data['p_value']}</p>
                                <p style="margin: 0;"><b>显著性:</b> 
                                    <span style="color: {'#3FB950' if factor_data['significant'] else '#F85149'}">
                                        {'显著' if factor_data['significant'] else '不显著'}
                                    </span>
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
            
            else:
                lags = result.get("lags", {})
                if lags:
                    lag_df = pd.DataFrame([
                        {"滞后期": k, "F统计量": v["f_statistic"], "P值": v["p_value"], "显著": v["significant"]}
                        for k, v in lags.items()
                    ])
                    
                    st.dataframe(lag_df, use_container_width=True)
                    
                    conclusion = result.get("conclusion", "")
                    st.info(f"📊 结论: {conclusion}")
        else:
            st.info("请先执行因果分析")


def create_contrastive_learning_tab(df: pd.DataFrame):
    """对比学习标签页"""
    st.markdown("## 🎯 对比学习情感增强")
    st.markdown("""
    <div style="color: #8B949E; margin-bottom: 16px;">
        使用对比学习（SimCSE风格）优化情感表示，提升情感分类精度，计算情感类别间的语义距离
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ⚙️ 分析配置")
        
        sample_size = st.slider("样本数量", 100, 1000, 500, step=100)
        
        if st.button("🎯 执行对比学习分析", type="primary"):
            with st.spinner("计算嵌入中..."):
                enhancer = ContrastiveSentimentEnhancer()
                
                sample_df = df.head(sample_size) if len(df) > sample_size else df
                result = enhancer.enhance_sentiment_analysis(sample_df)
                
                st.session_state['contrastive_result'] = result
                st.success("✅ 分析完成！")
    
    with col2:
        st.markdown("### 📊 对比学习结果")
        
        if 'contrastive_result' in st.session_state:
            result = st.session_state['contrastive_result']
            
            embedding_shape = result.get("embedding_shape", (0, 0))
            st.metric("嵌入维度", f"{embedding_shape[0]} × {embedding_shape[1]}")
            
            centroid_distances = result.get("centroid_distances", {})
            
            if centroid_distances:
                st.markdown("#### 📏 情感类别语义距离")
                
                distance_df = pd.DataFrame([
                    {"类别对": k, "语义距离": round(v, 3)}
                    for k, v in centroid_distances.items()
                ])
                
                fig = px.bar(
                    distance_df,
                    x="类别对",
                    y="语义距离",
                    title='情感类别间语义距离',
                    color="语义距离",
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"💡 {result.get('interpretation', '')}")
            
            sentiment_centroids = result.get("sentiment_centroids", {})
            if sentiment_centroids:
                st.markdown("#### 📊 情感中心点统计")
                
                for sentiment, data in sentiment_centroids.items():
                    st.markdown(f"""
                    <div style="background: #21262D; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                        <b>{sentiment}</b>: 维度 {data['dim']}, 范数 {data['norm']:.2f}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("请先执行对比学习分析")


def run_advanced_analysis_and_save(df: pd.DataFrame) -> Dict[str, Any]:
    """
    运行完整的前沿分析并保存结果
    
    Args:
        df: 分析后的数据框
    
    Returns:
        分析结果
    """
    pipeline = AdvancedAnalysisPipeline()
    results = pipeline.run_full_analysis(df)
    return results


if __name__ == "__main__":
    print("前沿分析可视化页面加载完成")
