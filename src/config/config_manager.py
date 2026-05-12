
# -*- coding: utf-8 -*-
"""
配置模块 - 管理大模型API密钥和系统配置
优先使用环境变量，保证安全性
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
        """加载配置文件，优先使用环境变量"""
        config = self._get_default_config()
        
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                print(f"⚠️  加载配置文件失败: {e}")
        
        return config
    
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
        """保存配置文件（不保存API密钥，使用环境变量）"""
        safe_config = self.config.copy()
        safe_config["llm"]["api_key"] = ""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(safe_config, f, ensure_ascii=False, indent=2)
    
    def get_api_key(self, provider=None):
        """获取API密钥，优先从环境变量获取"""
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        
        if not api_key:
            api_key = self.config["llm"].get("api_key", "")
        
        if not api_key:
            print("\n⚠️  未配置API密钥！")
            print("请设置环境变量 DEEPSEEK_API_KEY 或在 .env 文件中配置")
        
        return api_key
    
    def set_api_key(self, api_key, provider="deepseek"):
        """设置API密钥（仅在内存中，不保存到文件）"""
        self.config["llm"]["api_key"] = api_key
        self.config["llm"]["provider"] = provider
    
    def get_llm_config(self):
        """获取大模型配置，优先使用环境变量"""
        config = self.config["llm"].copy()
        
        if os.environ.get("DEEPSEEK_API_KEY"):
            config["api_key"] = os.environ.get("DEEPSEEK_API_KEY")
        if os.environ.get("DEEPSEEK_API_URL"):
            config["api_url"] = os.environ.get("DEEPSEEK_API_URL")
        if os.environ.get("DEEPSEEK_MODEL"):
            config["model"] = os.environ.get("DEEPSEEK_MODEL")
        if os.environ.get("DEEPSEEK_TEMPERATURE"):
            config["temperature"] = float(os.environ.get("DEEPSEEK_TEMPERATURE"))
        if os.environ.get("DEEPSEEK_MAX_TOKENS"):
            config["max_tokens"] = int(os.environ.get("DEEPSEEK_MAX_TOKENS"))
        
        return config
    
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

