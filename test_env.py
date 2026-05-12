#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试环境变量加载
"""
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 打印环境变量
print("DEEPSEEK_API_KEY:", os.environ.get("DEEPSEEK_API_KEY"))
print("DEEPSEEK_API_URL:", os.environ.get("DEEPSEEK_API_URL"))
print("DEEPSEEK_MODEL:", os.environ.get("DEEPSEEK_MODEL"))

# 测试配置管理器
from src.config.config_manager import config_manager
print("\n从配置管理器获取:")
llm_config = config_manager.get_llm_config()
print("API Key:", llm_config.get("api_key"))
print("API URL:", llm_config.get("api_url"))
print("Model:", llm_config.get("model"))