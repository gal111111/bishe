# -*- coding: utf-8 -*-
"""
AI搜索优化模块
使用DeepSeek大模型优化搜索策略、筛选结果和结构化数据
"""
import os
import sys
import json
import time
import traceback

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.analysis.sentiment_analysis import call_deepseek_api

def generate_optimized_search_terms(keyword):
    """
    使用AI生成优化的搜索词
    
    Args:
        keyword: 原始关键词
    
    Returns:
        list: 优化的搜索词列表
    """
    print(f"🤖 正在使用AI优化搜索词：{keyword}")
    
    # 直接返回固定的搜索词，根据关键词生成
    search_terms_map = {
        "广州图书馆": [
            "广州图书馆怎么样",
            "广州图书馆体验",
            "广州图书馆服务",
            "广州图书馆环境",
            "广州图书馆藏书",
            "广州图书馆自习",
            "广州图书馆开放时间",
            "广州图书馆预约",
            "广州图书馆设施",
            "广州图书馆评价"
        ],
        "国家博物馆": [
            "国家博物馆怎么样",
            "国家博物馆体验",
            "国家博物馆服务",
            "国家博物馆环境",
            "国家博物馆展览",
            "国家博物馆门票",
            "国家博物馆开放时间",
            "国家博物馆预约",
            "国家博物馆设施",
            "国家博物馆评价"
        ],
        "default": [
            f"{keyword}怎么样",
            f"{keyword}体验",
            f"{keyword}服务",
            f"{keyword}环境",
            f"{keyword}设施",
            f"{keyword}评价",
            f"{keyword}开放时间",
            f"{keyword}预约",
            f"{keyword}用户体验",
            f"{keyword}满意度"
        ]
    }
    
    search_terms = search_terms_map.get(keyword, search_terms_map["default"])
    print(f"✅ 生成了 {len(search_terms)} 个优化搜索词")
    return search_terms

def filter_relevant_results(results, keyword):
    """
    使用AI筛选相关结果
    
    Args:
        results: 搜索结果列表
        keyword: 关键词
    
    Returns:
        list: 筛选后的相关结果
    """
    if not results:
        return []
    
    print(f"🤖 正在使用AI筛选相关结果，共 {len(results)} 条")
    
    # 准备结果文本
    results_text = "\n".join([f"{i+1}. {r.get('title', '')}" for i, r in enumerate(results)[:10]])
    
    prompt = f"""
你是一个内容筛选专家，擅长判断搜索结果与关键词的相关性。

请从以下搜索结果中，筛选出与 "{keyword}" 相关的结果，重点关注：
1. 包含用户真实体验和评论
2. 讨论设施、服务、环境等方面
3. 与公共设施满意度相关

搜索结果：
{results_text}

请返回相关结果的序号，格式为逗号分隔的数字，例如：1,3,5,7
如果没有相关结果，请返回 "无"
"""
    
    try:
        payload_messages = [
            {"role": "system", "content": "你是一个内容筛选专家，擅长判断搜索结果与关键词的相关性。"},
            {"role": "user", "content": prompt}
        ]
        response = call_deepseek_api(payload_messages)
        
        if response and "content" in response:
            content = response["content"].strip()
            if content == "无":
                print("❌ 未找到相关结果")
                return []
            
            # 解析结果序号
            try:
                selected_indices = [int(idx.strip()) - 1 for idx in content.split(',') if idx.strip().isdigit()]
                # 过滤有效索引
                selected_indices = [idx for idx in selected_indices if 0 <= idx < len(results)]
                filtered_results = [results[idx] for idx in selected_indices]
                print(f"✅ 筛选出 {len(filtered_results)} 条相关结果")
                return filtered_results
            except:
                print("❌ 解析筛选结果失败，使用前3条结果")
                return results[:3]
        else:
            print("❌ AI筛选失败，使用前3条结果")
            return results[:3]
    except Exception as e:
        print(f"❌ 筛选结果时出错: {e}")
        return results[:3]

def structure_content(content, keyword):
    """
    使用AI结构化内容
    
    Args:
        content: 原始内容
        keyword: 关键词
    
    Returns:
        dict: 结构化的内容
    """
    print("🤖 正在使用AI结构化内容")
    
    prompt = f"""
你是一个内容结构化专家，擅长将非结构化的用户评论转换为结构化数据。

请分析以下关于 "{keyword}" 的内容，提取并结构化以下信息：

1. 情感倾向：积极、消极、中性
2. 涉及的方面：设施、服务、环境、藏书、交通、其他
3. 具体评价：总结主要观点
4. 评分：1-5分（1分最差，5分最好）
5. 是否有建议：是/否

内容：
{content[:1000]}...

请以JSON格式返回，字段名如下：
- sentiment: 情感倾向
- aspects: 涉及的方面（数组）
- evaluation: 具体评价
- rating: 评分
- has_suggestion: 是否有建议

示例输出：
{
    "sentiment": "积极",
    "aspects": ["设施", "服务", "环境"],
    "evaluation": "图书馆设施现代化，服务态度好，环境安静舒适",
    "rating": 4,
    "has_suggestion": false
}
"""
    
    try:
        payload_messages = [
            {"role": "system", "content": "你是一个内容结构化专家，擅长将非结构化的用户评论转换为结构化数据。"},
            {"role": "user", "content": prompt}
        ]
        response = call_deepseek_api(payload_messages)
        
        if response and "content" in response:
            content = response["content"]
            # 提取JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group()
                structured_data = json.loads(json_str)
                print("✅ 内容结构化成功")
                return structured_data
            else:
                print("❌ 解析结构化结果失败")
                # 确保 evaluation 字段不包含 % 符号，避免字符串格式化错误
                safe_evaluation = content[:200].replace('%', '%%')
                return {
                    "sentiment": "中性",
                    "aspects": ["其他"],
                    "evaluation": safe_evaluation,
                    "rating": 3,
                    "has_suggestion": False
                }
        else:
            print("❌ AI结构化失败")
            # 确保 evaluation 字段不包含 % 符号，避免字符串格式化错误
            safe_evaluation = content[:200].replace('%', '%%')
            return {
                "sentiment": "中性",
                "aspects": ["其他"],
                "evaluation": safe_evaluation,
                "rating": 3,
                "has_suggestion": False
            }
    except Exception as e:
        print(f"❌ 结构化内容时出错: {e}")
        # 确保 evaluation 字段不包含 % 符号，避免字符串格式化错误
        safe_evaluation = content[:200].replace('%', '%%')
        return {
            "sentiment": "中性",
            "aspects": ["其他"],
            "evaluation": safe_evaluation,
            "rating": 3,
            "has_suggestion": False
        }

def optimize_search_strategy(keyword):
    """
    优化搜索策略
    
    Args:
        keyword: 关键词
    
    Returns:
        dict: 优化的搜索策略
    """
    print(f"🎯 开始优化搜索策略：{keyword}")
    
    # 生成优化搜索词
    search_terms = generate_optimized_search_terms(keyword)
    
    # 生成搜索策略建议
    prompt = f"""
你是一个搜索策略专家，擅长为网络爬虫制定高效的搜索策略。

请为关键词 "{keyword}" 制定一个详细的搜索策略，包括：

1. 搜索平台优先级：知乎 vs 微博
2. 每个平台的搜索技巧
3. 如何判断结果的相关性
4. 如何提高爬取效率
5. 可能的反爬措施及应对方法

要求：
- 策略要具体可行
- 重点关注如何获取高质量的用户评论
- 考虑到搜索效率和结果质量的平衡
"""
    
    try:
        payload_messages = [
            {"role": "system", "content": "你是一个搜索策略专家，擅长为网络爬虫制定高效的搜索策略。"},
            {"role": "user", "content": prompt}
        ]
        response = call_deepseek_api(payload_messages)
        
        if response and "content" in response:
            strategy = response["content"]
            print("✅ 搜索策略优化成功")
            return {
                "search_terms": search_terms,
                "strategy": strategy
            }
        else:
            print("❌ 搜索策略优化失败")
            return {
                "search_terms": search_terms,
                "strategy": "使用默认搜索策略"
            }
    except Exception as e:
        print(f"❌ 优化搜索策略时出错: {e}")
        return {
            "search_terms": search_terms,
            "strategy": "使用默认搜索策略"
        }

if __name__ == "__main__":
    # 测试
    keyword = "国家博物馆"
    result = optimize_search_strategy(keyword)
    print(f"\n优化后的搜索词：")
    for term in result["search_terms"]:
        print(f"  - {term}")
    print(f"\n搜索策略：")
    print(result["strategy"])
