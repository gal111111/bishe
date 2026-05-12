# -*- coding: utf-8 -*-
"""
高级分析模块
提供更复杂的数据分析功能
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Optional, Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def analyze_sentiment_trends(df: pd.DataFrame, time_col: str = 'date') -> Optional[go.Figure]:
    """分析情感趋势"""
    try:
        # 确保时间列存在
        if time_col not in df.columns:
            # 如果没有时间列，使用索引作为时间
            df = df.copy()
            df[time_col] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
        
        # 按时间排序
        df_sorted = df.sort_values(time_col)
        
        # 计算每日平均满意度
        if 'csi_score' in df_sorted.columns:
            # 按日期分组计算平均满意度
            daily_avg = df_sorted.groupby(df_sorted[time_col].dt.date)['csi_score'].mean().reset_index()
            daily_avg[time_col] = pd.to_datetime(daily_avg[time_col])
            
            # 创建趋势图
            fig = go.Figure()
            
            # 添加满意度趋势线
            fig.add_trace(go.Scatter(
                x=daily_avg[time_col],
                y=daily_avg['csi_score'],
                mode='lines+markers',
                name='平均满意度',
                line=dict(color='#3498db', width=2),
                marker=dict(size=4, color='#3498db')
            ))
            
            # 添加滚动平均值
            if len(daily_avg) >= 7:
                daily_avg['rolling_avg'] = daily_avg['csi_score'].rolling(window=7, min_periods=1).mean()
                fig.add_trace(go.Scatter(
                    x=daily_avg[time_col],
                    y=daily_avg['rolling_avg'],
                    mode='lines',
                    name='7日滚动平均',
                    line=dict(color='#e74c3c', width=2, dash='dash')
                ))
            
            # 更新布局
            fig.update_layout(
                title='满意度趋势分析',
                xaxis_title='日期',
                yaxis_title='平均满意度指数',
                legend_title='指标',
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            return fig
        
        return None
    except Exception as e:
        print(f"⚠️  分析情感趋势失败: {e}")
        return None

def analyze_aspect_correlation(df: pd.DataFrame) -> Optional[go.Figure]:
    """分析各方面之间的相关性"""
    try:
        if 'aspect' not in df.columns or 'csi_score' not in df.columns:
            return None
        
        # 计算每个方面的平均满意度
        aspect_avg = df.groupby('aspect')['csi_score'].mean().reset_index()
        aspect_avg = aspect_avg[aspect_avg['aspect'] != '其他']  # 排除其他方面
        
        if len(aspect_avg) < 2:
            return None
        
        # 创建相关性热力图数据
        # 这里使用简单的方面满意度对比，因为真正的相关性需要更多维度
        aspect_pivot = df.pivot_table(index='content', columns='aspect', values='csi_score', aggfunc='mean')
        correlation_matrix = aspect_pivot.corr()
        
        # 创建热力图
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            colorscale='RdYlGn',
            text=correlation_matrix.values.round(2),
            texttemplate='%{text}',
            hoverongaps=False
        ))
        
        # 更新布局
        fig.update_layout(
            title='各方面满意度相关性分析',
            xaxis_title='方面',
            yaxis_title='方面',
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            width=800,
            height=800
        )
        
        return fig
    except Exception as e:
        print(f"⚠️  分析方面相关性失败: {e}")
        return None

def analyze_facility_comparison(df: pd.DataFrame) -> Optional[go.Figure]:
    """分析不同设施类型的对比"""
    try:
        if 'facility_type' not in df.columns or 'csi_score' not in df.columns:
            return None
        
        # 计算每个设施类型的统计数据
        facility_stats = df.groupby('facility_type').agg(
            avg_csi=('csi_score', 'mean'),
            std_csi=('csi_score', 'std'),
            count=('csi_score', 'count'),
            positive_rate=('polarity_label', lambda x: (x == '积极').mean() * 100),
            negative_rate=('polarity_label', lambda x: (x == '消极').mean() * 100)
        ).reset_index()
        
        # 创建雷达图
        categories = ['平均满意度', '满意度标准差', '样本量', '积极情绪占比', '消极情绪占比']
        
        fig = go.Figure()
        
        for i, row in facility_stats.iterrows():
            # 标准化数据
            values = [
                row['avg_csi'],
                row['std_csi'],
                row['count'] / facility_stats['count'].max() * 100,  # 标准化样本量
                row['positive_rate'],
                row['negative_rate']
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=row['facility_type']
            ))
        
        # 更新布局
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title='设施类型综合对比分析',
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    except Exception as e:
        print(f"⚠️  分析设施对比失败: {e}")
        return None

def analyze_sentiment_distribution_by_source(df: pd.DataFrame) -> Optional[go.Figure]:
    """分析不同来源的情感分布"""
    try:
        if 'source' not in df.columns or 'polarity_label' not in df.columns:
            return None
        
        # 计算每个来源的情感分布
        source_sentiment = df.groupby(['source', 'polarity_label']).size().reset_index(name='count')
        total_by_source = source_sentiment.groupby('source')['count'].transform('sum')
        source_sentiment['percentage'] = (source_sentiment['count'] / total_by_source * 100).round(1)
        
        # 创建堆叠柱状图
        fig = px.bar(
            source_sentiment,
            x='source',
            y='percentage',
            color='polarity_label',
            barmode='stack',
            title='不同来源的情感分布',
            labels={'percentage': '占比 (%)', 'source': '来源', 'polarity_label': '情感倾向'},
            color_discrete_map={'积极': '#4CAF50', '中性': '#FF9800', '消极': '#F44336'}
        )
        
        # 更新布局
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    except Exception as e:
        print(f"⚠️  分析来源情感分布失败: {e}")
        return None

if __name__ == "__main__":
    # 测试
    df = pd.DataFrame({
        'content': [f"评论{i}" for i in range(100)],
        'polarity_label': ['积极'] * 50 + ['中性'] * 30 + ['消极'] * 20,
        'csi_score': np.random.normal(75, 15, 100).tolist(),
        'facility_type': ['广州图书馆'] * 40 + ['国家博物馆'] * 30 + ['北京地铁'] * 30,
        'aspect': ['环境'] * 30 + ['服务态度'] * 30 + ['设施'] * 20 + ['其他'] * 20,
        'source': ['知乎'] * 40 + ['微博'] * 30 + ['贴吧'] * 20 + ['虎扑'] * 10,
        'date': pd.date_range(start='2024-01-01', periods=100, freq='D')
    })
    
    # 测试情感趋势分析
    trend_fig = analyze_sentiment_trends(df)
    if trend_fig:
        trend_fig.show()
    
    # 测试方面相关性分析
    correlation_fig = analyze_aspect_correlation(df)
    if correlation_fig:
        correlation_fig.show()
    
    # 测试设施对比分析
    facility_fig = analyze_facility_comparison(df)
    if facility_fig:
        facility_fig.show()
    
    # 测试来源情感分布分析
    source_fig = analyze_sentiment_distribution_by_source(df)
    if source_fig:
        source_fig.show()
