# -*- coding: utf-8 -*-
import os
import sys
import glob
import time
import re
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

st.set_page_config(
    page_title="城市舆情洞察系统",
    layout="wide",
    page_icon="🌟",
    initial_sidebar_state="collapsed"
)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")

from src.analysis.sentiment_analysis import analyze_dataframe, generate_ai_report, call_deepseek_api
from src.visualization.dashboard import generate_visualizations, plot_sankey_diagram
from src.analysis.academic_report import AcademicReportGenerator

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Space Grotesk', 'Noto Sans SC', sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #020617 0%, #0f172a 50%, #020617 100%);
    color: #e2e8f0;
}

.hero-section {
    position: relative;
    min-height: 60vh;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.hero-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        radial-gradient(ellipse at 20% 20%, rgba(59, 130, 246, 0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(236, 72, 153, 0.1) 0%, transparent 60%);
    animation: float 20s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(1deg); }
}

.hero-content {
    position: relative;
    z-index: 10;
    text-align: center;
    padding: 60px 40px;
}

.hero-title {
    font-size: 72px;
    font-weight: 700;
    letter-spacing: -2px;
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 20px;
    animation: glow 3s ease-in-out infinite;
}

@keyframes glow {
    0%, 100% { filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.5)); }
    50% { filter: drop-shadow(0 0 40px rgba(139, 92, 246, 0.8)); }
}

.hero-subtitle {
    font-size: 20px;
    color: rgba(148, 163, 184, 0.9);
    max-width: 600px;
    margin: 0 auto 40px;
    line-height: 1.6;
}

.nav-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    max-width: 900px;
    margin: 0 auto;
}

.nav-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.6) 100%);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 20px;
    padding: 32px 24px;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.nav-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent);
    transition: left 0.5s;
}

.nav-card:hover::before {
    left: 100%;
}

.nav-card:hover {
    transform: translateY(-8px) scale(1.02);
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 20px 60px rgba(59, 130, 246, 0.2);
}

.nav-icon {
    font-size: 48px;
    margin-bottom: 16px;
    display: block;
}

.nav-title {
    font-size: 20px;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 8px;
}

.nav-desc {
    font-size: 13px;
    color: rgba(148, 163, 184, 0.8);
    line-height: 1.5;
}

.section-title {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 8px;
    background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.section-subtitle {
    font-size: 14px;
    color: rgba(148, 163, 184, 0.7);
    margin-bottom: 32px;
}

.modern-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.5) 100%);
    border: 1px solid rgba(59, 130, 246, 0.15);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.modern-card:hover {
    border-color: rgba(59, 130, 246, 0.3);
    transform: translateY(-2px);
}

.stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
    border-radius: 100px;
    font-size: 13px;
    font-weight: 500;
    color: #94a3b8;
}

.chat-container {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.4) 100%);
    border: 1px solid rgba(59, 130, 246, 0.15);
    border-radius: 24px;
    padding: 32px;
    min-height: 500px;
    display: flex;
    flex-direction: column;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    margin-bottom: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.chat-message {
    max-width: 80%;
    padding: 16px 20px;
    border-radius: 16px;
    animation: messageIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes messageIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.chat-message.user {
    align-self: flex-end;
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    color: white;
    border-bottom-right-radius: 4px;
}

.chat-message.assistant {
    align-self: flex-start;
    background: rgba(30, 41, 59, 0.8);
    color: #e2e8f0;
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-bottom-left-radius: 4px;
}

.chat-input-container {
    display: flex;
    gap: 12px;
}

.chat-input {
    flex: 1;
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 16px;
    padding: 16px 20px;
    color: #e2e8f0;
    font-size: 15px;
    transition: all 0.3s ease;
}

.chat-input:focus {
    outline: none;
    border-color: rgba(59, 130, 246, 0.6);
    box-shadow: 0 0 30px rgba(59, 130, 246, 0.2);
}

.send-btn {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    border: none;
    border-radius: 16px;
    padding: 16px 32px;
    color: white;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}

.send-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(59, 130, 246, 0.4);
}

.quick-questions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.quick-question {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 100px;
    padding: 10px 20px;
    font-size: 13px;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.3s ease;
}

.quick-question:hover {
    background: rgba(59, 130, 246, 0.2);
    color: #ffffff;
    border-color: rgba(59, 130, 246, 0.4);
}

.back-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 12px;
    padding: 12px 24px;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
}

.back-btn:hover {
    background: rgba(59, 130, 246, 0.2);
    color: #ffffff;
    border-color: rgba(59, 130, 246, 0.4);
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 32px;
}

.metric-item {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.5) 100%);
    border: 1px solid rgba(59, 130, 246, 0.15);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.metric-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
}

.metric-value {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 8px;
}

.metric-label {
    font-size: 13px;
    color: rgba(148, 163, 184, 0.8);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.progress-bar {
    height: 6px;
    background: rgba(30, 41, 59, 0.8);
    border-radius: 3px;
    overflow: hidden;
    margin-top: 12px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    border-radius: 3px;
    transition: width 1s ease;
}

</style>
""", unsafe_allow_html=True)

def sanitize_filename(filename):
    filename = str(filename)
    filename = re.sub(r'[<>:"/\\\\|?*]', '_', filename)
    filename = filename.strip('. ')
    if not filename:
        filename = 'unnamed_file'
    return filename[:255]

def show_hero():
    st.markdown("""
    <div class="hero-section">
        <div class="hero-bg"></div>
        <div class="hero-content">
            <div class="hero-title">城市舆情洞察</div>
            <div class="hero-subtitle">
                运用先进的人工智能技术，深度分析城市公共设施舆情数据，
                为城市治理提供智能决策支持
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 数据洞察", key="nav_dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        st.markdown("""
        <div style="text-align: center; margin-top: 12px;">
            <div style="font-size: 14px; color: #94a3b8;">查看数据可视化和分析报告</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🤖 智能对话", key="nav_chat", use_container_width=True):
            st.session_state.page = "chat"
            st.rerun()
        st.markdown("""
        <div style="text-align: center; margin-top: 12px;">
            <div style="font-size: 14px; color: #94a3b8;">与AI助手进行自然语言交流</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("📁 数据管理", key="nav_data", use_container_width=True):
            st.session_state.page = "data"
            st.rerun()
        st.markdown("""
        <div style="text-align: center; margin-top: 12px;">
            <div style="font-size: 14px; color: #94a3b8;">上传数据并运行分析引擎</div>
        </div>
        """, unsafe_allow_html=True)

def show_dashboard_page():
    if st.button("← 返回主页", key="back_home"):
        st.session_state.page = "home"
        st.rerun()
    
    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">数据洞察中心</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">实时监控城市公共设施服务质量与市民满意度</div>', unsafe_allow_html=True)
    
    res_path = os.path.join(DATA_DIR, "analyzed_comments.csv")
    if not os.path.exists(res_path):
        st.markdown("""
        <div style="text-align: center; padding: 80px 40px; background: rgba(30, 41, 59, 0.4); border-radius: 24px; border: 1px solid rgba(59, 130, 246, 0.2);">
            <div style="font-size: 64px; margin-bottom: 20px;">📊</div>
            <h3 style="color: #e2e8f0; margin-bottom: 12px;">暂无分析数据</h3>
            <p style="color: rgba(148, 163, 184, 0.8);">请先在【数据管理】中上传并分析数据</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    df = pd.read_csv(res_path)
    
    avg_csi = df['csi_score'].mean() if 'csi_score' in df.columns else 0
    total = len(df)
    urgent = len(df[df.get('urgency_score', 0) >= 7]) if 'urgency_score' in df.columns else 0
    pos_rate = (df['polarity_label'] == '积极').mean() * 100 if 'polarity_label' in df.columns else 0
    
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-item">
            <div class="metric-value" style="color: #3b82f6;">{avg_csi:.1f}</div>
            <div class="metric-label">CSI 满意度</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {avg_csi}%;"></div>
            </div>
        </div>
        <div class="metric-item">
            <div class="metric-value" style="color: #8b5cf6;">{total:,}</div>
            <div class="metric-label">分析样本</div>
        </div>
        <div class="metric-item">
            <div class="metric-value" style="color: #ec4899;">{urgent}</div>
            <div class="metric-label">高危预警</div>
        </div>
        <div class="metric-item">
            <div class="metric-value" style="color: #10b981;">{pos_rate:.1f}%</div>
            <div class="metric-label">正面评价</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {pos_rate}%; background: linear-gradient(90deg, #10b981, #059669);"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📈 趋势分析", "🏢 设施分析", "📝 详细数据"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            if 'polarity_label' in df.columns:
                sentiment_counts = df['polarity_label'].value_counts()
                fig = px.pie(
                    values=sentiment_counts.values,
                    names=sentiment_counts.index,
                    hole=0.4,
                    color_discrete_map={'积极': '#10b981', '中性': '#f59e0b', '消极': '#ef4444'},
                    title='情感倾向分布'
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'csi_score' in df.columns:
                fig = px.histogram(
                    df, x='csi_score', nbins=20,
                    title='CSI满意度分布',
                    color_discrete_sequence=['#3b82f6']
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
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
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.dataframe(df.head(50), use_container_width=True)

def show_chat_page():
    if st.button("← 返回主页", key="back_home_chat"):
        st.session_state.page = "home"
        st.rerun()
    
    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">智能对话助手</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">基于分析数据，与AI进行自然语言交流</div>', unsafe_allow_html=True)
    
    res_path = os.path.join(DATA_DIR, "analyzed_comments.csv")
    if not os.path.exists(res_path):
        st.markdown("""
        <div style="text-align: center; padding: 80px 40px; background: rgba(30, 41, 59, 0.4); border-radius: 24px; border: 1px solid rgba(59, 130, 246, 0.2);">
            <div style="font-size: 64px; margin-bottom: 20px;">🤖</div>
            <h3 style="color: #e2e8f0; margin-bottom: 12px;">需要先分析数据</h3>
            <p style="color: rgba(148, 163, 184, 0.8);">请先在【数据管理】中上传并分析数据</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    df = pd.read_csv(res_path)
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "你好！我是基于当前舆情数据的AI助手。你可以问我任何关于数据分析的问题，比如：\n\n• 哪些设施的满意度最低？\n• 主要的负面评价集中在哪些方面？\n• 有哪些需要紧急关注的问题？"}
        ]
    
    quick_questions = [
        "哪些设施的满意度最低？",
        "主要的负面评价有哪些？",
        "满意度趋势如何？",
        "有哪些紧急问题？"
    ]
    
    st.markdown('<div class="quick-questions">', unsafe_allow_html=True)
    for q in quick_questions:
        if st.button(q, key=f"quick_{q}"):
            st.session_state.chat_messages.append({"role": "user", "content": q})
            process_chat_message(q, df)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
    for msg in st.session_state.chat_messages:
        role_class = "user" if msg["role"] == "user" else "assistant"
        st.markdown(f'<div class="chat-message {role_class}">{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 使用现代聊天输入组件
    user_input = st.chat_input("输入你的问题...", key="chat_input")
    
    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        process_chat_message(user_input, df)
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def process_chat_message(prompt, df):
    with st.spinner("思考中..."):
        try:
            # 提取更丰富的上下文信息
            search_content = df['content'].astype(str) if 'content' in df.columns else pd.Series(['']*len(df))
            
            # 智能选择上下文：优先选择与问题相关的评论
            ctx = df.head(10)
            if len(prompt) >= 3:
                # 提取关键词
                keywords = prompt.split()[:3]
                for keyword in keywords:
                    if len(keyword) >= 2:
                        relevant = df[search_content.str.contains(keyword, na=False, case=False)]
                        if not relevant.empty:
                            ctx = relevant.head(15)
                            break
            
            # 构建上下文文本
            txt_context = "\n".join([f"- {t}" for t in ctx['content'].astype(str).tolist()])
            
            # 生成更详细的统计摘要
            stats_summary = ""
            
            if 'csi_score' in df.columns:
                avg_csi = df['csi_score'].mean()
                max_csi = df['csi_score'].max()
                min_csi = df['csi_score'].min()
                stats_summary += f"平均CSI指数: {avg_csi:.1f}\n"
                stats_summary += f"最高CSI指数: {max_csi:.1f}\n"
                stats_summary += f"最低CSI指数: {min_csi:.1f}\n"
            
            if 'polarity_label' in df.columns:
                pos_count = len(df[df['polarity_label'] == '积极'])
                neg_count = len(df[df['polarity_label'] == '消极'])
                neu_count = len(df[df['polarity_label'] == '中性'])
                total = len(df)
                stats_summary += f"正面评价: {pos_count}条 ({pos_count/total*100:.1f}%)\n"
                stats_summary += f"负面评价: {neg_count}条 ({neg_count/total*100:.1f}%)\n"
                stats_summary += f"中性评价: {neu_count}条 ({neu_count/total*100:.1f}%)\n"
            
            if 'facility_type' in df.columns:
                facility_counts = df['facility_type'].value_counts()
                top_facilities = facility_counts.head(5)
                stats_summary += f"主要设施类型: {', '.join(top_facilities.index.tolist())}\n"
                stats_summary += f"设施类型数量: {len(facility_counts)}种\n"
            
            if 'aspect' in df.columns:
                aspect_counts = df['aspect'].value_counts().head(5)
                stats_summary += f"主要评论方面: {', '.join(aspect_counts.index.tolist())}\n"
            
            if 'urgency_score' in df.columns:
                urgent_count = len(df[df['urgency_score'] >= 7])
                stats_summary += f"高危预警: {urgent_count}条\n"
            
            # 系统提示词优化
            sys_msg = """你是一个专业的城市数据分析师，擅长从大量评论数据中提取有价值的洞察。
            请根据给定的【评论数据摘要】和【统计数据】回答用户问题，要求：
            1. 回答要基于数据，提供具体的数据支持
            2. 使用友好、专业的语气
            3. 回答要结构清晰，重点突出
            4. 使用markdown格式让回答更易读
            5. 如果数据中没有明确答案，请根据常识推断并说明
            6. 提供有针对性的建议和解决方案"""
            
            user_msg = f"""【统计数据摘要】:
{stats_summary}

【评论数据片段】:
{txt_context}

【用户问题】: {prompt}"""
            
            # 调用DeepSeek API
            res = call_deepseek_api([
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}
            ])
            
            if res and "content" in res:
                ans = res["content"]
            else:
                # 增强的智能回复
                ans = generate_enhanced_reply(prompt, df)
            
            st.session_state.chat_messages.append({"role": "assistant", "content": ans})
            
        except Exception as e:
            err_msg = f"抱歉，处理时出错了：{str(e)}"
            st.session_state.chat_messages.append({"role": "assistant", "content": err_msg})

def generate_enhanced_reply(prompt, df):
    prompt_lower = prompt.lower()
    
    # 满意度分析
    if any(keyword in prompt_lower for keyword in ["最低", "最差", "不满意", "满意度", "评分"]):
        if 'facility_type' in df.columns and 'csi_score' in df.columns:
            facility_avg = df.groupby('facility_type')['csi_score'].mean().sort_values()
            if len(facility_avg) >= 3:
                worst = facility_avg.head(3)
                best = facility_avg.tail(3)
                return f"""根据数据分析：

## 满意度最低的设施
1. **{worst.index[0]}** - CSI指数: {worst.iloc[0]:.1f}
2. **{worst.index[1]}** - CSI指数: {worst.iloc[1]:.1f}  
3. **{worst.index[2]}** - CSI指数: {worst.iloc[2]:.1f}

## 满意度最高的设施
1. **{best.index[2]}** - CSI指数: {best.iloc[2]:.1f}
2. **{best.index[1]}** - CSI指数: {best.iloc[1]:.1f}  
3. **{best.index[0]}** - CSI指数: {best.iloc[0]:.1f}

## 改进建议
- 优先关注满意度最低的设施，分析具体问题
- 学习满意度高的设施的成功经验
- 制定针对性的改进计划"""
    
    # 负面评价分析
    if any(keyword in prompt_lower for keyword in ["负面", "问题", "批评", "抱怨"]):
        response = """## 主要问题分析

"""
        
        if 'aspect' in df.columns:
            aspect_counts = df['aspect'].value_counts().head(5)
            response += "### 评论最多的方面\n"
            response += "\n".join([f"• **{aspect}**: {count}条" for aspect, count in aspect_counts.items()])
            response += "\n\n"
        
        if 'urgency_score' in df.columns:
            urgent_count = len(df[df['urgency_score'] >= 7])
            response += f"### 紧急问题\n目前共有 **{urgent_count}** 条高危预警评论（紧急度≥7）\n\n"
        
        if 'polarity_label' in df.columns:
            neg_df = df[df['polarity_label'] == '消极']
            if 'aspect' in neg_df.columns:
                neg_aspects = neg_df['aspect'].value_counts().head(3)
                response += "### 主要负面评论方面\n"
                response += "\n".join([f"• **{aspect}**: {count}条" for aspect, count in neg_aspects.items()])
                response += "\n\n"
        
        response += "## 改进建议\n"
        response += "- 建立问题优先级排序机制\n"
        response += "- 定期跟踪问题解决进度\n"
        response += "- 建立用户反馈闭环系统"
        
        return response
    
    # 紧急问题分析
    if any(keyword in prompt_lower for keyword in ["紧急", "高危", "重要", "严重"]):
        if 'urgency_score' in df.columns:
            urgent_df = df[df['urgency_score'] >= 7]
            urgent_count = len(urgent_df)
            
            response = f"""## 紧急问题分析

### 总体情况
- **高危预警总数**: {urgent_count}条
- **占比**: {urgent_count/len(df)*100:.1f}%  of total comments

"""
            
            if 'aspect' in urgent_df.columns:
                urgent_aspects = urgent_df['aspect'].value_counts().head(3)
                response += "### 主要紧急问题方面\n"
                response += "\n".join([f"• **{aspect}**: {count}条" for aspect, count in urgent_aspects.items()])
                response += "\n\n"
            
            if 'facility_type' in urgent_df.columns:
                urgent_facilities = urgent_df['facility_type'].value_counts().head(3)
                response += "### 问题最严重的设施\n"
                response += "\n".join([f"• **{facility}**: {count}条" for facility, count in urgent_facilities.items()])
                response += "\n\n"
            
            response += "## 应对建议\n"
            response += "- 立即成立专项小组处理紧急问题\n"
            response += "- 24小时内给出问题解决方案\n"
            response += "- 建立紧急问题上报机制\n"
            response += "- 定期回顾紧急问题处理效果"
            
            return response
    
    # 整体趋势分析
    if any(keyword in prompt_lower for keyword in ["趋势", "怎么样", "整体", "概况", "总结"]):
        response = """## 整体数据分析

"""
        
        if 'csi_score' in df.columns:
            avg_csi = df['csi_score'].mean()
            max_csi = df['csi_score'].max()
            min_csi = df['csi_score'].min()
            response += f"### CSI指数分析\n"
            response += f"- **平均指数**: {avg_csi:.1f}/100\n"
            response += f"- **最高指数**: {max_csi:.1f}\n"
            response += f"- **最低指数**: {min_csi:.1f}\n\n"
        
        if 'polarity_label' in df.columns:
            pos_count = len(df[df['polarity_label'] == '积极'])
            neg_count = len(df[df['polarity_label'] == '消极'])
            neu_count = len(df[df['polarity_label'] == '中性'])
            total = len(df)
            response += f"### 情感分析\n"
            response += f"- **正面评价**: {pos_count}条 ({pos_count/total*100:.1f}%)\n"
            response += f"- **负面评价**: {neg_count}条 ({neg_count/total*100:.1f}%)\n"
            response += f"- **中性评价**: {neu_count}条 ({neu_count/total*100:.1f}%)\n\n"
        
        if 'facility_type' in df.columns:
            facility_counts = df['facility_type'].value_counts()
            response += f"### 设施分布\n"
            response += f"- **设施类型数量**: {len(facility_counts)}种\n"
            response += f"- **主要设施**: {', '.join(facility_counts.head(3).index.tolist())}\n\n"
        
        response += "## 整体评估\n"
        if 'csi_score' in df.columns:
            if avg_csi >= 80:
                response += "✅ **优秀**: 整体表现出色，用户满意度高\n"
            elif avg_csi >= 60:
                response += "⚠️ **良好**: 整体表现不错，但仍有改进空间\n"
            else:
                response += "❌ **需要改进**: 整体表现不佳，需要全面优化\n"
        
        return response
    
    # 设施类型分析
    if any(keyword in prompt_lower for keyword in ["设施", "类型", "场所"]):
        if 'facility_type' in df.columns:
            facility_stats = []
            for facility, group in df.groupby('facility_type'):
                stats = {
                    'facility': facility,
                    'count': len(group),
                    'avg_csi': group['csi_score'].mean() if 'csi_score' in group.columns else 50,
                    'pos_rate': (group['polarity_label'] == '积极').mean() * 100 if 'polarity_label' in group.columns else 0
                }
                facility_stats.append(stats)
            
            facility_stats.sort(key=lambda x: x['avg_csi'], reverse=True)
            
            response = """## 设施类型分析

"""
            
            for i, stat in enumerate(facility_stats[:5]):
                response += f"### {i+1}. {stat['facility']}\n"
                response += f"- **评论数**: {stat['count']}条\n"
                response += f"- **平均CSI**: {stat['avg_csi']:.1f}\n"
                response += f"- **正面评价率**: {stat['pos_rate']:.1f}%\n\n"
            
            return response
    
    # 默认回复
    return f"""感谢你的问题！基于当前{len(df):,}条数据分析，我可以为你提供以下方面的洞察：

### 可咨询的问题类型

**📊 数据概览**
- 整体满意度如何？
- 情感倾向分布如何？
- 各设施类型表现如何？

**🔍 问题分析**
- 哪些设施满意度最低？
- 主要的负面评价有哪些？
- 有哪些紧急问题需要关注？

**📈 趋势分析**
- 满意度趋势如何变化？
- 哪些方面需要重点改进？
- 如何提升整体服务质量？

请告诉我你具体想了解哪方面的信息，我会为你提供详细的分析。"""

def show_data_page():
    if st.button("← 返回主页", key="back_home_data"):
        st.session_state.page = "home"
        st.rerun()
    
    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">数据管理中心</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">上传数据文件，启动智能分析引擎</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="modern-card">
            <div style="font-size: 32px; margin-bottom: 12px;">📁</div>
            <h3 style="color: #ffffff; margin-bottom: 8px;">选择数据文件</h3>
            <p style="color: rgba(148, 163, 184, 0.8); font-size: 14px;">
                从已爬取的数据文件中选择一个进行分析
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        raw_files = glob.glob(os.path.join(RAW_DIR, "*_raw_*.csv"))
        
        if raw_files:
            raw_files.sort(key=os.path.getmtime, reverse=True)
            file_options = [os.path.basename(f) for f in raw_files]
            selected_file = st.selectbox("选择文件", file_options)
            
            if selected_file:
                filepath = os.path.join(RAW_DIR, selected_file)
                df = pd.read_csv(filepath, encoding="utf-8-sig", on_bad_lines='skip')
                st.markdown(f"""
                <div style="margin-top: 16px; padding: 16px; background: rgba(30, 41, 59, 0.6); border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #94a3b8;">数据条数</span>
                        <span style="color: #ffffff; font-weight: 600;">{len(df):,}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #94a3b8;">文件大小</span>
                        <span style="color: #ffffff; font-weight: 600;">{os.path.getsize(filepath)/1024:.1f} KB</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🚀 启动智能分析", type="primary", use_container_width=True):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        status_text.text("🔧 正在预处理数据...")
                        from src.analysis.sentiment_analysis import preprocess_data
                        df_clean = preprocess_data(df)
                        progress_bar.progress(0.2)
                        
                        status_text.text("🤖 正在分析情感...")
                        df_res = analyze_dataframe(df_clean, preferred="snownlp", 
                            progress_callback=lambda p: progress_bar.progress(0.2 + p * 0.6))
                        progress_bar.progress(0.8)
                        
                        status_text.text("📊 生成可视化...")
                        df_res.to_csv(os.path.join(DATA_DIR, "analyzed_comments.csv"), 
                            index=False, encoding="utf-8-sig")
                        generate_visualizations(df_res, pd.DataFrame(), pd.DataFrame(), 
                            os.path.join(DATA_DIR, "viz"))
                        progress_bar.progress(0.95)
                        
                        status_text.text("✅ 完成！")
                        progress_bar.progress(1.0)
                        
                        st.session_state.df = df_res
                        st.success("分析完成！点击返回主页查看结果。")
                        time.sleep(2)
                        st.session_state.page = "home"
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"分析出错: {e}")
                        import traceback
                        st.error(traceback.format_exc())
        else:
            st.info("暂无数据文件，请先运行爬虫采集数据。")
    
    with col2:
        st.markdown("""
        <div class="modern-card">
            <div style="font-size: 32px; margin-bottom: 12px;">⚙️</div>
            <h3 style="color: #ffffff; margin-bottom: 8px;">分析说明</h3>
            <p style="color: rgba(148, 163, 184, 0.8); font-size: 14px; line-height: 1.8;">
                • 使用SnowNLP进行快速情感分析<br>
                • 计算CSI满意度指数(0-100)<br>
                • 识别评论方面和具体情绪<br>
                • 评估问题紧急程度(0-10)<br>
                • 生成丰富的可视化图表
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="modern-card">
            <div style="font-size: 32px; margin-bottom: 12px;">📝</div>
            <h3 style="color: #ffffff; margin-bottom: 8px;">数据采集</h3>
            <p style="color: rgba(148, 163, 184, 0.8); font-size: 14px;">
                在终端运行以下命令采集数据：
            </p>
            <div style="margin-top: 12px; padding: 12px; background: rgba(15, 23, 42, 0.8); border-radius: 8px; font-family: monospace; font-size: 13px;">
                python test_auto_crawl.py
            </div>
        </div>
        """, unsafe_allow_html=True)

def main():
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    
    if st.session_state.page == "home":
        show_hero()
    elif st.session_state.page == "dashboard":
        show_dashboard_page()
    elif st.session_state.page == "chat":
        show_chat_page()
    elif st.session_state.page == "data":
        show_data_page()

if __name__ == "__main__":
    main()
