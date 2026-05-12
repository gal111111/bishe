# -*- coding: utf-8 -*-
"""
页面模块包：各功能页面独立模块
"""
from src.pages.dashboard import show_dashboard
from src.pages.data_center import page_data_center
from src.pages.chatbot import page_chatbot
from src.pages.novel_viz import page_novel_viz
from src.pages.report import page_report

__all__ = [
    'show_dashboard',
    'page_data_center',
    'page_chatbot',
    'page_novel_viz',
    'page_report',
]
