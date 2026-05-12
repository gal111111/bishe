# -*- coding: utf-8 -*-
"""
知识图谱构建模块
用于舆情分析中的实体识别、关系抽取和图谱可视化
"""
import os
import sys
import json
import re
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.utils.deepseek_client import DeepSeekClient
    from src.analysis.sentiment_analysis import call_deepseek_api
except ImportError:
    pass

# 公共设施实体类型定义
ENTITY_TYPES = {
    "设施": ["设施", "设备", "硬件", "建筑", "场馆", "空间", "场地", "图书馆", "博物馆", "公园", "厕所", "电梯"],
    "服务": ["服务", "态度", "效率", "管理", "人员", "工作人员", "馆员", "保安", "保洁"],
    "环境": ["环境", "卫生", "安静", "整洁", "干净", "噪音", "吵闹", "空气", "温度"],
    "位置": ["位置", "交通", "便利", "距离", "远", "近", "方便", "地铁", "公交"],
    "开放": ["时间", "开放", "关门", "预约", "订位", "排队", "等待"],
    "藏书": ["藏书", "书籍", "图书", "资料", "馆藏", "资源"],
    "价格": ["价格", "费用", "收费", "门票", "免费", "贵", "便宜"],
    "安全": ["安全", "保安", "防护", "隐患", "危险", "事故"]
}

# 情感关系定义
RELATION_TYPES = {
    "正面评价": ["好", "很好", "不错", "棒", "满意", "喜欢", "优秀", "出色", "完美", "推荐", "赞"],
    "负面评价": ["差", "糟糕", "很差", "不好", "烂", "失望", "不满", "讨厌", "垃圾", "差劲"],
    "中性提及": ["有", "是", "在", "去", "来", "使用"]
}

class EntityExtractor:
    """实体提取器"""
    
    def __init__(self):
        self.entity_keywords = {}
        for entity_type, keywords in ENTITY_TYPES.items():
            for keyword in keywords:
                self.entity_keywords[keyword] = entity_type
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        从文本中提取实体
        
        参数:
            text: 评论文本
            
        返回:
            实体列表，每个实体包含: text, type
        """
        entities = []
        seen = set()
        
        # 基于关键词匹配提取实体
        for keyword, entity_type in self.entity_keywords.items():
            if keyword in text and keyword not in seen:
                # 找到关键词在文本中的位置
                for match in re.finditer(re.escape(keyword), text):
                    entities.append({
                        "text": keyword,
                        "type": entity_type,
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    })
                    seen.add(keyword)
        
        # 按位置排序
        entities.sort(key=lambda x: x["start_pos"])
        return entities

class RelationExtractor:
    """关系提取器"""
    
    def __init__(self):
        self.relation_keywords = {}
        for relation_type, keywords in RELATION_TYPES.items():
            for keyword in keywords:
                self.relation_keywords[keyword] = relation_type
    
    def extract_relations(self, text: str, entities: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        提取实体之间的关系
        
        参数:
            text: 评论文本
            entities: 实体列表
            
        返回:
            关系列表，每个关系包含: source, target, type, sentiment
        """
        relations = []
        
        if len(entities) < 1:
            return relations
        
        # 简单的关系提取策略
        # 1. 提取情感词
        sentiment = "中性"
        for keyword, rel_type in self.relation_keywords.items():
            if keyword in text:
                if rel_type == "正面评价":
                    sentiment = "积极"
                elif rel_type == "负面评价":
                    sentiment = "消极"
        
        # 2. 建立实体与情感的关系
        for i, entity in enumerate(entities):
            # 查找该实体附近的情感词
            entity_text = entity["text"]
            entity_start = entity["start_pos"]
            entity_end = entity["end_pos"]
            
            # 窗口范围内查找情感词
            window_size = 30
            window_start = max(0, entity_start - window_size)
            window_end = min(len(text), entity_end + window_size)
            window_text = text[window_start:window_end]
            
            # 判断该实体的情感
            entity_sentiment = "中性"
            for keyword, rel_type in self.relation_keywords.items():
                if keyword in window_text:
                    if rel_type == "正面评价":
                        entity_sentiment = "积极"
                    elif rel_type == "负面评价":
                        entity_sentiment = "消极"
            
            relations.append({
                "source": entity["text"],
                "source_type": entity["type"],
                "target": "评论者",
                "target_type": "用户",
                "type": "评价",
                "sentiment": entity_sentiment,
                "context": window_text
            })
        
        return relations

class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()
        self.entities = []
        self.relations = []
        self.entity_counts = Counter()
        self.relation_counts = Counter()
    
    def add_comment(self, text: str, comment_id: Optional[str] = None):
        """
        添加一条评论到图谱
        
        参数:
            text: 评论文本
            comment_id: 评论ID
        """
        # 提取实体
        entities = self.entity_extractor.extract_entities(text)
        
        # 提取关系
        relations = self.relation_extractor.extract_relations(text, entities)
        
        # 添加到图谱
        for entity in entities:
            entity_key = (entity["text"], entity["type"])
            self.entity_counts[entity_key] += 1
            
            # 去重添加实体
            if not any(e["text"] == entity["text"] and e["type"] == entity["type"] for e in self.entities):
                self.entities.append({
                    "id": f"entity_{len(self.entities)}",
                    "text": entity["text"],
                    "type": entity["type"],
                    "count": 1
                })
            else:
                for e in self.entities:
                    if e["text"] == entity["text"] and e["type"] == entity["type"]:
                        e["count"] = e.get("count", 0) + 1
        
        for relation in relations:
            rel_key = (relation["source"], relation["target"], relation["type"], relation["sentiment"])
            self.relation_counts[rel_key] += 1
            
            self.relations.append({
                "id": f"relation_{len(self.relations)}",
                "source": relation["source"],
                "source_type": relation["source_type"],
                "target": relation["target"],
                "target_type": relation["target_type"],
                "type": relation["type"],
                "sentiment": relation["sentiment"],
                "context": relation["context"],
                "comment_id": comment_id
            })
    
    def build_from_dataframe(self, df, content_col: str = "content", id_col: str = None):
        """
        从DataFrame构建图谱
        
        参数:
            df: 数据DataFrame
            content_col: 内容列名
            id_col: ID列名
        """
        for idx, row in df.iterrows():
            text = str(row.get(content_col, ""))
            comment_id = str(row.get(id_col, idx)) if id_col else str(idx)
            self.add_comment(text, comment_id)
    
    def get_graph_data(self) -> Dict[str, Any]:
        """
        获取图谱数据（用于可视化）
        
        返回:
            包含nodes和edges的字典
        """
        nodes = []
        edges = []
        
        # 添加实体节点
        for entity in self.entities:
            nodes.append({
                "id": entity["id"],
                "label": entity["text"],
                "type": entity["type"],
                "size": min(30, entity.get("count", 1) * 5),
                "count": entity.get("count", 1)
            })
        
        # 添加用户节点
        nodes.append({
            "id": "user_node",
            "label": "评论者",
            "type": "用户",
            "size": 20,
            "count": len(self.relations)
        })
        
        # 添加关系边
        for relation in self.relations:
            # 找到源节点ID
            source_id = None
            for entity in self.entities:
                if entity["text"] == relation["source"] and entity["type"] == relation["source_type"]:
                    source_id = entity["id"]
                    break
            
            if source_id:
                # 确定边的颜色
                color = "#F59E0B"  # 中性-黄色
                if relation["sentiment"] == "积极":
                    color = "#3FB950"  # 积极-绿色
                elif relation["sentiment"] == "消极":
                    color = "#F85149"  # 消极-红色
                
                edges.append({
                    "id": relation["id"],
                    "source": source_id,
                    "target": "user_node",
                    "label": relation["sentiment"],
                    "color": color,
                    "type": relation["type"]
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_entities": len(self.entities),
                "total_relations": len(self.relations),
                "entity_types": dict(Counter(e["type"] for e in self.entities)),
                "sentiment_distribution": dict(Counter(r["sentiment"] for r in self.relations))
            }
        }
    
    def save_graph(self, output_path: str):
        """
        保存图谱到JSON文件
        
        参数:
            output_path: 输出文件路径
        """
        graph_data = self.get_graph_data()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 知识图谱已保存到: {output_path}")
    
    def get_insights(self) -> Dict[str, Any]:
        """
        获取图谱洞察
        
        返回:
            洞察字典
        """
        if not self.entities:
            return {"message": "图谱为空，暂无洞察"}
        
        # 最常提及的实体
        top_entities = sorted(self.entities, key=lambda x: x.get("count", 0), reverse=True)[:10]
        
        # 情感分布
        sentiment_dist = Counter(r["sentiment"] for r in self.relations)
        
        # 实体类型分布
        type_dist = Counter(e["type"] for e in self.entities)
        
        # 负面评价最多的实体
        negative_entities = defaultdict(int)
        for relation in self.relations:
            if relation["sentiment"] == "消极":
                negative_entities[relation["source"]] += 1
        
        top_negative = sorted(negative_entities.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "top_mentioned_entities": [{"text": e["text"], "type": e["type"], "count": e.get("count", 0)} for e in top_entities],
            "sentiment_distribution": dict(sentiment_dist),
            "entity_type_distribution": dict(type_dist),
            "most_criticized_entities": [{"text": k, "count": v} for k, v in top_negative]
        }

if __name__ == "__main__":
    print("=" * 80)
    print("测试知识图谱构建模块")
    print("=" * 80)
    
    builder = KnowledgeGraphBuilder()
    
    # 测试评论
    test_comments = [
        "广州图书馆的环境很好，书籍很全，但是服务态度有点差",
        "这个博物馆的设施很新，但是位置有点偏，交通不太方便",
        "公园的卫生状况糟糕，保安也不管事，太失望了",
        "阅览室很安静，学习氛围不错，就是开放时间太短了"
    ]
    
    for i, comment in enumerate(test_comments):
        print(f"\n添加评论 {i+1}: {comment}")
        builder.add_comment(comment, f"comment_{i}")
    
    print("\n" + "=" * 80)
    print("图谱统计:")
    print("=" * 80)
    
    graph_data = builder.get_graph_data()
    print(f"实体数量: {graph_data['stats']['total_entities']}")
    print(f"关系数量: {graph_data['stats']['total_relations']}")
    print(f"实体类型: {graph_data['stats']['entity_types']}")
    print(f"情感分布: {graph_data['stats']['sentiment_distribution']}")
    
    print("\n" + "=" * 80)
    print("图谱洞察:")
    print("=" * 80)
    
    insights = builder.get_insights()
    print(f"\n最常提及的实体:")
    for entity in insights["top_mentioned_entities"]:
        print(f"  - {entity['text']} ({entity['type']}): {entity['count']}次")
    
    print(f"\n被批评最多的实体:")
    for entity in insights["most_criticized_entities"]:
        print(f"  - {entity['text']}: {entity['count']}次")
    
    # 保存测试
    os.makedirs("test_output", exist_ok=True)
    builder.save_graph("test_output/knowledge_graph.json")
    
    print("\n✅ 测试完成！")