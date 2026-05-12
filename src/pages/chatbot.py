# -*- coding: utf-8 -*-
"""
智能决策助手页面模块：基于RAG的智能问答系统
使用 rag_retriever.py 的 RAGRetriever 类进行检索增强
"""
import os
import pandas as pd
import streamlit as st

from src.analysis.sentiment_analysis import call_deepseek_api
from src.utils.rag_retriever import RAGRetriever
from src.utils.error_handler import safe_execute


def _rag_search(df: pd.DataFrame, prompt: str, top_n: int = 20) -> pd.DataFrame:
    """RAG智能检索：使用 RAGRetriever 进行 TF-IDF 相似度检索

    Args:
        df: 分析结果数据框
        prompt: 用户输入的问题
        top_n: 返回的最大结果数，默认20

    Returns:
        pd.DataFrame: 检索结果，按相似度降序排列
    """
    context_fields = []
    if 'content' in df.columns:
        context_fields.append('content')
    for col in ['polarity_label', 'facility_type', 'csi_score', 'aspect']:
        if col in df.columns:
            context_fields.append(col)

    retriever = RAGRetriever(context_fields=context_fields)
    documents = df.where(df.notna(), None).to_dict(orient='records')
    retriever.build_index(documents)

    results = retriever.search(prompt, top_k=top_n, min_score=0.0)

    if not results:
        return df.head(top_n)

    matched_indices = []
    for r in results:
        for idx, row in df.iterrows():
            if row.get('content') == r.get('content') and idx not in matched_indices:
                matched_indices.append(idx)
                break

    if not matched_indices:
        return df.head(top_n)

    return df.loc[matched_indices]


def _build_context_text(ctx: pd.DataFrame) -> str:
    """构建RAG上下文文本，包含评论内容、情感标签、设施类型、CSI分数

    Args:
        ctx: 检索到的相关评论数据框

    Returns:
        str: 格式化的上下文文本
    """
    lines = []
    for _, row in ctx.iterrows():
        parts = [f"评论: {row['content']}"]
        if 'polarity_label' in ctx.columns and pd.notna(row.get('polarity_label')):
            parts.append(f"情感: {row['polarity_label']}")
        if 'facility_type' in ctx.columns and pd.notna(row.get('facility_type')):
            parts.append(f"设施: {row['facility_type']}")
        if 'csi_score' in ctx.columns and pd.notna(row.get('csi_score')):
            parts.append(f"CSI: {row['csi_score']:.1f}")
        if 'aspect' in ctx.columns and pd.notna(row.get('aspect')):
            parts.append(f"方面: {row['aspect']}")
        lines.append(" | ".join(parts))
    return "\n".join([f"- {line}" for line in lines])


@safe_execute(default_return=None, user_message="智能问答加载出错，请稍后重试")
def page_chatbot(load_analyzed_df):
    """智能决策助手页面：基于RAG的智能问答系统

    Args:
        load_analyzed_df: 加载分析数据的函数
    """
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🤖 智能决策助手 (RAG)")
    with col2:
        if st.button("🔄 清除聊天记录"):
            if "messages" in st.session_state:
                del st.session_state.messages
            st.rerun()

    df = load_analyzed_df()
    if df is None:
        st.error("⚠️ 请先在【数据管理中心】运行分析！")
        return

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
                    ctx = _rag_search(df, prompt, top_n=20)
                    txt_context = _build_context_text(ctx)

                    sys_msg = "你是城市数据分析师。根据给定的【评论数据】回答用户问题。如果数据中没有答案，请根据常识推断并说明。"
                    user_msg = f"【评论数据片段】:\n{txt_context}\n\n【用户问题】: {prompt}"

                    res = call_deepseek_api([
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": user_msg}
                    ])

                    if not res or "content" not in res:
                        raise RuntimeError("AI 服务调用失败，请检查 API 配置或余额")
                    ans = res["content"]
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})

                    with st.expander("📊 查看 AI 参考的数据源"):
                        display_cols = ['content']
                        for col in ['polarity_label', 'facility_type', 'csi_score', 'aspect']:
                            if col in df.columns:
                                display_cols.append(col)
                        st.dataframe(ctx[display_cols])

                except Exception as e:
                    err_msg = f"系统处理出错: {e}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})
