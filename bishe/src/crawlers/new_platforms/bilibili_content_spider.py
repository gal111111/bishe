# -*- coding: utf-8 -*-
"""
B站爬虫 - Selenium版本（内容版）
功能：爬取B站视频标题和描述
"""

import time
import os
import sys
import random
import re
import pickle
from datetime import datetime
from selenium.webdriver.common.by import By

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.crawlers.selenium_spiders.common import BaseSpider, init_csv_header, save_to_csv_standard


class BilibiliContentSpider(BaseSpider):
    """
    B站爬虫类（内容版）
    """
    
    def __init__(self, use_edge=True):
        super().__init__(use_edge=use_edge)
        self.platform = "B站"
        self.video_fields = [
            "platform", "video_id", "video_title", "video_author", 
            "video_description", "crawl_time"
        ]
    
    def load_cookies(self, cookie_file="data/cookies/bilibili_cookies.pkl"):
        """加载已保存的Cookie"""
        if not os.path.exists(cookie_file):
            print(f"\033[33m[B站爬虫][警告]\033[0m Cookie文件不存在: {cookie_file}")
            return False
        
        try:
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            self.driver.get("https://www.bilibili.com")
            time.sleep(2)
            
            for cookie in cookies:
                cookie_copy = cookie.copy()
                if 'expiry' in cookie_copy:
                    cookie_copy['expiry'] = int(cookie_copy['expiry'])
                try:
                    self.driver.add_cookie(cookie_copy)
                except:
                    pass
            
            print(f"\033[32m[B站爬虫]\033[0m 已加载 {len(cookies)} 个Cookie")
            return True
        except Exception as e:
            print(f"\033[31m[B站爬虫][错误]\033[0m 加载Cookie失败: {e}")
            return False
    
    def search_and_get_videos(self, keyword, max_videos=10):
        """搜索关键词并获取视频链接"""
        print(f"\033[34m[B站爬虫]\033[0m 开始搜索关键词: {keyword}")
        
        search_url = f"https://search.bilibili.com/all?keyword={keyword}"
        self.driver.get(search_url)
        time.sleep(5)
        
        video_links = []
        scroll_count = 0
        
        while len(video_links) < max_videos and scroll_count < 10:
            try:
                videos = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='video/']")
                for video in videos:
                    href = video.get_attribute("href")
                    if href and "video" in href and href not in video_links:
                        video_links.append(href)
                        print(f"\033[32m[B站爬虫]\033[0m 获取视频链接: {href}")
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                scroll_count += 1
            except Exception as e:
                print(f"\033[31m[B站爬虫][错误]\033[0m 搜索失败: {e}")
                break
        
        print(f"\033[32m[B站爬虫]\033[0m 共获取 {len(video_links)} 个视频链接")
        return video_links[:max_videos]
    
    def crawl_video_content(self, video_url):
        """爬取视频内容"""
        print(f"\033[34m[B站爬虫]\033[0m 爬取视频内容: {video_url}")
        
        self.driver.get(video_url)
        time.sleep(5)
        
        video_title = "NULL"
        video_author = "NULL"
        video_id = "NULL"
        video_description = "NULL"
        
        try:
            match = re.search(r'video/([a-zA-Z0-9]+)', video_url)
            if match:
                video_id = match.group(1)
            
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1")
                video_title = title_elem.text.strip()
            except:
                pass
            
            try:
                author_selectors = ["[class*='up-name']", "[class*='user-name']"]
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
            
            try:
                desc_selectors = ["[class*='desc']", "[class*='description']"]
                for selector in desc_selectors:
                    try:
                        desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        video_description = desc_elem.text.strip()
                        if video_description:
                            break
                    except:
                        pass
            except:
                pass
            
            print(f"\033[34m[B站爬虫]\033[0m 视频标题: {video_title}")
            print(f"\033[34m[B站爬虫]\033[0m 视频作者: {video_author}")
            
            return {
                "platform": self.platform,
                "video_id": video_id,
                "video_title": video_title,
                "video_author": video_author,
                "video_description": video_description,
                "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"\033[31m[B站爬虫][错误]\033[0m 爬取视频失败: {e}")
            return None
    
    def run(self, keyword, output_dir="data/raw", max_videos=10):
        """运行爬虫"""
        print("\033[34m" + "="*60 + "\033[0m")
        print(f"\033[34m[B站爬虫]\033[0m 启动B站爬虫（内容版）")
        print("\033[34m" + "="*60 + "\033[0m")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"bilibili_{keyword}_{timestamp}.csv")
        
        init_csv_header(output_file, self.video_fields)
        all_videos = []
        
        try:
            self.load_cookies()
            video_links = self.search_and_get_videos(keyword, max_videos)
            
            for i, video_url in enumerate(video_links):
                print(f"\033[34m[B站爬虫]\033[0m 进度: {i+1}/{len(video_links)}")
                try:
                    video_data = self.crawl_video_content(video_url)
                    if video_data:
                        all_videos.append(video_data)
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    print(f"\033[31m[B站爬虫][错误]\033[0m 爬取失败: {e}")
                    continue
            
            if all_videos:
                save_to_csv_standard(all_videos, output_file, self.video_fields)
                print(f"\033[32m[B站爬虫]\033[0m 共保存 {len(all_videos)} 个视频到: {output_file}")
            else:
                print(f"\033[33m[B站爬虫][警告]\033[0m 未获取到视频数据")
            
            return output_file
            
        except Exception as e:
            print(f"\033[31m[B站爬虫][错误]\033[0m 爬虫运行失败: {e}")
            return None
        finally:
            print("\033[34m[B站爬虫]\033[0m 爬取完成，5秒后关闭浏览器...")
            time.sleep(5)
            self.driver.quit()


if __name__ == "__main__":
    spider = BilibiliContentSpider(use_edge=True)
    spider.run("上海迪士尼", max_videos=5)
