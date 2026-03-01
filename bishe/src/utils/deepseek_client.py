# -*- coding: utf-8 -*-
"""
DeepSeek客户端模块
用于与DeepSeek API交互
"""
import os
import sys
import json
import time
import requests
from typing import List, Dict, Optional, Any

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        """初始化DeepSeek客户端"""
        try:
            from src.config.config_manager import ConfigManager
            config_manager = ConfigManager()
            llm_config = config_manager.get_llm_config()
            
            self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY") or llm_config.get("api_key", "")
            self.base_url = base_url or os.environ.get("DEEPSEEK_API_URL") or llm_config.get("api_url", "https://api.deepseek.com/v1")
            self.model = model or os.environ.get("DEEPSEEK_MODEL") or llm_config.get("model", "deepseek-chat")
        except Exception as e:
            print(f"⚠️  加载配置失败，使用环境变量: {e}")
            self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
            self.base_url = base_url or os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1")
            self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
            print(f"[OK] DeepSeek API密钥已加载 ({len(self.api_key)}字符)")
            print(f"[OK] API URL: {self.base_url}")
            print(f"[OK] Model: {self.model}")
        else:
            print("[WARN] 未设置DeepSeek API密钥，将使用模拟数据")
    
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 1000) -> Dict[str, Any]:
        """调用Chat Completion API"""
        if not self.api_key:
            # 返回模拟数据
            return {
                "choices": [{
                    "message": {
                        "content": "这是一个积极的评论。\n\n情感倾向: 积极\n情感强度: 4\n具体情绪: 满意\n方面: 服务态度\n情感原因: 服务人员态度友好\nCSI满意度指数: 85\n紧急度: 0\n需要整改: 否"
                    }
                }]
            }
        
        use_model = model or self.model
        url = self.base_url
        if not url.endswith("/chat/completions"):
            if url.endswith("/v1"):
                url = f"{url}/chat/completions"
            elif "/v1/" not in url:
                url = f"{url}/v1/chat/completions"
            
        payload = {
            "model": use_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            if response.status_code != 200:
                print(f"⚠️  API请求失败: HTTP {response.status_code}")
                print(f"⚠️  响应内容: {response.text[:500]}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[WARN] 调用DeepSeek API失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[WARN] 响应内容: {e.response.text[:500] if e.response.text else '无'}")
            # 返回模拟数据作为备用
            return {
                "choices": [{
                    "message": {
                        "content": "这是一个积极的评论。\n\n情感倾向: 积极\n情感强度: 4\n具体情绪: 满意\n方面: 服务态度\n情感原因: 服务人员态度友好\nCSI满意度指数: 85\n紧急度: 0\n需要整改: 否"
                    }
                }]
            }
    
    def embedding(self, input: str, model: str = "deepseek-embedding-v1.0") -> Dict[str, Any]:
        """调用Embedding API"""
        if not self.api_key:
            # 返回模拟数据
            return {
                "data": [{
                    "embedding": [0.0] * 768  # 模拟768维嵌入
                }]
            }
        
        url = f"{self.base_url}/embeddings"
        payload = {
            "model": model,
            "input": input
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️  调用DeepSeek Embedding API失败: {e}")
            # 返回模拟数据作为备用
            return {
                "data": [{
                    "embedding": [0.0] * 768  # 模拟768维嵌入
                }]
            }

if __name__ == "__main__":
    # 测试
    client = DeepSeekClient()
    
    # 测试chat_completion
    messages = [
        {"role": "system", "content": "你是一个专业的情感分析师，负责分析公共设施相关评论的情感。"},
        {"role": "user", "content": "广州图书馆的环境很好，书籍很全，服务态度也不错"}
    ]
    
    response = client.chat_completion(messages)
    print("Chat Completion响应:")
    print(json.dumps(response, ensure_ascii=False, indent=2))
    
    # 测试embedding
    embedding_response = client.embedding("广州图书馆的环境很好")
    print("\nEmbedding响应:")
    print(f"嵌入维度: {len(embedding_response['data'][0]['embedding'])}")
