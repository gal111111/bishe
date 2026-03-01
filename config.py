# -*- coding: utf-8 -*-
"""
情感分析模块配置
优先使用环境变量配置API密钥，确保安全性

环境变量设置方法：
Windows:
  set DEEPSEEK_API_KEY=your-api-key-here
  或在 .env 文件中添加

Linux/Mac:
  export DEEPSEEK_API_KEY=your-api-key-here
"""
import os

# 尝试加载 dotenv（如果已安装）
try:
    from dotenv import load_dotenv
    # Load from project root .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use system environment variables

# DeepSeek API配置（从环境变量读取，提高安全性）
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-gxclqeqaklaobomgciagbofmkmeoeciizwqdsmiicsqqlobc')
DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.siliconflow.cn/v1/chat/completions')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-ai/DeepSeek-V3')

if not DEEPSEEK_API_KEY:
    print("⚠️  警告: 未设置 DEEPSEEK_API_KEY 环境变量")
    print("   请在 .env 文件中添加: DEEPSEEK_API_KEY=your-key-here")