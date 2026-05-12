# -*- coding: utf-8 -*-
"""
可视化仪表盘模块
生成各种数据可视化图表
"""
import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def generate_visualizations(df: pd.DataFrame, report_df: pd.DataFrame, aspect_df: pd.DataFrame, out_dir: str) -> List[str]:
    """生成各种可视化图表"""
    print("🎨 生成可视化图表...")
    
    # 确保输出目录存在
    os.makedirs(out_dir, exist_ok=True)
    
    generated_files = []
    
    # 1. 情感分布饼图
    if 'polarity_label' in df.columns:
        pie_path = plot_sentiment_distribution(df, out_dir)
        if pie_path:
            generated_files.append(pie_path)
    
    # 2. 满意度得分分布图
    if 'csi_score' in df.columns:
        hist_path = plot_csi_distribution(df, out_dir)
        if hist_path:
            generated_files.append(hist_path)
    
    # 3. 各方面满意度对比图
    if not aspect_df.empty:
        aspect_path = plot_aspect_comparison(aspect_df, out_dir)
        if aspect_path:
            generated_files.append(aspect_path)
    
    # 4. 各设施类型满意度对比
    if 'facility_type' in df.columns and 'csi_score' in df.columns:
        facility_path = plot_facility_comparison(df, out_dir)
        if facility_path:
            generated_files.append(facility_path)
    
    # 5. 紧急度分布图
    if 'urgency_score' in df.columns:
        urgency_path = plot_urgency_distribution(df, out_dir)
        if urgency_path:
            generated_files.append(urgency_path)
    
    # 6. 设施类型-方面热力图
    if 'facility_type' in df.columns and 'aspect' in df.columns and 'csi_score' in df.columns:
        heatmap_path = plot_facility_aspect_heatmap(df, out_dir)
        if heatmap_path:
            generated_files.append(heatmap_path)
    
    # 7. 雷达图 - 各方面综合表现
    if 'aspect' in df.columns and 'csi_score' in df.columns:
        radar_path = plot_radar_chart(df, out_dir)
        if radar_path:
            generated_files.append(radar_path)
    
    # 8. 面积图 - 情感趋势
    if 'csi_score' in df.columns:
        area_path = plot_area_chart(df, out_dir)
        if area_path:
            generated_files.append(area_path)
    
    # 9. 极坐标图 - 设施类型分布
    if 'facility_type' in df.columns and 'csi_score' in df.columns:
        polar_path = plot_polar_chart(df, out_dir)
        if polar_path:
            generated_files.append(polar_path)
    
    # 10. 漏斗图 - 情感漏斗
    if 'polarity_label' in df.columns:
        funnel_path = plot_funnel_chart(df, out_dir)
        if funnel_path:
            generated_files.append(funnel_path)
    
    # 11. 散点图 - 满意度与紧急度关系
    if 'csi_score' in df.columns and 'urgency_score' in df.columns:
        scatter_path = plot_scatter_chart(df, out_dir)
        if scatter_path:
            generated_files.append(scatter_path)
    
    # 12. 小提琴图 - 各设施类型满意度分布
    if 'facility_type' in df.columns and 'csi_score' in df.columns:
        violin_path = plot_violin_chart(df, out_dir)
        if violin_path:
            generated_files.append(violin_path)
    
    # 13. 堆叠柱状图 - 各设施类型情感构成
    if 'facility_type' in df.columns and 'polarity_label' in df.columns:
        stacked_path = plot_stacked_bar_chart(df, out_dir)
        if stacked_path:
            generated_files.append(stacked_path)
    
    # 14. 词云图
    if 'content' in df.columns:
        wordcloud_path = plot_wordcloud(df, out_dir)
        if wordcloud_path:
            generated_files.append(wordcloud_path)
    
    # 15. 3D散点图
    if 'facility_type' in df.columns and 'csi_score' in df.columns and 'urgency_score' in df.columns:
        scatter3d_path = plot_3d_scatter(df, out_dir)
        if scatter3d_path:
            generated_files.append(scatter3d_path)
    
    return generated_files

def plot_sentiment_distribution(df: pd.DataFrame, out_dir: str, filename: str = 'emotion_distribution.png') -> Optional[str]:
    """绘制情感分布饼图"""
    try:
        sentiment_counts = df['polarity_label'].value_counts()
        
        plt.figure(figsize=(10, 6))
        plt.pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%', startangle=90, colors=['#4CAF50', '#FF9800', '#F44336'])
        plt.title('情感分布', fontsize=16)
        plt.axis('equal')  # 确保饼图是圆的
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        print(f"✅ 情感分布饼图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制情感分布饼图失败: {e}")
        return None

def plot_csi_distribution(df: pd.DataFrame, out_dir: str, filename: str = 'sentiment_score_distribution.png') -> Optional[str]:
    """绘制满意度得分分布图"""
    try:
        plt.figure(figsize=(12, 6))
        sns.histplot(df['csi_score'], bins=20, kde=True, color='#3498db')
        plt.title('满意度得分分布', fontsize=16)
        plt.xlabel('CSI满意度指数', fontsize=12)
        plt.ylabel('频率', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        print(f"✅ 满意度得分分布图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制满意度得分分布图失败: {e}")
        return None

def plot_aspect_comparison(aspect_df: pd.DataFrame, out_dir: str, filename: str = 'aspect_avg_scores.png') -> Optional[str]:
    """绘制各方面满意度对比图"""
    try:
        # 按方面分组计算平均满意度
        aspect_avg = aspect_df.groupby('aspect')['avg_csi_score'].mean().sort_values(ascending=False)
        
        plt.figure(figsize=(12, 6))
        aspect_avg.plot(kind='bar', color='#27ae60')
        plt.title('各方面平均满意度', fontsize=16)
        plt.xlabel('方面', fontsize=12)
        plt.ylabel('平均CSI指数', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 各方面满意度对比图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制各方面满意度对比图失败: {e}")
        return None

def plot_facility_comparison(df: pd.DataFrame, out_dir: str, filename: str = 'facility_boxplot.png') -> Optional[str]:
    """绘制各设施类型满意度对比"""
    try:
        plt.figure(figsize=(12, 6))
        sns.boxplot(x='facility_type', y='csi_score', data=df)
        plt.title('各设施类型满意度分布', fontsize=16)
        plt.xlabel('设施类型', fontsize=12)
        plt.ylabel('CSI满意度指数', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 各设施类型满意度对比图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制各设施类型满意度对比图失败: {e}")
        return None

def plot_urgency_distribution(df: pd.DataFrame, out_dir: str, filename: str = 'urgency_distribution.png') -> Optional[str]:
    """绘制紧急度分布图"""
    try:
        urgency_counts = df['urgency_score'].value_counts().sort_index()
        
        plt.figure(figsize=(12, 6))
        urgency_counts.plot(kind='bar', color='#e74c3c')
        plt.title('紧急度分布', fontsize=16)
        plt.xlabel('紧急度', fontsize=12)
        plt.ylabel('数量', fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        print(f"✅ 紧急度分布图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制紧急度分布图失败: {e}")
        return None

def plot_facility_aspect_heatmap(df: pd.DataFrame, out_dir: str, filename: str = 'facility_aspect_heatmap.png') -> Optional[str]:
    """绘制设施类型-方面热力图"""
    try:
        # 计算每个设施类型-方面组合的平均满意度
        heatmap_data = df.groupby(['facility_type', 'aspect'])['csi_score'].mean().unstack()
        
        plt.figure(figsize=(14, 8))
        sns.heatmap(heatmap_data, annot=True, cmap='RdYlGn', center=70, fmt='.1f')
        plt.title('设施类型-方面满意度热力图', fontsize=16)
        plt.xlabel('方面', fontsize=12)
        plt.ylabel('设施类型', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 设施类型-方面热力图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制设施类型-方面热力图失败: {e}")
        return None

def plot_sankey_diagram(df: pd.DataFrame, out_dir: str, filename: str = 'sankey_flow.html') -> Optional[str]:
    """绘制桑基图"""
    try:
        if 'aspect' not in df.columns or 'polarity_label' not in df.columns:
            return None
        
        # 准备桑基图数据
        # 1. 计算方面到情感的流量
        flow_data = df.groupby(['aspect', 'polarity_label']).size().reset_index(name='value')
        
        # 2. 创建节点和链接
        labels = list(set(flow_data['aspect'].tolist() + flow_data['polarity_label'].tolist()))
        label_dict = {label: i for i, label in enumerate(labels)}
        
        source = [label_dict[aspect] for aspect in flow_data['aspect']]
        target = [label_dict[pol] for pol in flow_data['polarity_label']]
        value = flow_data['value'].tolist()
        
        # 3. 创建桑基图
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels
            ),
            link=dict(
                source=source,
                target=target,
                value=value
            )
        )])
        
        fig.update_layout(title_text="方面-情感流向图", font_size=10)
        
        output_path = os.path.join(out_dir, filename)
        fig.write_html(output_path)
        
        print(f"✅ 桑基图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制桑基图失败: {e}")
        return None

def plot_radar_chart(df: pd.DataFrame, out_dir: str, filename: str = 'radar_chart.png') -> Optional[str]:
    """绘制雷达图 - 各方面综合表现"""
    try:
        aspect_avg = df.groupby('aspect')['csi_score'].mean()
        aspects = aspect_avg.index.tolist()
        scores = aspect_avg.values.tolist()
        
        if len(aspects) < 3:
            return None
        
        angles = [n / float(len(aspects)) * 2 * 3.14159 for n in range(len(aspects))]
        angles += angles[:1]
        scores += scores[:1]
        aspects += aspects[:1]
        
        plt.figure(figsize=(10, 10))
        ax = plt.subplot(111, polar=True)
        ax.plot(angles, scores, 'o-', linewidth=2, label='各方面满意度')
        ax.fill(angles, scores, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(aspects[:-1])
        ax.set_ylim(0, 100)
        ax.set_title('各方面满意度综合雷达图', fontsize=16, pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 雷达图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制雷达图失败: {e}")
        return None

def plot_area_chart(df: pd.DataFrame, out_dir: str, filename: str = 'area_chart.png') -> Optional[str]:
    """绘制面积图 - 满意度趋势"""
    try:
        df_sorted = df.sort_values('csi_score').reset_index(drop=True)
        df_sorted['index'] = range(len(df_sorted))
        
        plt.figure(figsize=(14, 6))
        plt.fill_between(df_sorted['index'], df_sorted['csi_score'], alpha=0.4, color='#3498db')
        plt.plot(df_sorted['index'], df_sorted['csi_score'], color='#2980b9', linewidth=2)
        plt.title('满意度分布趋势面积图', fontsize=16)
        plt.xlabel('样本序号（按满意度排序）', fontsize=12)
        plt.ylabel('CSI满意度指数', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 100)
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 面积图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制面积图失败: {e}")
        return None

def plot_polar_chart(df: pd.DataFrame, out_dir: str, filename: str = 'polar_chart.png') -> Optional[str]:
    """绘制极坐标图 - 设施类型分布"""
    try:
        facility_stats = df.groupby('facility_type').agg({
            'csi_score': 'mean',
            'content': 'count'
        }).reset_index()
        facility_stats.columns = ['facility_type', 'avg_csi', 'count']
        
        if len(facility_stats) < 2:
            return None
        
        angles = [n / float(len(facility_stats)) * 2 * 3.14159 for n in range(len(facility_stats))]
        
        plt.figure(figsize=(12, 12))
        ax = plt.subplot(111, polar=True)
        
        bar_width = 2 * 3.14159 / len(facility_stats)
        bars = ax.bar(angles, facility_stats['avg_csi'], width=bar_width, alpha=0.7, 
                     color=plt.cm.viridis(facility_stats['count'] / max(facility_stats['count'])))
        
        ax.set_xticks(angles)
        ax.set_xticklabels(facility_stats['facility_type'])
        ax.set_ylim(0, 100)
        ax.set_title('各设施类型满意度极坐标图', fontsize=16, pad=20)
        
        sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=min(facility_stats['count']), vmax=max(facility_stats['count'])))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', pad=0.1)
        cbar.set_label('评论数量', fontsize=12)
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 极坐标图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制极坐标图失败: {e}")
        return None

def plot_funnel_chart(df: pd.DataFrame, out_dir: str, filename: str = 'funnel_chart.png') -> Optional[str]:
    """绘制漏斗图 - 情感漏斗"""
    try:
        sentiment_order = ['积极', '中性', '消极']
        sentiment_counts = df['polarity_label'].value_counts()
        
        counts = []
        labels = []
        for sentiment in sentiment_order:
            if sentiment in sentiment_counts:
                counts.append(sentiment_counts[sentiment])
                labels.append(sentiment)
        
        if len(counts) < 2:
            return None
        
        colors = ['#4CAF50', '#FF9800', '#F44336']
        
        plt.figure(figsize=(12, 8))
        y_pos = range(len(counts), 0, -1)
        width_scales = [1.0, 0.7, 0.4]
        
        for i, (count, label, color, width) in enumerate(zip(counts, labels, colors, width_scales)):
            plt.barh(y_pos[i], count, height=0.6, color=color, alpha=0.8, label=f'{label}: {count}条')
            plt.text(count/2, y_pos[i], f'{label}\n{count}条', ha='center', va='center', 
                    fontsize=12, color='white', fontweight='bold')
        
        plt.yticks(y_pos, labels)
        plt.xlabel('评论数量', fontsize=12)
        plt.title('情感分布漏斗图', fontsize=16)
        plt.legend()
        plt.grid(True, alpha=0.3, axis='x')
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 漏斗图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制漏斗图失败: {e}")
        return None

def plot_scatter_chart(df: pd.DataFrame, out_dir: str, filename: str = 'scatter_chart.png') -> Optional[str]:
    """绘制散点图 - 满意度与紧急度关系"""
    try:
        plt.figure(figsize=(12, 8))
        
        scatter = plt.scatter(df['csi_score'], df['urgency_score'], 
                             alpha=0.6, s=100, c=df['csi_score'], 
                             cmap='RdYlGn', edgecolors='black', linewidth=0.5)
        
        plt.colorbar(scatter, label='CSI满意度指数')
        plt.title('满意度与紧急度关系散点图', fontsize=16)
        plt.xlabel('CSI满意度指数', fontsize=12)
        plt.ylabel('紧急度', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xlim(0, 100)
        plt.ylim(0, max(df['urgency_score']) + 1 if not df['urgency_score'].empty else 10)
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 散点图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制散点图失败: {e}")
        return None

def plot_violin_chart(df: pd.DataFrame, out_dir: str, filename: str = 'violin_chart.png') -> Optional[str]:
    """绘制小提琴图 - 各设施类型满意度分布"""
    try:
        plt.figure(figsize=(14, 8))
        sns.violinplot(x='facility_type', y='csi_score', data=df, inner='box', palette='Set2')
        plt.title('各设施类型满意度分布小提琴图', fontsize=16)
        plt.xlabel('设施类型', fontsize=12)
        plt.ylabel('CSI满意度指数', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        plt.ylim(0, 100)
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 小提琴图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制小提琴图失败: {e}")
        return None

def plot_stacked_bar_chart(df: pd.DataFrame, out_dir: str, filename: str = 'stacked_bar_chart.png') -> Optional[str]:
    """绘制堆叠柱状图 - 各设施类型情感构成"""
    try:
        crosstab = pd.crosstab(df['facility_type'], df['polarity_label'])
        
        colors = ['#4CAF50', '#FF9800', '#F44336']
        sentiment_order = ['积极', '中性', '消极']
        
        fig, ax = plt.subplots(figsize=(14, 8))
        bottom = pd.Series([0] * len(crosstab), index=crosstab.index)
        
        for i, sentiment in enumerate(sentiment_order):
            if sentiment in crosstab.columns:
                ax.bar(crosstab.index, crosstab[sentiment], bottom=bottom, 
                      label=sentiment, color=colors[i], alpha=0.8)
                bottom += crosstab[sentiment]
        
        ax.set_title('各设施类型情感构成堆叠柱状图', fontsize=16)
        ax.set_xlabel('设施类型', fontsize=12)
        ax.set_ylabel('评论数量', fontsize=12)
        ax.legend(title='情感倾向')
        ax.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 堆叠柱状图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制堆叠柱状图失败: {e}")
        return None

def plot_wordcloud(df: pd.DataFrame, out_dir: str, filename: str = 'wordcloud.png') -> Optional[str]:
    """绘制词云图"""
    try:
        from wordcloud import WordCloud
        import jieba
        
        text = ' '.join(df['content'].astype(str).tolist())
        try:
            words = jieba.cut(text)
        except:
            words = list(text)
        words = [w for w in words if len(w) > 1]
        text_clean = ' '.join(words)
        
        if not text_clean.strip():
            text_clean = text
        
        try:
            wordcloud = WordCloud(
                font_path='C:/Windows/Fonts/simhei.ttf',
                width=800,
                height=600,
                background_color='white',
                max_words=100,
                colormap='viridis'
            ).generate(text_clean)
        except:
            wordcloud = WordCloud(
                width=800,
                height=600,
                background_color='white',
                max_words=100,
                colormap='viridis'
            ).generate(text_clean)
        
        plt.figure(figsize=(12, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('评论关键词词云图', fontsize=16, pad=20)
        
        output_path = os.path.join(out_dir, filename)
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 词云图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制词云图失败: {e}")
        return None

def plot_3d_scatter(df: pd.DataFrame, out_dir: str, filename: str = '3d_scatter.html') -> Optional[str]:
    """绘制3D散点图（使用Plotly）"""
    try:
        fig = go.Figure(data=[go.Scatter3d(
            x=df['csi_score'],
            y=df['urgency_score'],
            z=df.groupby('facility_type').ngroup(),
            mode='markers',
            marker=dict(
                size=8,
                color=df['csi_score'],
                colorscale='RdYlGn',
                opacity=0.8,
                colorbar=dict(title='CSI满意度')
            ),
            text=df.apply(lambda row: f"设施: {row['facility_type']}<br>满意度: {row['csi_score']}<br>紧急度: {row['urgency_score']}", axis=1),
            hoverinfo='text'
        )])
        
        fig.update_layout(
            title='满意度-紧急度-设施类型3D散点图',
            scene=dict(
                xaxis_title='CSI满意度',
                yaxis_title='紧急度',
                zaxis_title='设施类型编号',
                camera=dict(
                    up=dict(x=0, y=0, z=1),
                    center=dict(x=0, y=0, z=0),
                    eye=dict(x=1.5, y=1.5, z=0.5)
                )
            ),
            height=600
        )
        
        output_path = os.path.join(out_dir, filename)
        fig.write_html(output_path)
        
        print(f"✅ 3D散点图已保存: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  绘制3D散点图失败: {e}")
        return None

if __name__ == "__main__":
    # 测试
    df = pd.DataFrame({
        'content': [f"评论{i}" for i in range(50)],
        'polarity_label': ['积极'] * 25 + ['中性'] * 15 + ['消极'] * 10,
        'csi_score': [85, 90, 75, 80, 95] * 10,
        'facility_type': ['广州图书馆'] * 20 + ['国家博物馆'] * 15 + ['北京地铁'] * 15,
        'aspect': ['环境'] * 15 + ['服务态度'] * 15 + ['设施'] * 10 + ['其他'] * 10,
        'urgency_score': [0, 1, 2, 3, 4] * 10
    })
    
    report_df = pd.DataFrame({
        'facility_type': ['广州图书馆', '国家博物馆', '北京地铁'],
        'total_comments': [20, 15, 15],
        'positive_count': [15, 10, 5],
        'negative_count': [2, 3, 7],
        'neutral_count': [3, 2, 3],
        'positive_rate': [75, 66.7, 33.3],
        'negative_rate': [10, 20, 46.7],
        'avg_csi_score': [85, 80, 65],
        'avg_urgency_score': [1, 1.5, 2.5]
    })
    
    aspect_df = pd.DataFrame({
        'facility_type': ['广州图书馆', '广州图书馆', '国家博物馆', '国家博物馆', '北京地铁', '北京地铁'],
        'aspect': ['环境', '服务态度', '环境', '设施', '服务态度', '设施'],
        'count': [10, 10, 8, 7, 8, 7],
        'positive_count': [8, 9, 6, 4, 3, 2],
        'negative_count': [1, 0, 1, 2, 3, 4],
        'positive_rate': [80, 90, 75, 57.1, 37.5, 28.6],
        'negative_rate': [10, 0, 12.5, 28.6, 37.5, 57.1],
        'avg_csi_score': [90, 95, 85, 75, 65, 60]
    })
    
    out_dir = 'test_visualization'
    generated_files = generate_visualizations(df, report_df, aspect_df, out_dir)
    print(f"生成的图表文件: {generated_files}")
