# -*- coding: utf-8 -*-
"""
小红书爬虫 - Selenium版本（增强版）
功能：爬取小红书笔记内容、评论等
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
    小红书爬虫类（增强版 - 支持评论爬取）
    """
    
    def __init__(self, use_edge=True):
        super().__init__(use_edge=use_edge)
        self.platform = "小红书"
        self.comment_fields = [
            "platform", "post_id", "post_title", "post_author", 
            "comment_id", "comment_author", "comment_content", 
            "comment_like_count", "comment_time", "crawl_time"
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
    
    def search_and_get_posts(self, keyword, max_posts=10):
        """
        搜索关键词并获取笔记链接
        
        Args:
            keyword: 搜索关键词
            max_posts: 最大笔记数量
        """
        print(f"\033[34m[小红书爬虫]\033[0m 开始搜索关键词: {keyword}")
        
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
        self.driver.get(search_url)
        time.sleep(5)
        
        # 尝试点击"网页版"按钮
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
                        # XPath选择器
                        buttons = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS选择器
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
        
        post_links = []
        scroll_count = 0
        max_scrolls = 10
        
        while len(post_links) < max_posts and scroll_count < max_scrolls:
            print(f"\033[34m[小红书爬虫]\033[0m 滚动页面 {scroll_count + 1}")
            
            try:
                # 查找笔记链接
                notes = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/explore/']")
                
                for note in notes:
                    try:
                        href = note.get_attribute("href")
                        if href and "/explore/" in href and href not in post_links:
                            post_links.append(href)
                            print(f"\033[32m[小红书爬虫]\033[0m 获取笔记链接: {href}")
                    except:
                        pass
                
                # 滚动页面
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                scroll_count += 1
                
            except Exception as e:
                print(f"\033[31m[小红书爬虫][错误]\033[0m 搜索失败: {e}")
                break
        
        print(f"\033[32m[小红书爬虫]\033[0m 共获取 {len(post_links)} 个笔记链接")
        return post_links[:max_posts]
    
    def crawl_post_comments(self, post_url, max_comments=50):
        """
        爬取笔记详情页的评论
        
        Args:
            post_url: 笔记URL
            max_comments: 最大评论数
        """
        print(f"\033[34m[小红书爬虫]\033[0m 爬取笔记评论: {post_url}")
        
        self.driver.get(post_url)
        time.sleep(5)
        
        # 尝试点击"网页版"按钮
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
        
        comments_data = []
        post_title = "NULL"
        post_author = "NULL"
        post_id = "NULL"
        
        try:
            # 提取笔记ID
            match = re.search(r'/explore/(\w+)', post_url)
            if match:
                post_id = match.group(1)
            
            # 提取笔记标题
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, "#detail-title")
                post_title = title_elem.text.strip()
            except:
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, "[class*='title']")
                    post_title = title_elem.text.strip()
                except:
                    pass
            
            # 提取笔记作者
            try:
                author_elem = self.driver.find_element(By.CSS_SELECTOR, "[class*='author'] [class*='name']")
                post_author = author_elem.text.strip()
            except:
                pass
            
            print(f"\033[34m[小红书爬虫]\033[0m 笔记标题: {post_title}")
            print(f"\033[34m[小红书爬虫]\033[0m 笔记作者: {post_author}")
            
            # 滚动到评论区
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.5);")
            time.sleep(2)
            
            # 查找评论区
            try:
                # 尝试多种选择器
                comment_selectors = [
                    "[class*='comment-item']",
                    "[class*='note-comment']",
                    ".comment-inner",
                    "[data-v-*] .content"
                ]
                
                comment_elements = []
                for selector in comment_selectors:
                    try:
                        comment_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if comment_elements:
                            break
                    except:
                        pass
                
                # 如果没找到，尝试查找所有包含评论的区域
                if not comment_elements:
                    # 滚动更多
                    for _ in range(3):
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                    
                    # 尝试查找评论内容
                    all_text = self.driver.find_elements(By.CSS_SELECTOR, "div, span, p")
                    for elem in all_text:
                        try:
                            text = elem.text.strip()
                            if len(text) > 10 and len(text) < 500:
                                # 简单判断是否是评论
                                if any(keyword in text for keyword in ['觉得', '感觉', '喜欢', '好看', '不错', '推荐', '太', '很', '真的']):
                                    comment_elements.append(elem)
                        except:
                            pass
                
                print(f"\033[34m[小红书爬虫]\033[0m 找到 {len(comment_elements)} 个评论元素")
                
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
                        if comment_content == post_title or comment_content == post_author:
                            continue
                        
                        comment_id = f"xhs_cmt_{post_id}_{i}"
                        
                        comments_data.append({
                            "platform": self.platform,
                            "post_id": post_id,
                            "post_title": post_title,
                            "post_author": post_author,
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
                print(f"\033[31m[小红书爬虫][错误]\033[0m 解析评论失败: {e}")
        
        except Exception as e:
            print(f"\033[31m[小红书爬虫][错误]\033[0m 爬取笔记失败: {e}")
        
        print(f"\033[32m[小红书爬虫]\033[0m 获取 {len(comments_data)} 条评论")
        return comments_data
    
    def run(self, keyword, output_dir="data/raw", max_posts=10, max_comments_per_post=30):
        """
        运行爬虫
        
        Args:
            keyword: 搜索关键词
            output_dir: 输出目录
            max_posts: 最大笔记数量
            max_comments_per_post: 每个笔记最大评论数
        """
        print("\033[34m" + "="*60 + "\033[0m")
        print(f"\033[34m[小红书爬虫]\033[0m 启动小红书爬虫（评论增强版）")
        print("\033[34m" + "="*60 + "\033[0m")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"xiaohongshu_comments_{keyword}_{timestamp}.csv")
        
        init_csv_header(output_file, self.comment_fields)
        
        all_comments = []
        
        try:
            # 加载Cookie
            self.load_cookies()
            
            # 搜索获取笔记链接
            post_links = self.search_and_get_posts(keyword, max_posts)
            
            # 逐个爬取评论
            for i, post_url in enumerate(post_links):
                print(f"\033[34m[小红书爬虫]\033[0m 进度: {i+1}/{len(post_links)}")
                
                try:
                    comments = self.crawl_post_comments(post_url, max_comments_per_post)
                    all_comments.extend(comments)
                    
                    # 随机延迟，避免被封
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    print(f"\033[31m[小红书爬虫][错误]\033[0m 爬取失败: {e}")
                    continue
            
            # 保存数据
            if all_comments:
                save_to_csv_standard(all_comments, output_file, self.comment_fields)
                print(f"\033[32m[小红书爬虫]\033[0m 共保存 {len(all_comments)} 条评论到: {output_file}")
            else:
                print(f"\033[33m[小红书爬虫][警告]\033[0m 未获取到评论数据")
            
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
    spider.run("上海迪士尼", max_posts=5, max_comments_per_post=20)
