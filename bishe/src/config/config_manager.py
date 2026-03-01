
# -*- coding: utf-8 -*-
"""
配置模块 - 管理大模型API密钥和系统配置
"""
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "api_config.json"


class ConfigManager:
    def __init__(self):
        self.config_dir = PROJECT_ROOT / "config"
        self.config_dir.mkdir(exist_ok=True)
        self.crawl_data_dir = PROJECT_ROOT / "crawl_data"
        
        for platform in ["tieba", "weibo", "hupu", "zhihu"]:
            (self.crawl_data_dir / platform).mkdir(exist_ok=True, parents=True)
        
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  加载配置文件失败: {e}")
                return self._get_default_config()
        else:
            return self._get_default_config()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "llm": {
                "provider": "deepseek",
                "api_key": "",
                "api_url": "https://api.siliconflow.cn/v1/chat/completions",
                "model": "deepseek-ai/DeepSeek-V3",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "crawler": {
                "timeout": 30,
                "retry_times": 3,
                "cleanup_on_start": True,
                "max_keywords_per_platform": 10
            },
            "data": {
                "encoding": "utf-8-sig",
                "deduplicate_by": "content",
                "min_content_length": 5
            }
        }
    
    def save_config(self):
        """保存配置文件"""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get_api_key(self, provider=None):
        """获取API密钥"""
        if provider is None:
            provider = self.config["llm"]["provider"]
        
        if not self.config["llm"]["api_key"]:
            print("\n⚠️  未配置API密钥！")
            print("请输入你的API密钥:")
            api_key = input().strip()
            if api_key:
                self.config["llm"]["api_key"] = api_key
                self.save_config()
                print("✅ API密钥已保存！")
        
        return self.config["llm"]["api_key"]
    
    def set_api_key(self, api_key, provider="deepseek"):
        """设置API密钥"""
        self.config["llm"]["api_key"] = api_key
        self.config["llm"]["provider"] = provider
        self.save_config()
    
    def get_llm_config(self):
        """获取大模型配置"""
        return self.config["llm"]
    
    def get_crawler_config(self):
        """获取爬虫配置"""
        return self.config["crawler"]
    
    def get_data_config(self):
        """获取数据配置"""
        return self.config["data"]
    
    def get_crawl_data_path(self, platform, filename=None):
        """获取爬取数据路径"""
        platform_dir = self.crawl_data_dir / platform
        if filename:
            return str(platform_dir / filename)
        return str(platform_dir)
    
    def get_merged_data_path(self):
        """获取合并数据路径"""
        return str(self.crawl_data_dir / "merged_data.json")


config_manager = ConfigManager()

