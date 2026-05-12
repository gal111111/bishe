# -*- coding: utf-8 -*-
"""
小红书爬虫 - Selenium版本（内容版）
功能：爬取小红书帖子标题和内容
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


class XiaohongshuSpider(BaseSpider):
    """
    小红书爬虫类（内容版）
    """
    
    def __init__(self, use_edge=True):
        super().__init__(use_edge=use_edge)
        self.platform = "小红书"
        self.post_fields = [
            "platform", "post_id", "post_title", "post_author", 
            "post_content", "post_like_count", "post_collect_count", 
            "post_comment_count", "crawl_time"
        ]
    
    def load_cookies(self, cookie_file="data/cookies/xiaohongshu_cookies.pkl"):
        """
        加载已保存的Cookie
        
        Args:
            cookie_file: Cookie文件路径
        """
        if not os.path.exists(cookie_file):
            print(f"\033[33m[小红书爬虫][警告]\033[0m Cookie文件不存在: {cookie_file}")
            return False
        
        try:
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            # 先访问一次小红书首页，设置domain
            self.driver.get("https://www.xiaohongshu.com")
            time.sleep(2)
            
            for cookie in cookies:
                # 移除可能导致问题的字段
                cookie_copy = cookie.copy()
                if 'expiry' in cookie_copy:
                    cookie_copy['expiry'] = int(cookie_copy['expiry'])
                
                try:
                    self.driver.add_cookie(cookie_copy)
                except Exception as e:
                    pass
            
            print(f"\033[32m[小红书爬虫]\033[0m 已加载 {len(cookies)} 个Cookie")
            return True
            
        except Exception as e:
            print(f"\033[31m[小红书爬虫][错误]\033[0m 加载Cookie失败: {e}")
            return False
    
    def click_web_version_button(self):
        """
        点击网页版按钮
        """
        try:
            print(f"\033[34m[小红书爬虫]\033[0m 正在查找网页版按钮...")
            web_button_selectors = [
                "//*[contains(text(), '网页版')]",
                "//span[contains(text(), '网页版')]",
                "//button[contains(text(), '网页版')]",
                "[class*='web']",
                "[class*='desktop']"
            ]
            
            found = False
            for selector in web_button_selectors:
                try:
                    if selector.startswith("//"):
                        buttons = self.driver.find_elements(By.XPATH, selector)
                    else:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if buttons:
                        for btn in buttons:
                            try:
                                btn.click()
                                print(f"\033[32m[小红书爬虫]\033[0m 成功点击网页版按钮")
                                time.sleep(3)
                                found = True
                                break
                            except:
                                pass
                    if found:
                        break
                except:
                    pass
            
            if not found:
                print(f"\033[33m[小红书爬虫][警告]\033[0m 未找到网页版按钮")
        except Exception as e:
            print(f"\033[31m[小红书爬虫][错误]\033[0m 点击网页版按钮失败: {e}")
    
    def search_and_get_posts(self, keyword, max_posts=10):
        """
        搜索关键词并获取帖子链接
        
        Args:
            keyword: 搜索关键词
            max_posts: 最大帖子数量
        """
        print(f"\033[34m[小红书爬虫]\033[0m 开始搜索关键词: {keyword}")
        
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
        self.driver.get(search_url)
        time.sleep(5)
        
        # 点击网页版按钮
        self.click_web_version_button()
        time.sleep(3)
        
        post_links = []
        scroll_count = 0
        max_scrolls = 10
        
        while len(post_links) < max_posts and scroll_count < max_scrolls:
            print(f"\033[34m[小红书爬虫]\033[0m 滚动页面 {scroll_count + 1}")
            
            try:
                # 查找帖子链接
                notes = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/explore/']")
                
                for note in notes:
                    try:
                        href = note.get_attribute("href")
                        if href and "/explore/" in href and href not in post_links:
                            post_links.append(href)
                            print(f"\033[32m[小红书爬虫]\033[0m 获取帖子链接: {href}")
                    except:
                        pass
                
                # 滚动页面
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                scroll_count += 1
                
            except Exception as e:
                print(f"\033[31m[小红书爬虫][错误]\033[0m 搜索失败: {e}")
                break
        
        print(f"\033[32m[小红书爬虫]\033[0m 共获取 {len(post_links)} 个帖子链接")
        return post_links[:max_posts]
    
    def crawl_post_content(self, post_url):
        """
        爬取帖子详情页的内容
        
        Args:
            post_url: 帖子URL
        """
        print(f"\033[34m[小红书爬虫]\033[0m 爬取帖子内容: {post_url}")
        
        self.driver.get(post_url)
        time.sleep(5)
        
        # 点击网页版按钮
        self.click_web_version_button()
        time.sleep(3)
        
        post_data = {}
        post_title = "NULL"
        post_author = "NULL"
        post_id = "NULL"
        post_content = "NULL"
        post_like_count = "NULL"
        post_collect_count = "NULL"
        post_comment_count = "NULL"
        
        try:
            # 提取帖子ID
            match = re.search(r'/explore/(\w+)', post_url)
            if match:
                post_id = match.group(1)
            
            # 提取帖子标题
            try:
                title_selectors = [
                    "#detail-title",
                    "[class*='title']",
                    "h1",
                    "[data-e2e*='title']"
                ]
                for selector in title_selectors:
                    try:
                        title_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        post_title = title_elem.text.strip()
                        if post_title:
                            break
                    except:
                        pass
            except:
                pass
            
            # 提取帖子作者
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
                        post_author = author_elem.text.strip()
                        if post_author:
                            break
                    except:
                        pass
            except:
                pass
            
            # 提取帖子正文内容
            try:
                content_selectors = [
                    "[class*='content']",
                    "[class*='desc']",
                    "[data-e2e*='content']",
                    "[class*='note-content']"
                ]
                for selector in content_selectors:
                    try:
                        content_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        contents = []
                        for elem in content_elems:
                            try:
                                text = elem.text.strip()
                                if text and len(text) > 10:
                                    contents.append(text)
                            except:
                                pass
                        if contents:
                            post_content = "\n".join(contents)
                            break
                    except:
                        pass
            except:
                pass
            
            # 提取互动数据（点赞、收藏、评论）
            try:
                interaction_selectors = [
                    "[class*='like']",
                    "[class*='collect']",
                    "[class*='comment']"
                ]
                for i, selector in enumerate(interaction_selectors):
                    try:
                        elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elems:
                            text = elems[0].text.strip()
                            if i == 0:
                                post_like_count = text
                            elif i == 1:
                                post_collect_count = text
                            elif i == 2:
                                post_comment_count = text
                    except:
                        pass
            except:
                pass
            
            print(f"\033[34m[小红书爬虫]\033[0m 帖子标题: {post_title}")
            print(f"\033[34m[小红书爬虫]\033[0m 帖子作者: {post_author}")
            print(f"\033[34m[小红书爬虫]\033[0m 内容长度: {len(post_content)} 字符")
            
            post_data = {
                "platform": self.platform,
                "post_id": post_id,
                "post_title": post_title,
                "post_author": post_author,
                "post_content": post_content,
                "post_like_count": post_like_count,
                "post_collect_count": post_collect_count,
                "post_comment_count": post_comment_count,
                "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"\033[31m[小红书爬虫][错误]\033[0m 爬取帖子失败: {e}")
        
        return post_data
    
    def run(self, keyword, output_dir="data/raw", max_posts=10):
        """
        运行爬虫
        
        Args:
            keyword: 搜索关键词
            output_dir: 输出目录
            max_posts: 最大帖子数量
        """
        print("\033[34m" + "="*60 + "\033[0m")
        print(f"\033[34m[小红书爬虫]\033[0m 启动小红书爬虫（内容版）")
        print("\033[34m" + "="*60 + "\033[0m")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"xiaohongshu_{keyword}_{timestamp}.csv")
        
        init_csv_header(output_file, self.post_fields)
        
        all_posts = []
        
        try:
            # 加载Cookie
            self.load_cookies()
            
            # 搜索获取帖子链接
            post_links = self.search_and_get_posts(keyword, max_posts)
            
            # 逐个爬取帖子内容
            for i, post_url in enumerate(post_links):
                print(f"\033[34m[小红书爬虫]\033[0m 进度: {i+1}/{len(post_links)}")
                
                try:
                    post_data = self.crawl_post_content(post_url)
                    if post_data:
                        all_posts.append(post_data)
                    
                    # 随机延迟
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    print(f"\033[31m[小红书爬虫][错误]\033[0m 爬取失败: {e}")
                    continue
            
            # 保存数据
            if all_posts:
                save_to_csv_standard(all_posts, output_file, self.post_fields)
                print(f"\033[32m[小红书爬虫]\033[0m 共保存 {len(all_posts)} 个帖子到: {output_file}")
            else:
                print(f"\033[33m[小红书爬虫][警告]\033[0m 未获取到帖子数据")
            
            return output_file
            
        except Exception as e:
            print(f"\033[31m[小红书爬虫][错误]\033[0m 爬虫运行失败: {e}")
            return None
        finally:
            print("\033[34m[小红书爬虫]\033[0m 爬取完成，5秒后关闭浏览器...")
            time.sleep(5)
            self.driver.quit()


if __name__ == "__main__":
    spider = XiaohongshuSpider(use_edge=True)
    spider.run("上海迪士尼", max_posts=5)
