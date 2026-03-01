# -*- coding: utf-8 -*-
"""
抖音爬虫 - Selenium版本（内容版）
功能：爬取抖音视频标题和描述
"""

import time
import os
import sys
import random
import re
import pickle
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.crawlers.selenium_spiders.common import BaseSpider, init_csv_header, save_to_csv_standard


class DouyinContentSpider(BaseSpider):
    """
    抖音爬虫类（内容版）
    """
    
    def __init__(self, use_edge=True):
        super().__init__(use_edge=use_edge)
        self.platform = "抖音"
        self.video_fields = [
            "platform", "video_id", "video_title", "video_author", 
            "video_description", "video_like_count", "video_comment_count", 
            "video_share_count", "crawl_time"
        ]
    
    def load_cookies(self, cookie_file="data/cookies/douyin_cookies.pkl"):
        """
        加载已保存的Cookie
        
        Args:
            cookie_file: Cookie文件路径
        """
        if not os.path.exists(cookie_file):
            print(f"\033[33m[抖音爬虫][警告]\033[0m Cookie文件不存在: {cookie_file}")
            return False
        
        try:
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            # 先访问一次抖音首页，设置domain
            self.driver.get("https://www.douyin.com")
            time.sleep(2)
            
            for cookie in cookies:
                cookie_copy = cookie.copy()
                if 'expiry' in cookie_copy:
                    cookie_copy['expiry'] = int(cookie_copy['expiry'])
                
                try:
                    self.driver.add_cookie(cookie_copy)
                except Exception as e:
                    pass
            
            print(f"\033[32m[抖音爬虫]\033[0m 已加载 {len(cookies)} 个Cookie")
            return True
            
        except Exception as e:
            print(f"\033[31m[抖音爬虫][错误]\033[0m 加载Cookie失败: {e}")
            return False
    
    def search_and_get_videos(self, keyword, max_videos=10):
        """
        搜索关键词并获取视频链接
        
        Args:
            keyword: 搜索关键词
            max_videos: 最大视频数量
        """
        print(f"\033[34m[抖音爬虫]\033[0m 开始搜索关键词: {keyword}")
        
        search_url = f"https://www.douyin.com/search/{keyword}?type=video"
        self.driver.get(search_url)
        time.sleep(8)
        
        video_links = []
        scroll_count = 0
        max_scrolls = 15
        
        while len(video_links) < max_videos and scroll_count < max_scrolls:
            print(f"\033[34m[抖音爬虫]\033[0m 滚动页面 {scroll_count + 1}")
            
            try:
                # 尝试多种选择器查找视频
                selectors = [
                    "a[href*='video/']",
                    "[class*='video-item'] a",
                    "[class*='search-card'] a",
                    "li a[href*='/video/']"
                ]
                
                for selector in selectors:
                    try:
                        videos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for video in videos:
                            try:
                                href = video.get_attribute("href")
                                if href and "video" in href and href not in video_links:
                                    video_links.append(href)
                                    print(f"\033[32m[抖音爬虫]\033[0m 获取视频链接: {href}")
                            except:
                                pass
                    except:
                        pass
                
                # 滚动页面
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(3, 5))
                scroll_count += 1
                
            except Exception as e:
                print(f"\033[31m[抖音爬虫][错误]\033[0m 搜索失败: {e}")
                break
        
        print(f"\033[32m[抖音爬虫]\033[0m 共获取 {len(video_links)} 个视频链接")
        return video_links[:max_videos]
    
    def crawl_video_content(self, video_url):
        """
        爬取视频内容
        
        Args:
            video_url: 视频URL
        """
        print(f"\033[34m[抖音爬虫]\033[0m 爬取视频内容: {video_url}")
        
        self.driver.get(video_url)
        time.sleep(8)
        
        video_data = {}
        video_title = "NULL"
        video_author = "NULL"
        video_id = "NULL"
        video_description = "NULL"
        video_like_count = "NULL"
        video_comment_count = "NULL"
        video_share_count = "NULL"
        
        try:
            # 提取视频ID
            match = re.search(r'video/(\d+)', video_url)
            if match:
                video_id = match.group(1)
            
            # 提取视频标题/描述
            try:
                desc_selectors = [
                    "[class*='video-title']",
                    "[class*='video-desc']",
                    "[data-e2e*='video-desc']",
                    "h1",
                    "[class*='title']"
                ]
                for selector in desc_selectors:
                    try:
                        title_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        title_text = title_elem.text.strip()
                        if title_text:
                            video_title = title_text
                            video_description = title_text
                            break
                    except:
                        pass
            except:
                pass
            
            # 提取视频作者
            try:
                author_selectors = [
                    "[class*='author'] [class*='name']",
                    "[class*='user-name']",
                    "[data-e2e*='author']",
                    "[class*='nickname']"
                ]
                for selector in author_selectors:
                    try:
                        author_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        video_author = author_elem.text.strip()
                        if video_author:
                            break
                    except:
                        pass
            except:
                pass
            
            # 提取互动数据（点赞、评论、分享）
            try:
                # 查找所有包含数字的元素
                interaction_elements = self.driver.find_elements(By.CSS_SELECTOR, "div, span")
                interaction_texts = []
                for elem in interaction_elements:
                    try:
                        text = elem.text.strip()
                        if text and any(char in text for char in '0123456789'):
                            interaction_texts.append(text)
                    except:
                        pass
                
                # 尝试提取点赞、评论、分享数据
                if len(interaction_texts) >= 3:
                    video_like_count = interaction_texts[0]
                    video_comment_count = interaction_texts[1]
                    video_share_count = interaction_texts[2]
            except:
                pass
            
            print(f"\033[34m[抖音爬虫]\033[0m 视频标题: {video_title}")
            print(f"\033[34m[抖音爬虫]\033[0m 视频作者: {video_author}")
            
            video_data = {
                "platform": self.platform,
                "video_id": video_id,
                "video_title": video_title,
                "video_author": video_author,
                "video_description": video_description,
                "video_like_count": video_like_count,
                "video_comment_count": video_comment_count,
                "video_share_count": video_share_count,
                "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"\033[31m[抖音爬虫][错误]\033[0m 爬取视频失败: {e}")
        
        return video_data
    
    def run(self, keyword, output_dir="data/raw", max_videos=10):
        """
        运行爬虫
        
        Args:
            keyword: 搜索关键词
            output_dir: 输出目录
            max_videos: 最大视频数量
        """
        print("\033[34m" + "="*60 + "\033[0m")
        print(f"\033[34m[抖音爬虫]\033[0m 启动抖音爬虫（内容版）")
        print("\033[34m" + "="*60 + "\033[0m")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"douyin_{keyword}_{timestamp}.csv")
        
        init_csv_header(output_file, self.video_fields)
        
        all_videos = []
        
        try:
            # 加载Cookie
            self.load_cookies()
            
            # 搜索获取视频链接
            video_links = self.search_and_get_videos(keyword, max_videos)
            
            # 逐个爬取视频内容
            for i, video_url in enumerate(video_links):
                print(f"\033[34m[抖音爬虫]\033[0m 进度: {i+1}/{len(video_links)}")
                
                try:
                    video_data = self.crawl_video_content(video_url)
                    if video_data:
                        all_videos.append(video_data)
                    
                    # 随机延迟
                    time.sleep(random.uniform(3, 5))
                    
                except Exception as e:
                    print(f"\033[31m[抖音爬虫][错误]\033[0m 爬取失败: {e}")
                    continue
            
            # 保存数据
            if all_videos:
                save_to_csv_standard(all_videos, output_file, self.video_fields)
                print(f"\033[32m[抖音爬虫]\033[0m 共保存 {len(all_videos)} 个视频到: {output_file}")
            else:
                print(f"\033[33m[抖音爬虫][警告]\033[0m 未获取到视频数据")
            
            return output_file
            
        except Exception as e:
            print(f"\033[31m[抖音爬虫][错误]\033[0m 爬虫运行失败: {e}")
            return None
        finally:
            print("\033[34m[抖音爬虫]\033[0m 爬取完成，5秒后关闭浏览器...")
            time.sleep(5)
            self.driver.quit()


if __name__ == "__main__":
    spider = DouyinContentSpider(use_edge=True)
    spider.run("上海迪士尼", max_videos=5)
