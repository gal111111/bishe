# -*- coding: utf-8 -*-
"""
舆情传播分析模块
用于分析舆情传播路径、影响力节点和扩散预测
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class InfluenceNode:
    """影响力节点"""
    
    def __init__(self, node_id: str, name: str, node_type: str = "user"):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self.in_degree = 0
        self.out_degree = 0
        self.betweenness = 0.0
        self.pagerank = 0.0
        self.sentiment_score = 0.0
        self.posts = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "type": self.node_type,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "betweenness": self.betweenness,
            "pagerank": self.pagerank,
            "sentiment_score": self.sentiment_score,
            "post_count": len(self.posts)
        }

class PropagationEdge:
    """传播边"""
    
    def __init__(self, source: str, target: str, weight: float = 1.0, edge_type: str = "retweet"):
        self.source = source
        self.target = target
        self.weight = weight
        self.edge_type = edge_type
        self.timestamp = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "type": self.edge_type,
            "timestamp": self.timestamp
        }

class PublicOpinionAnalyzer:
    """舆情传播分析器"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.propagation_paths = []
        self.time_series_data = []
    
    def add_post(self, post_id: str, author: str, content: str, 
                  timestamp: Optional[str] = None, 
                  platform: str = "unknown",
                  sentiment: str = "neutral",
                  replies_to: Optional[str] = None,
                  reposts_of: Optional[str] = None):
        """
        添加一条帖子/评论
        
        参数:
            post_id: 帖子ID
            author: 作者
            content: 内容
            timestamp: 时间戳
            platform: 平台
            sentiment: 情感倾向
            replies_to: 回复的帖子ID
            reposts_of: 转发的帖子ID
        """
        if author not in self.nodes:
            self.nodes[author] = InfluenceNode(author, author)
        
        node = self.nodes[author]
        node.posts.append({
            "post_id": post_id,
            "content": content,
            "timestamp": timestamp,
            "platform": platform,
            "sentiment": sentiment
        })
        
        if sentiment == "positive":
            node.sentiment_score += 1
        elif sentiment == "negative":
            node.sentiment_score -= 1
        
        if replies_to:
            self.edges.append(PropagationEdge(replies_to, author, 1.0, "reply"))
            node.in_degree += 1
        elif reposts_of:
            self.edges.append(PropagationEdge(reposts_of, author, 1.5, "repost"))
            node.in_degree += 1
    
    def build_from_dataframe(self, df, 
                             content_col: str = "content",
                             author_col: str = "user",
                             time_col: str = "create_time",
                             platform_col: str = "platform",
                             sentiment_col: str = "polarity_label",
                             id_col: str = None):
        """
        从DataFrame构建传播网络
        
        参数:
            df: 数据DataFrame
            content_col: 内容列名
            author_col: 作者列名
            time_col: 时间列名
            platform_col: 平台列名
            sentiment_col: 情感列名
            id_col: ID列名
        """
        for idx, row in df.iterrows():
            post_id = str(row.get(id_col, idx)) if id_col else str(idx)
            author = str(row.get(author_col, f"user_{idx}"))
            content = str(row.get(content_col, ""))
            timestamp = row.get(time_col, None)
            platform = str(row.get(platform_col, "unknown"))
            sentiment = str(row.get(sentiment_col, "neutral"))
            
            self.add_post(
                post_id=post_id,
                author=author,
                content=content,
                timestamp=timestamp,
                platform=platform,
                sentiment=sentiment
            )
    
    def calculate_pagerank(self, damping_factor: float = 0.85, max_iterations: int = 100, tol: float = 1e-6):
        """
        计算PageRank
        
        参数:
            damping_factor: 阻尼系数
            max_iterations: 最大迭代次数
            tol: 收敛阈值
        """
        if not self.nodes:
            return
        
        n = len(self.nodes)
        node_ids = list(self.nodes.keys())
        node_index = {node_id: i for i, node_id in enumerate(node_ids)}
        
        pagerank = np.ones(n) / n
        
        for iteration in range(max_iterations):
            new_pagerank = np.ones(n) * (1 - damping_factor) / n
            
            for edge in self.edges:
                source_idx = node_index.get(edge.source, -1)
                target_idx = node_index.get(edge.target, -1)
                
                if source_idx != -1 and target_idx != -1:
                    source_node = self.nodes[edge.source]
                    if source_node.out_degree > 0:
                        new_pagerank[target_idx] += damping_factor * pagerank[source_idx] / source_node.out_degree
            
            delta = np.sum(np.abs(new_pagerank - pagerank))
            pagerank = new_pagerank
            
            if delta < tol:
                break
        
        for i, node_id in enumerate(node_ids):
            self.nodes[node_id].pagerank = pagerank[i]
    
    def find_influential_nodes(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        找到有影响力的节点
        
        参数:
            top_k: 返回前k个节点
            
        返回:
            有影响力节点列表
        """
        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda x: (x.pagerank, x.in_degree, -x.sentiment_score),
            reverse=True
        )
        
        return [node.to_dict() for node in sorted_nodes[:top_k]]
    
    def detect_propagation_path(self, start_node: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        检测传播路径
        
        参数:
            start_node: 起始节点
            max_depth: 最大深度
            
        返回:
            传播路径列表
        """
        paths = []
        
        def dfs(current_node: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            path.append(current_node)
            paths.append(path.copy())
            
            for edge in self.edges:
                if edge.source == current_node and edge.target not in path:
                    dfs(edge.target, path, depth + 1)
            
            path.pop()
        
        dfs(start_node, [], 0)
        return paths
    
    def analyze_time_series(self, time_window: str = "D") -> Dict[str, Any]:
        """
        时间序列分析
        
        参数:
            time_window: 时间窗口 ('D'=天, 'H'=小时, 'W'=周)
            
        返回:
            时间序列分析结果
        """
        time_data = defaultdict(lambda: {"count": 0, "positive": 0, "negative": 0, "neutral": 0})
        
        for node in self.nodes.values():
            for post in node.posts:
                timestamp = post.get("timestamp")
                sentiment = post.get("sentiment", "neutral")
                
                if timestamp:
                    try:
                        if isinstance(timestamp, str):
                            dt = pd.to_datetime(timestamp)
                        else:
                            dt = timestamp
                        
                        time_key = dt.floor(time_window).strftime("%Y-%m-%d")
                        
                        time_data[time_key]["count"] += 1
                        if sentiment == "positive" or sentiment == "积极":
                            time_data[time_key]["positive"] += 1
                        elif sentiment == "negative" or sentiment == "消极":
                            time_data[time_key]["negative"] += 1
                        else:
                            time_data[time_key]["neutral"] += 1
                    except:
                        pass
        
        sorted_times = sorted(time_data.keys())
        
        return {
            "time_points": sorted_times,
            "data": {
                time: time_data[time] for time in sorted_times
            }
        }
    
    def get_network_data(self) -> Dict[str, Any]:
        """
        获取网络数据（用于可视化）
        
        返回:
            包含nodes和edges的字典
        """
        nodes_data = [node.to_dict() for node in self.nodes.values()]
        
        edges_data = []
        for edge in self.edges:
            edges_data.append(edge.to_dict())
        
        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "stats": {
                "total_nodes": len(nodes_data),
                "total_edges": len(edges_data),
                "avg_degree": np.mean([n.in_degree + n.out_degree for n in self.nodes.values()]) if self.nodes else 0
            }
        }
    
    def get_insights(self) -> Dict[str, Any]:
        """
        获取传播分析洞察
        
        返回:
            洞察字典
        """
        if not self.nodes:
            return {"message": "网络为空，暂无洞察"}
        
        # 最有影响力的节点
        top_influencers = self.find_influential_nodes(top_k=10)
        
        # 情感分布
        sentiment_counts = Counter()
        for node in self.nodes.values():
            for post in node.posts:
                sentiment = post.get("sentiment", "neutral")
                sentiment_counts[sentiment] += 1
        
        # 时间序列
        time_series = self.analyze_time_series()
        
        return {
            "top_influencers": top_influencers,
            "sentiment_distribution": dict(sentiment_counts),
            "time_series": time_series,
            "network_stats": self.get_network_data()["stats"]
        }
    
    def save_analysis(self, output_path: str):
        """
        保存分析结果
        
        参数:
            output_path: 输出文件路径
        """
        analysis_data = {
            "network": self.get_network_data(),
            "insights": self.get_insights()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 舆情传播分析已保存到: {output_path}")

if __name__ == "__main__":
    print("=" * 80)
    print("测试舆情传播分析模块")
    print("=" * 80)
    
    analyzer = PublicOpinionAnalyzer()
    
    # 模拟一些数据
    test_data = [
        {"post_id": "1", "author": "user_a", "content": "迪士尼真好玩！", "sentiment": "positive"},
        {"post_id": "2", "author": "user_b", "content": "人太多了，排队好烦", "sentiment": "negative"},
        {"post_id": "3", "author": "user_c", "content": "回复user_a: 我也觉得！", "sentiment": "positive", "replies_to": "user_a"},
        {"post_id": "4", "author": "user_d", "content": "转发user_a: 同感", "sentiment": "positive", "reposts_of": "user_a"},
        {"post_id": "5", "author": "user_e", "content": "服务态度很好", "sentiment": "positive"},
    ]
    
    for data in test_data:
        analyzer.add_post(**data)
    
    # 计算PageRank
    analyzer.calculate_pagerank()
    
    print("\n" + "=" * 80)
    print("Top 5 影响力节点:")
    print("=" * 80)
    top_nodes = analyzer.find_influential_nodes(top_k=5)
    for i, node in enumerate(top_nodes, 1):
        print(f"{i}. {node['name']} - PageRank: {node['pagerank']:.4f}, 入度: {node['in_degree']}")
    
    print("\n" + "=" * 80)
    print("网络统计:")
    print("=" * 80)
    stats = analyzer.get_network_data()["stats"]
    print(f"总节点数: {stats['total_nodes']}")
    print(f"总边数: {stats['total_edges']}")
    print(f"平均度数: {stats['avg_degree']:.2f}")
    
    # 保存测试
    os.makedirs("test_output", exist_ok=True)
    analyzer.save_analysis("test_output/opinion_propagation.json")
    
    print("\n✅ 测试完成！")