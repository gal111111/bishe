# -*- coding: utf-8 -*-
"""
抖音爬虫 - Selenium版本（增强版）
功能：爬取抖音视频内容、评论等
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


class DouyinSpider(BaseSpider):
    """
    抖音爬虫类（增强版 - 支持评论爬取）
    """
    
    def __init__(self, use_edge=True):
        super().__init__(use_edge=use_edge)
        self.platform = "抖音"
        self.comment_fields = [
            "platform", "video_id", "video_title", "video_author", 
            "comment_id", "comment_author", "comment_content", 
            "comment_like_count", "comment_time", "crawl_time"
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
    
    def crawl_video_comments(self, video_url, max_comments=50):
        """
        爬取视频评论
        
        Args:
            video_url: 视频URL
            max_comments: 最大评论数
        """
        print(f"\033[34m[抖音爬虫]\033[0m 爬取视频评论: {video_url}")
        
        self.driver.get(video_url)
        time.sleep(8)
        
        comments_data = []
        video_title = "NULL"
        video_author = "NULL"
        video_id = "NULL"
        
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
                        video_title = title_elem.text.strip()
                        if video_title:
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
            
            print(f"\033[34m[抖音爬虫]\033[0m 视频标题: {video_title}")
            print(f"\033[34m[抖音爬虫]\033[0m 视频作者: {video_author}")
            
            # 点击评论按钮或滚动到评论区
            try:
                # 尝试点击评论按钮
                comment_btn_selectors = [
                    "[class*='comment']",
                    "[data-e2e*='comment']",
                    "button[class*='comment']"
                ]
                for selector in comment_btn_selectors:
                    try:
                        btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        btn.click()
                        time.sleep(2)
                        break
                    except:
                        pass
            except:
                pass
            
            # 滚动评论区
            for _ in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # 查找评论
            try:
                comment_selectors = [
                    "[class*='comment-item']",
                    "[class*='comment-content']",
                    "[data-e2e*='comment-item']",
                    "[class*='reply-item']",
                    "li[class*='comment']"
                ]
                
                comment_elements = []
                for selector in comment_selectors:
                    try:
                        comment_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if comment_elements:
                            print(f"\033[34m[抖音爬虫]\033[0m 使用选择器 {selector} 找到 {len(comment_elements)} 个元素")
                            break
                    except:
                        pass
                
                # 如果没找到，尝试更通用的方式
                if not comment_elements:
                    all_text = self.driver.find_elements(By.CSS_SELECTOR, "div, span, p")
                    for elem in all_text:
                        try:
                            text = elem.text.strip()
                            if len(text) > 5 and len(text) < 300:
                                comment_elements.append(elem)
                        except:
                            pass
                
                print(f"\033[34m[抖音爬虫]\033[0m 找到 {len(comment_elements)} 个评论元素")
                
                for i, elem in enumerate(comment_elements[:max_comments]):
                    try:
                        comment_text = elem.text.strip()
                        
                        # 过滤无效内容
                        if not comment_text or len(comment_text) < 5:
                            continue
                        
                        # 清理评论内容
                        lines = comment_text.split('\n')
                        comment_content = lines[-1] if lines else comment_text
                        
                        # 跳过标题和作者名
                        if comment_content == video_title or comment_content == video_author:
                            continue
                        
                        comment_id = f"douyin_cmt_{video_id}_{i}"
                        
                        comments_data.append({
                            "platform": self.platform,
                            "video_id": video_id,
                            "video_title": video_title,
                            "video_author": video_author,
                            "comment_id": comment_id,
                            "comment_author": "NULL",
                            "comment_content": comment_content,
                            "comment_like_count": "NULL",
                            "comment_time": "NULL",
                            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                    except Exception as e:
                        continue
                
            except Exception as e:
                print(f"\033[31m[抖音爬虫][错误]\033[0m 解析评论失败: {e}")
        
        except Exception as e:
            print(f"\033[31m[抖音爬虫][错误]\033[0m 爬取视频失败: {e}")
        
        print(f"\033[32m[抖音爬虫]\033[0m 获取 {len(comments_data)} 条评论")
        return comments_data
    
    def run(self, keyword, output_dir="data/raw", max_videos=10, max_comments_per_video=30):
        """
        运行爬虫
        
        Args:
            keyword: 搜索关键词
            output_dir: 输出目录
            max_videos: 最大视频数量
            max_comments_per_video: 每个视频最大评论数
        """
        print("\033[34m" + "="*60 + "\033[0m")
        print(f"\033[34m[抖音爬虫]\033[0m 启动抖音爬虫（评论增强版）")
        print("\033[34m" + "="*60 + "\033[0m")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"douyin_comments_{keyword}_{timestamp}.csv")
        
        init_csv_header(output_file, self.comment_fields)
        
        all_comments = []
        
        try:
            # 加载Cookie
            self.load_cookies()
            
            # 搜索获取视频链接
            video_links = self.search_and_get_videos(keyword, max_videos)
            
            # 逐个爬取评论
            for i, video_url in enumerate(video_links):
                print(f"\033[34m[抖音爬虫]\033[0m 进度: {i+1}/{len(video_links)}")
                
                try:
                    comments = self.crawl_video_comments(video_url, max_comments_per_video)
                    all_comments.extend(comments)
                    
                    # 随机延迟
                    time.sleep(random.uniform(3, 5))
                    
                except Exception as e:
                    print(f"\033[31m[抖音爬虫][错误]\033[0m 爬取失败: {e}")
                    continue
            
            # 保存数据
            if all_comments:
                save_to_csv_standard(all_comments, output_file, self.comment_fields)
                print(f"\033[32m[抖音爬虫]\033[0m 共保存 {len(all_comments)} 条评论到: {output_file}")
            else:
                print(f"\033[33m[抖音爬虫][警告]\033[0m 未获取到评论数据")
            
            return output_file
            
        except Exception as e:
            print(f"\033[31m[抖音爬虫][错误]\033[0m 爬虫运行失败: {e}")
            return None
        finally:
            print("\033[34m[抖音爬虫]\033[0m 爬取完成，5秒后关闭浏览器...")
            time.sleep(5)
            self.driver.quit()


if __name__ == "__main__":
    spider = DouyinSpider(use_edge=True)
    spider.run("上海迪士尼", max_videos=5, max_comments_per_video=20)
