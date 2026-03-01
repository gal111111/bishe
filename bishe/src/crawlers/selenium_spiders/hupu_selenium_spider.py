
# -*- coding: utf-8 -*-
"""
虎扑爬虫模块 - 基于微博/知乎爬虫的成功经验重构
符合数据格式规范
"""

import os
import sys
import time
import json
import csv
import re
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.crawlers.selenium_spiders.common import init_csv_header, format_time_str, format_numeric_value, save_to_csv_standard


class HupuSpider:
    """虎扑爬虫"""
    
    def __init__(self, headless=False):
        self.project_root = project_root
        self.headless = headless
        self.driver_service = Service(executable_path=os.path.join(project_root, "drivers", "edgedriver_win64", "msedgedriver.exe"))
        self.edge_options = Options()
        self.edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.edge_options.add_argument("--disable-blink-features=AutomationControlled")
        self.edge_options.add_argument("--start-maximized")
        self.edge_options.add_argument("--disable-features=EdgeOnDeviceModel")
        
        if self.headless:
            self.edge_options.add_argument("--headless=new")
        
        self.driver = webdriver.Edge(service=self.driver_service, options=self.edge_options)
        self.wait = WebDriverWait(self.driver, 15)
        self.long_wait = WebDriverWait(self.driver, 30)
        self.crawl_data = []
        self.cookie_path = os.path.join(self.project_root, "data", "hupu_cookies.json")
        self._ensure_data_dir()
        self._handle_login()
    
    def _ensure_data_dir(self):
        data_dir = os.path.join(self.project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        raw_dir = os.path.join(data_dir, "raw")
        os.makedirs(raw_dir, exist_ok=True)
    
    def _safe_get(self, url, max_retries=3):
        attempt = 0
        while attempt < max_retries:
            try:
                print("正在访问: %s (尝试 %d/%d)" % (url, attempt + 1, max_retries))
                self.driver.get(url)
                WebDriverWait(self.driver, 30).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                return True
            except Exception as e:
                print("访问URL失败 (尝试 %d/%d): %s" % (attempt + 1, max_retries, str(e)))
                if attempt + 1 < max_retries:
                    time.sleep(2)
                else:
                    return False
            attempt = attempt + 1
        return False
    
    def _handle_login(self):
        print("\n=== 开始处理虎扑登录 ===")
        
        if os.path.exists(self.cookie_path):
            try:
                import json
                self.driver.get("https://www.hupu.com/404")
                time.sleep(1)
                with open(self.cookie_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                added_count = 0
                for cookie in cookies:
                    cookie_copy = cookie.copy()
                    for key in ['sameSite', 'expiry']:
                        if key in cookie_copy:
                            del cookie_copy[key]
                    try:
                        self.driver.add_cookie(cookie_copy)
                        added_count += 1
                    except:
                        continue
                print("已加载 %d/%d 个Cookie" % (added_count, len(cookies)))
                self.driver.get("https://www.hupu.com")
                self.driver.refresh()
                time.sleep(3)
                
                if "www.hupu.com" in self.driver.current_url:
                    print("使用已保存的 Cookie 登录成功！无需扫码！")
                    return True
            except Exception as e:
                print("Cookie加载失败: %s" % str(e))
        
        print("本地Cookie无效/未找到，请在浏览器中登录虎扑")
        print("请在弹出的浏览器窗口中完成登录，登录后请等待页面跳转到主页...")
        
        self._safe_get("https://www.hupu.com/")
        
        login_success = False
        wait_time = 0
        max_wait = 120
        
        while wait_time < max_wait:
            try:
                if "www.hupu.com" in self.driver.current_url:
                    login_success = True
                    break
            except Exception:
                pass
            
            time.sleep(2)
            wait_time += 2
            if wait_time % 10 == 0:
                print("等待登录中...(%d/%d秒)" % (wait_time, max_wait))
        
        if not login_success:
            print("登录超时，请重新运行程序并及时登录")
            return False
        
        print("登录验证成功！")
        try:
            import json
            cookies = self.driver.get_cookies()
            with open(self.cookie_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print("Cookie 已保存到：%s" % self.cookie_path)
        except Exception as e:
            print("Cookie保存失败: %s" % str(e))
        
        return True
    
    def _extract_comments_from_dom(self):
        comments_data = []
        seen_texts = set()
        
        try:
            comment_container_selectors = [
                '.index_discuss-card__Nd4MK',
                '[class*="discuss-card"]',
                '.reply-item',
                '[class*="reply-item"]',
                '.comment-item',
                '[class*="comment-item"]'
            ]
            
            user_name_selectors = [
                '.p_author_name',
                '[class*="p_author_name"]',
                '.d_author',
                '[class*="d_author"]',
                '.username',
                '[class*="username"]'
            ]
            
            comment_content_selectors = [
                '.discuss-card__content',
                '[class*="discuss-card__content"]',
                '.content',
                '[class*="content"]',
                '.reply-content',
                '[class*="reply-content"]',
                '.comment-content',
                '[class*="comment-content"]'
            ]
            
            comment_containers = []
            for selector in comment_container_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        print("  使用DOM选择器 %s 找到 %d 个评论容器" % (selector, len(containers)))
                        comment_containers = containers
                        break
                except:
                    continue
            
            if not comment_containers:
                print("  未找到评论容器，尝试其他方式")
                return None
            
            for container in comment_containers:
                try:
                    user_name = "未知用户"
                    comment_content = ""
                    
                    for selector in user_name_selectors:
                        try:
                            user_elem = container.find_element(By.CSS_SELECTOR, selector)
                            user_text = user_elem.text.strip()
                            if user_text and len(user_text) > 1 and len(user_text) < 50:
                                user_name = user_text
                                break
                        except:
                            continue
                    
                    for selector in comment_content_selectors:
                        try:
                            content_elem = container.find_element(By.CSS_SELECTOR, selector)
                            content_text = content_elem.text.strip()
                            if content_text and len(content_text) > 1:
                                comment_content = content_text
                                break
                        except:
                            continue
                    
                    if comment_content and comment_content not in seen_texts:
                        filter_words = ['回复', '赞', '踩', '评论', '查看', '更多', '收起', '删除', '举报', '分享', '楼', '层']
                        should_skip = False
                        for word in filter_words:
                            if word in comment_content and len(comment_content) < 20:
                                should_skip = True
                                break
                        
                        if not should_skip:
                            comment_content = comment_content.replace('\n', ' ').replace('\r', ' ')
                            
                            if comment_content and len(comment_content) > 0:
                                comments_data.append({"user": user_name, "content": comment_content})
                                seen_texts.add(comment_content)
                                print("    [DOM] 用户: %s, 评论: %s" % (user_name, comment_content[:50]))
                except Exception as e:
                    continue
            
            print("  DOM方式提取到 %d 条评论" % len(comments_data))
            return comments_data
            
        except Exception as e:
            print("  DOM提取评论失败: %s" % str(e))
            return None
    
    def crawl(self, keyword, target_count=20):
        """爬取虎扑内容"""
        print("\n开始爬取虎扑：%s" % keyword)
        
        try:
            print("正在访问虎扑主页: https://www.hupu.com/")
            if not self._safe_get("https://www.hupu.com/"):
                print("[虎扑-错误] 无法访问虎扑主页")
                return self.crawl_data
            
            time.sleep(3)
            
            print("正在点击'手机虎扑'链接...")
            current_window = self.driver.current_window_handle
            window_handles_before = self.driver.window_handles
            
            try:
                hupu_mobile_link = self.wait.until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "手机虎扑"))
                )
                hupu_mobile_link.click()
                print("已点击'手机虎扑'链接")
            except Exception as e:
                print("[虎扑-错误] 点击'手机虎扑'链接失败: %s" % str(e))
                try:
                    hupu_mobile_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, "手机虎扑")
                    hupu_mobile_link.click()
                    print("已通过部分链接文本点击'手机虎扑'")
                except Exception as e2:
                    print("[虎扑-错误] 无法找到'手机虎扑'链接: %s" % str(e2))
                    return self.crawl_data
            
            time.sleep(3)
            
            print("正在切换到新窗口...")
            window_handles_after = self.driver.window_handles
            new_window = None
            for handle in window_handles_after:
                if handle not in window_handles_before:
                    new_window = handle
                    break
            
            if new_window:
                self.driver.switch_to.window(new_window)
                print("已切换到新窗口")
            else:
                print("[虎扑-警告] 未检测到新窗口，继续使用当前窗口")
            
            time.sleep(5)
            print("当前页面URL: %s" % self.driver.current_url)
            
            print("正在查找搜索框...")
            search_input = None
            search_selectors = [
                '.tabs-component-search-input',
                '.tabs-component-search-input input',
                'input[type="search"]',
                'input[placeholder*="搜索"]',
                'input'
            ]
            
            for selector in search_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        try:
                            elem.click()
                            time.sleep(1)
                            
                            inp = elem
                            try:
                                inp = elem.find_element(By.CSS_SELECTOR, "input")
                            except:
                                pass
                            
                            inp.click()
                            time.sleep(0.5)
                            inp.clear()
                            time.sleep(0.5)
                            inp.send_keys(keyword)
                            search_input = inp
                            print("已在搜索框输入关键词: %s (使用选择器: %s)" % (keyword, selector))
                            break
                        except:
                            continue
                    if search_input:
                        break
                except Exception as e:
                    continue
            
            if not search_input:
                print("[虎扑-错误] 无法找到搜索框或输入关键词")
                return self.crawl_data
            
            time.sleep(2)
            
            print("正在点击搜索按钮...")
            search_button_selectors = [
                '.index_search-input-ask__aCEe7',
                'button[type="submit"]',
                '.search-btn',
                '[class*="search-btn"]'
            ]
            
            search_clicked = False
            for selector in search_button_selectors:
                try:
                    search_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    search_btn.click()
                    print("已点击搜索按钮 (选择器: %s)" % selector)
                    search_clicked = True
                    break
                except:
                    try:
                        search_input.send_keys('\n')
                        print("已通过回车键触发搜索")
                        search_clicked = True
                        break
                    except:
                        continue
            
            if not search_clicked:
                print("[虎扑-错误] 无法触发搜索")
                return self.crawl_data
            
            time.sleep(5)
            print("搜索完成，当前URL: %s" % self.driver.current_url)
            
            print("[虎扑-滚动] 开始预滚动加载更多帖子...")
            for i in range(5):
                print("[滚动] 正在滚动加载更多内容 (%d/5)..." % (i+1))
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
            print("[滚动] 滚动完成")
            
            print("从搜索结果页提取虎扑...")
            
            post_counter = 0
            processed_urls = []
            
            while post_counter < target_count:
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                post_selectors = [
                    '.index_title__Hc6QK',
                    '.index_search-result__Z0Q6G',
                    '[class*="index_title"]',
                    '[class*="search-result"]',
                    '.post-item',
                    '[class*="post-item"]'
                ]
                
                posts = []
                for selector in post_selectors:
                    try:
                        posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if posts:
                            print("使用选择器 %s 找到 %d 个虎扑卡片" % (selector, len(posts)))
                            break
                    except:
                        continue
                
                if not posts:
                    print("[虎扑-错误] 未找到帖子元素")
                    # 尝试滚动加载更多
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    continue
                
                # 遍历当前页面的所有帖子
                for idx, post in enumerate(posts):
                    if post_counter >= target_count:
                        break
                        
                    try:
                        print("\n正在处理第 %d 个虎扑卡片..." % idx)
                        
                        post_url = None
                        clicked_title = False
                        
                        try:
                            print("  尝试直接点击标题元素...")
                            post.click()
                            time.sleep(5)
                            post_url = self.driver.current_url
                            if post_url and ('hupu.com' in post_url or 'bbs' in post_url or 'thread' in post_url):
                                print("  点击成功，当前URL: %s" % post_url)
                                clicked_title = True
                        except Exception as e:
                            print("  点击标题失败: %s" % str(e))
                        
                        if not clicked_title:
                            try:
                                all_links = post.find_elements(By.TAG_NAME, 'a')
                                print("  该卡片有 %d 个链接" % len(all_links))
                                for link_idx, link in enumerate(all_links):
                                    try:
                                        href = link.get_attribute('href')
                                        text = link.text.strip()
                                        print("    链接 %d: %s (文本: %s)" % (link_idx, href, text[:30]))
                                        if href and ('hupu.com' in href or 'bbs' in href or 'thread' in href):
                                            post_url = href
                                            print("  找到虎扑链接: %s" % post_url)
                                            break
                                    except:
                                        continue
                            except Exception as e:
                                print("  获取链接失败: %s" % str(e))
                        
                        if not post_url and not clicked_title:
                            print("  未找到链接且点击失败，跳过该卡片")
                            continue
                        
                        if post_url in processed_urls:
                            print("  该链接已处理过，跳过")
                            continue
                        
                        print("\n=== 虎扑第%d条 ===" % (post_counter + 1))
                        print("虎扑链接: %s" % post_url)
                        
                        current_window = self.driver.current_window_handle
                        need_close_window = False
                        
                        if not clicked_title:
                            self.driver.execute_script("window.open('%s', '_blank');" % post_url)
                            time.sleep(2)
                            
                            all_windows = self.driver.window_handles
                            new_window = [w for w in all_windows if w != current_window][0]
                            self.driver.switch_to.window(new_window)
                            need_close_window = True
                            time.sleep(5)
                        else:
                            print("  已在帖子页面，无需打开新窗口")
                            time.sleep(2)
                        
                        post_data = {
                            "platform": "hupu",
                            "post_id": "hupu_%d_%d" % (post_counter, int(time.time())),
                            "content": "NULL",
                            "publish_time": "NULL",
                            "like_count": "NULL",
                            "comment_count": "NULL",
                            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "url": self.driver.current_url,
                            "comment_content": "NULL",
                            "comment_users": "NULL"
                        }
                        
                        try:
                            content_selectors = [
                                '.bbs-content-font',
                                '[class*="bbs-content"]',
                                '.thread-content',
                                '[class*="thread-content"]',
                                '.post-content',
                                '[class*="post-content"]',
                                '.content',
                                '[class*="content"]'
                            ]
                            for selector in content_selectors:
                                try:
                                    content_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    if content_elems:
                                        post_data["content"] = content_elems[0].text.strip().replace('\n', ' ').replace('\r', ' ')
                                        if post_data["content"]:
                                            break
                                except:
                                    continue
                            print("虎扑内容:")
                            print(post_data["content"])
                        except Exception as e:
                            print("提取内容失败: %s" % str(e))
                        
                        print("正在点击展开全部回复...")
                        try:
                            expand_selectors = [
                                '.expand-all-replies > span',
                                '.expand-all-replies',
                                '[class*="expand-all-replies"]',
                                '//span[contains(text(), "展开")]',
                                '//*[contains(text(), "查看全部回复")]'
                            ]
                            for expand_round in range(5):
                                expanded_any = False
                                for selector in expand_selectors:
                                    try:
                                        if selector.startswith('//'):
                                            elem = self.driver.find_element(By.XPATH, selector)
                                        else:
                                            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                        time.sleep(1)
                                        elem.click()
                                        print("已点击展开回复 (第%d轮)" % (expand_round + 1))
                                        time.sleep(3)
                                        expanded_any = True
                                        break
                                    except:
                                        continue
                                if not expanded_any:
                                    break
                        except:
                            pass
                        
                        print("正在滚动加载评论...")
                        last_height = 0
                        same_count = 0
                        for i in range(100):
                            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(2)
                            try:
                                new_height = self.driver.execute_script("return document.body.scrollHeight")
                                if new_height == last_height:
                                    same_count += 1
                                    if same_count >= 10:
                                        break
                                else:
                                    same_count = 0
                                    last_height = new_height
                            except:
                                pass
                        print("滚动完成")
                        
                        try:
                            more_selectors = [
                                '//a[contains(text(), "下一页")]',
                                '//span[contains(text(), "下一页")]',
                                '//button[contains(text(), "下一页")]'
                            ]
                            for page_round in range(10):
                                clicked_any = False
                                for selector in more_selectors:
                                    try:
                                        elem = self.driver.find_element(By.XPATH, selector)
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                        time.sleep(1)
                                        elem.click()
                                        print("点击了下一页 (第%d页)" % (page_round + 2))
                                        time.sleep(3)
                                        clicked_any = True
                                        for i in range(50):
                                            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                            time.sleep(2)
                                        break
                                    except:
                                        continue
                                if not clicked_any:
                                    break
                        except:
                            pass
                        
                        comments_data = []
                        try:
                            print("正在使用DOM方式提取评论...")
                            comments_data = self._extract_comments_from_dom()
                            if comments_data is not None:
                                print("DOM方式提取到 %d 条评论" % len(comments_data))
                            
                            if comments_data is None or len(comments_data) == 0:
                                print("DOM方式未提取到评论，尝试文本方式...")
                                seen_texts = set()
                                try:
                                    all_text = self.driver.find_element(By.TAG_NAME, 'body').text
                                    lines = all_text.split('\n')
                                    print("页面文本行数: %d" % len(lines))
                                    
                                    comment_start_idx = 0
                                    for idx, line in enumerate(lines):
                                        line = line.strip()
                                        if '回复' in line or '楼' in line and len(line) < 20:
                                            comment_start_idx = idx + 1
                                            print("找到评论区起始位置: 第%d行" % comment_start_idx)
                                            break
                                    
                                    i = comment_start_idx
                                    while i < len(lines):
                                        line = lines[i].strip()
                                        if not line or len(line) < 2:
                                            i += 1
                                            continue
                                        
                                        filter_words = ['回复', '赞', '踩', '查看', '更多', '收起', '删除', '举报', '分享', '楼', '层']
                                        should_skip = False
                                        for word in filter_words:
                                            if word in line and len(line) < 30:
                                                should_skip = True
                                                break
                                        
                                        if should_skip:
                                            i += 1
                                            continue
                                        
                                        if line and len(line) > 3 and line not in seen_texts:
                                            user_name = "未知用户"
                                            comment_content = line
                                            
                                            if ':' in line or '：' in line:
                                                parts = line.split(':', 1)
                                                if len(parts) == 2 and len(parts[0]) < 30 and len(parts[0]) > 1:
                                                    user_name = parts[0].strip()
                                                    comment_content = parts[1].strip()
                                                    if not comment_content and i + 1 < len(lines):
                                                        comment_content = lines[i + 1].strip()
                                                        i += 1
                                            
                                            if comment_content and len(comment_content) > 1:
                                                comments_data.append({"user": user_name, "content": comment_content})
                                                seen_texts.add(line)
                                        
                                        i += 1
                                    
                                    print("文本方式共提取到 %d 条有效评论" % len(comments_data))
                                except Exception as e2:
                                    print("文本方式提取评论也失败: %s" % str(e2))
                            
                            print("最终提取到 %d 条有效评论" % len(comments_data))
                            
                            if comments_data:
                                for c in comments_data:
                                    comment_row = post_data.copy()
                                    comment_row["comment_content"] = c["content"]
                                    comment_row["comment_users"] = c["user"]
                                    self.crawl_data.append(comment_row)
                                print("已保存 %d 条评论" % len(comments_data))
                            else:
                                self.crawl_data.append(post_data)
                                print("未找到评论，保存虎扑本身")
                        except Exception as e:
                            print("提取评论失败: %s" % str(e))
                            self.crawl_data.append(post_data)
                        
                        if need_close_window:
                            self.driver.close()
                            self.driver.switch_to.window(current_window)
                        else:
                            # 如果是直接点击进入的，需要返回搜索结果页
                            self.driver.back()
                            time.sleep(3)
                        
                        processed_urls.append(post_url)
                        post_counter += 1
                        print("\n完成虎扑 %d/%d" % (post_counter, target_count))
                        time.sleep(random.uniform(2, 4))
                    except Exception as e:
                        print("处理虎扑失败: %s" % str(e))
                        try:
                            all_windows = self.driver.window_handles
                            if len(all_windows) > 1:
                                for w in all_windows[1:]:
                                    self.driver.switch_to.window(w)
                                    self.driver.close()
                                self.driver.switch_to.window(all_windows[0])
                            else:
                                # 如果只有一个窗口，尝试返回搜索结果页
                                self.driver.back()
                                time.sleep(3)
                        except:
                            pass
                        continue
                
                # 滚动加载更多帖子
                print("正在加载更多虎扑...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)
            
            print("\n=== 爬取完成 ===")
            print("共爬取 %d 条虎扑" % post_counter)
            print("共保存 %d 条数据（含评论）" % len(self.crawl_data))
            return self.crawl_data
            
        except Exception as e:
            print("[虎扑-致命错误] 爬取中断：%s" % str(e))
            return self.crawl_data
    
    def save_comments_to_csv(self, hupu_data, keyword):
        try:
            raw_dir = os.path.join(self.project_root, "data", "raw")
            date_str = datetime.now().strftime("%Y%m%d")
            csv_path = os.path.join(raw_dir, "hupu_raw_%s_%s.csv" % (keyword, date_str))
            
            base_fields = [
                "platform", "post_id", "content", "publish_time", 
                "like_count", "comment_count", "crawl_time", "url", 
                "comment_content", "comment_users"
            ]
            
            if os.path.exists(csv_path):
                os.remove(csv_path)
                print("[格式规范] 已删除旧的CSV文件，避免重复数据")
            
            import csv
            with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=base_fields)
                writer.writeheader()
                
                for row in hupu_data:
                    formatted_row = {}
                    for field in base_fields:
                        value = row.get(field, "NULL")
                        if value is None or value == "":
                            value = "NULL"
                        formatted_row[field] = value
                    writer.writerow(formatted_row)
            
            print("[格式规范] 已保存%d条数据到%s，格式符合规范" % (len(hupu_data), csv_path))
            
            return csv_path
            
        except Exception as e:
            print("保存数据失败: %s" % str(e))
            return None
    
    def close(self):
        try:
            if self.driver:
                self.driver.quit()
                print("[虎扑-结束] 驱动已关闭")
        except Exception as e:
            print("关闭浏览器失败: %s" % str(e))


if __name__ == "__main__":
    print("=" * 80)
    print("虎扑爬虫测试 - 简单版")
    print("=" * 80)
    
    try:
        spider = HupuSpider(headless=False)
        
        keyword = "上海迪士尼"
        print("测试爬取关键词: %s" % keyword)
        print("目标爬取虎扑数: 20条（以获取约100条评论）")
        
        hupu_data = spider.crawl(keyword, target_count=20)
        
        csv_path = None
        if hupu_data:
            print("\n爬取成功！共获取 %d 条数据（每条评论单独一行）" % len(hupu_data))
            print("\n=== 爬取的数据预览（前10条） ===")
            for i, data in enumerate(hupu_data[:10]):
                print("\n--- 第%d条数据 ---" % (i+1))
                content_preview = data['content'][:80] if len(data['content']) > 80 else data['content']
                print("虎扑内容: %s..." % content_preview)
                print("评论用户: %s" % data['comment_users'])
                print("评论内容: %s" % data['comment_content'])
            
            csv_path = spider.save_comments_to_csv(hupu_data, keyword)
            if csv_path:
                print("\n" + "=" * 80)
                print("📁 数据已成功保存！")
                print("📂 文件路径: %s" % csv_path)
                print("=" * 80)
        else:
            print("未获取到数据")
        
        print("\n⏰ 浏览器窗口将保持打开10秒，让你查看...")
        time.sleep(10)
        print("⏰ 10秒到了，准备关闭浏览器...")
            
    finally:
        if 'spider' in locals():
            spider.close()
        
        print("\n" + "=" * 80)
        print("虎扑爬虫测试完成！")
        print("=" * 80)

