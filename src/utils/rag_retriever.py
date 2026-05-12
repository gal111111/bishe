# -*- coding: utf-8 -*-
"""
RAG检索增强模块
基于jieba分词、多关键词OR匹配、TF-IDF相似度排序和上下文窗口扩展
"""
import os
import sys
import math
import jieba
import functools
from typing import List, Dict, Any, Optional
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

_jieba_initialized = False


def _ensure_jieba():
    global _jieba_initialized
    if not _jieba_initialized:
        jieba.setLogLevel(jieba.logging.INFO)
        _jieba_initialized = True


@functools.lru_cache(maxsize=512)
def tokenize(text: str) -> tuple:
    _ensure_jieba()
    return tuple(jieba.cut_for_search(text))


def _compute_idf(documents: List[List[str]]) -> Dict[str, float]:
    n = len(documents)
    if n == 0:
        return {}
    df = Counter()
    for doc_tokens in documents:
        unique_tokens = set(doc_tokens)
        for token in unique_tokens:
            df[token] += 1
    idf = {}
    for token, freq in df.items():
        idf[token] = math.log((n + 1) / (freq + 1)) + 1
    return idf


def _compute_tf(tokens: List[str]) -> Dict[str, float]:
    total = len(tokens)
    if total == 0:
        return {}
    counts = Counter(tokens)
    return {token: count / total for token, count in counts.items()}


def _tfidf_vector(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    tf = _compute_tf(tokens)
    return {token: tf_val * idf.get(token, 1.0) for token, tf_val in tf.items()}


def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    common_keys = set(vec_a.keys()) & set(vec_b.keys())
    if not common_keys:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class RAGRetriever:
    def __init__(self, context_fields: Optional[List[str]] = None):
        self.documents: List[Dict[str, Any]] = []
        self.doc_tokens: List[List[str]] = []
        self.idf: Dict[str, float] = {}
        self.doc_vectors: List[Dict[str, float]] = []
        self.context_fields = context_fields or ['评论内容', '情感标签', '设施类型', 'CSI分数']

    def build_index(self, documents: List[Dict[str, Any]]):
        self.documents = documents
        self.doc_tokens = []
        for doc in documents:
            combined_text = self._extract_text(doc)
            tokens = list(tokenize(combined_text))
            self.doc_tokens.append(tokens)
        self.idf = _compute_idf(self.doc_tokens)
        self.doc_vectors = [_tfidf_vector(tokens, self.idf) for tokens in self.doc_tokens]

    def search(self, query: str, top_k: int = 5, min_score: float = 0.05) -> List[Dict[str, Any]]:
        if not self.documents:
            return []
        query_tokens = list(tokenize(query))
        query_vector = _tfidf_vector(query_tokens, self.idf)
        keyword_hits = self._keyword_or_match(query_tokens)
        scored = []
        for idx, doc_vector in enumerate(self.doc_vectors):
            tfidf_score = _cosine_similarity(query_vector, doc_vector)
            keyword_boost = 0.3 if idx in keyword_hits else 0.0
            final_score = tfidf_score + keyword_boost
            if final_score >= min_score:
                scored.append((idx, final_score))
        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in scored[:top_k]:
            doc = self._expand_context(idx)
            doc['_rag_score'] = round(score, 4)
            results.append(doc)
        return results

    def _keyword_or_match(self, query_tokens: List[str]) -> set:
        query_set = set(query_tokens)
        hits = set()
        for idx, doc_tokens in enumerate(self.doc_tokens):
            if query_set & set(doc_tokens):
                hits.add(idx)
        return hits

    def _extract_text(self, doc: Dict[str, Any]) -> str:
        parts = []
        for field in self.context_fields:
            value = doc.get(field, '')
            if value is not None:
                parts.append(str(value))
        return ' '.join(parts)

    def _expand_context(self, idx: int) -> Dict[str, Any]:
        doc = dict(self.documents[idx])
        context_parts = []
        for field in self.context_fields:
            value = doc.get(field)
            if value is not None and str(value).strip():
                context_parts.append(f"{field}: {value}")
        doc['_rag_context'] = '\n'.join(context_parts)
        return doc
