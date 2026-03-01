
# -*- coding: utf-8 -*-
"""
模块1：大模型关键词智能扩展
输入核心关键词，调用大模型生成高相关性拓展关键词
"""
import os
import sys
import json
import requests
from typing import List, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.config.config_manager import config_manager


class KeywordExpander:
    def __init__(self):
        self.config = config_manager.get_llm_config()
        self.api_key = config_manager.get_api_key()
        self.api_url = self.config.get("api_url", "https://api.siliconflow.cn/v1/chat/completions")
        self.model = self.config.get("model", "deepseek-ai/DeepSeek-V3")
    
    def _call_deepseek_api(self, prompt: str) -&gt; str:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的关键词拓展专家，擅长根据核心关键词生成高相关性的搜索关键词。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 2000)
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"❌ API调用失败: {e}")
            raise
    
    def expand_keywords(self, core_keyword: str) -&gt; List[str]:
        """
        核心关键词拓展功能
        输入：单个核心关键词（字符串）
        输出：拓展关键词列表（JSON格式）
        """
        print(f"\n{'='*80}")
        print(f"🔍 关键词扩展 - 核心关键词: {core_keyword}")
        print(f"{'='*80}")
        
        prompt = f"""请为以下核心关键词生成拓展搜索关键词，要求：

1. 拓展关键词需覆盖正/负/中性情感维度
2. 适配贴吧/微博/虎扑/知乎平台搜索习惯
3. 聚焦"公共设施"（交通/卫生/服务/配套等）
4. 生成至少10个拓展关键词
5. 以JSON数组格式返回，不要有其他文字

核心关键词：{core_keyword}

请直接返回JSON数组，格式如下：
["关键词1", "关键词2", "关键词3", ...]
"""
        
        try:
            response = self._call_deepseek_api(prompt)
            
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start &gt;= 0 and json_end &gt; json_start:
                json_str = response[json_start:json_end]
                keywords = json.loads(json_str)
            else:
                keywords = [core_keyword]
            
            keywords = list(set(keywords))
            keywords = [k for k in keywords if k and len(k.strip()) &gt; 0]
            
            if core_keyword not in keywords:
                keywords.insert(0, core_keyword)
            
            print(f"\n✅ 关键词扩展成功！共生成 {len(keywords)} 个关键词:")
            for i, kw in enumerate(keywords, 1):
                print(f"   {i}. {kw}")
            
            return keywords
            
        except Exception as e:
            print(f"⚠️  关键词扩展失败，返回原关键词: {e}")
            return [core_keyword]


def main():
    print("=" * 80)
    print("🔍 关键词扩展模块 - 示例调用")
    print("=" * 80)
    
    expander = KeywordExpander()
    
    core_keyword = "上海迪士尼 公共设施 满意度"
    print(f"\n🎯 核心关键词: {core_keyword}")
    
    keywords = expander.expand_keywords(core_keyword)
    
    print(f"\n{'='*80}")
    print("📋 最终关键词列表:")
    print(f"{'='*80}")
    for i, kw in enumerate(keywords, 1):
        print(f"{i}. {kw}")
    
    output_file = os.path.join(PROJECT_ROOT, "data", "expanded_keywords.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(keywords, f, ensure_ascii=False, indent=2)
    print(f"\n💾 关键词已保存到: {output_file}")


if __name__ == "__main__":
    main()

