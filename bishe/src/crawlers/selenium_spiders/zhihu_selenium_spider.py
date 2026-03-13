
# -*- coding: utf-8 -*-
"""
知乎爬虫模块 - 符合数据格式规范
基于微博爬虫的成功经验重构
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
sys.path.insert(0, os.path.dirname(project_root))

from src.crawlers.selenium_spiders.common import init_csv_header, format_time_str, format_numeric_value, save_to_csv_standard


class ZhihuSpider:
    """知乎爬虫"""
    
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
        self.cookie_path = os.path.join(self.project_root, "data", "zhihu_cookies.json")
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
        print("\n=== 开始处理知乎登录 ===")
        
        if os.path.exists(self.cookie_path):
            try:
                import json
                self.driver.get("https://www.zhihu.com/404")
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
                self.driver.get("https://www.zhihu.com")
                self.driver.refresh()
                time.sleep(3)
                
                if "zhihu.com" in self.driver.current_url:
                    print("使用已保存的 Cookie 登录成功！无需扫码！")
                    return True
            except Exception as e:
                print("Cookie加载失败: %s" % str(e))
        
        print("本地Cookie无效/未找到，请在浏览器中登录知乎")
        print("请在弹出的浏览器窗口中完成登录，登录后请等待页面跳转到主页...")
        
        self._safe_get("https://www.zhihu.com/signin")
        
        login_success = False
        wait_time = 0
        max_wait = 120
        
        while wait_time < max_wait:
            try:
                if "zhihu.com" in self.driver.current_url and "signin" not in self.driver.current_url.lower():
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
                '.CommentItem',
                '[class*="CommentItem"]',
                '[class*="comment-item"]',
                '.List-item',
                '.CommentList-item',
                '[class*="CommentList"] > div',
                '.CommentsV2-comment',
                '[class*="Comment"]',
                '.AnswerItem-comment',
                '[class*="AnswerItem"] [class*="comment"]'
            ]
            
            user_name_selectors = [
                '.UserLink-link',
                '.AuthorInfo-name',
                '[class*="AuthorInfo"] [class*="name"]',
                'a[href*="/people/"]',
                '.CommentItem-author',
                '[class*="CommentItem"] [class*="author"]',
                '[class*="comment"] [class*="author"]'
            ]
            
            comment_content_selectors = [
                '.RichContent',
                '.CommentItem-content',
                '[class*="CommentItem"] [class*="content"]',
                '[class*="comment"] [class*="content"]',
                '.CommentItem-body',
                '[class*="CommentItem"] [class*="body"]',
                '.RichText',
                '[class*="RichText"]'
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
                        filter_words = ['回复', '赞', '踩', '评论', '查看', '更多', '收起', '删除', '举报', '分享']
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
        """爬取知乎内容"""
        print(f"\n开始爬取知乎：{keyword}")
        
        try:
            search_url = f"https://www.zhihu.com/search?q={keyword}&type=content"
            print(f"正在搜索: {search_url}")
            if not self._safe_get(search_url):
                print("[知乎-错误] 无法访问搜索页面")
                return self.crawl_data
            
            print("[知乎-滚动] 开始预滚动加载更多帖子...")
            for i in range(5):
                print("[滚动] 正在滚动加载更多内容 (%d/5)..." % (i+1))
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
            print("[滚动] 滚动完成")
            
            print("从搜索结果页提取知乎...")
            
            post_counter = 0
            comment_counter = 0
            target_comments = target_count * 20
            processed_urls = []
            
            while comment_counter < target_comments and post_counter < target_count:
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                post_selectors = [
                    '.ContentItem',
                    '[class*="ContentItem"]',
                    '.List-item'
                ]
                
                posts = []
                for selector in post_selectors:
                    try:
                        posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if posts:
                            print("使用选择器 %s 找到 %d 个知乎卡片" % (selector, len(posts)))
                            break
                    except:
                        continue
                
                if not posts:
                    print("[知乎-错误] 未找到帖子元素")
                    break
                
                # 遍历当前页面的所有帖子
                for idx, post in enumerate(posts):
                    if post_counter >= target_count:
                        break
                        
                    try:
                        print("\n正在处理第 %d 个知乎卡片..." % idx)
                        
                        post_url = None
                        
                        try:
                            all_links = post.find_elements(By.TAG_NAME, 'a')
                            print("  该卡片有 %d 个链接" % len(all_links))
                            for link_idx, link in enumerate(all_links):
                                try:
                                    href = link.get_attribute('href')
                                    text = link.text.strip()
                                    print("    链接 %d: %s (文本: %s)" % (link_idx, href, text[:30]))
                                    if href and ('zhihu.com/question/' in href or 'zhihu.com/answer/' in href):
                                        post_url = href
                                        print("  找到知乎链接: %s" % post_url)
                                        break
                                except:
                                    continue
                        except Exception as e:
                            print("  获取链接失败: %s" % str(e))
                        
                        if not post_url:
                            print("  未找到链接，跳过该卡片")
                            continue
                        
                        if post_url in processed_urls:
                            print("  该链接已处理过，跳过")
                            continue
                        
                        print("\n=== 知乎第%d条 ===" % (post_counter + 1))
                        print("知乎链接: %s" % post_url)
                        
                        current_window = self.driver.current_window_handle
                        
                        self.driver.execute_script("window.open('%s', '_blank');" % post_url)
                        time.sleep(2)
                        
                        all_windows = self.driver.window_handles
                        new_window = [w for w in all_windows if w != current_window][0]
                        self.driver.switch_to.window(new_window)
                        
                        time.sleep(5)
                        
                        post_data = {
                            "platform": "zhihu",
                            "post_id": "zhihu_%d_%d" % (post_counter, int(time.time())),
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
                                '.RichContent',
                                '.QuestionHeader-title',
                                '.AnswerItem-content',
                                '[class*="RichContent"]'
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
                            print("知乎内容:")
                            print(post_data["content"])
                        except Exception as e:
                            print("提取内容失败: %s" % str(e))
                        
                        try:
                            view_all_selectors = [
                                'a.QuestionMainAction.ViewAll-QuestionMainAction',
                                'a.ViewAll-QuestionMainAction',
                                'a[class*="ViewAll"]',
                                '//a[contains(@class, "ViewAll")]',
                                '//a[contains(text(), "查看全部")]',
                                '//a[contains(text(), "个回答")]'
                            ]
                            clicked_view_all = False
                            for selector in view_all_selectors:
                                try:
                                    if selector.startswith('//'):
                                        elems = self.driver.find_elements(By.XPATH, selector)
                                    else:
                                        elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    if elems:
                                        elem = elems[0]
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                        time.sleep(1)
                                        elem.click()
                                        print("点击了'查看全部回答'按钮")
                                        time.sleep(3)
                                        clicked_view_all = True
                                        break
                                except Exception as e:
                                    continue
                            if not clicked_view_all:
                                print("未找到'查看全部回答'按钮，继续处理当前页面")
                            
                            try:
                                close_selectors = [
                                    'button.Modal-closeButton',
                                    'button[aria-label="关闭"]',
                                    'button.Button--plain.Modal-closeButton',
                                    '//button[contains(@class, "Modal-closeButton")]',
                                    '//button[@aria-label="关闭"]',
                                    '//button[contains(@aria-label, "关闭")]'
                                ]
                                for selector in close_selectors:
                                    try:
                                        if selector.startswith('//'):
                                            close_elems = self.driver.find_elements(By.XPATH, selector)
                                        else:
                                            close_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                        if close_elems:
                                            close_elems[0].click()
                                            print("关闭了弹窗")
                                            time.sleep(1)
                                            break
                                    except:
                                        continue
                            except Exception as e:
                                print("关闭弹窗失败: %s" % str(e))
                        except Exception as e:
                            print("点击'查看全部回答'失败: %s" % str(e))
                        
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
                        
                        comments_data = []
                        try:
                            print("正在提取所有回答和评论...")
                            
                            answer_selectors = [
                                '.List-item',
                                '.AnswerItem',
                                '[class*="AnswerItem"]',
                                '.ContentItem'
                            ]
                            
                            all_answers = []
                            for selector in answer_selectors:
                                try:
                                    all_answers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    if all_answers and len(all_answers) > 0:
                                        print("找到 %d 个回答" % len(all_answers))
                                        break
                                except:
                                    continue
                            
                            if not all_answers:
                                print("未找到回答，尝试提取整个页面评论...")
                                comments_data = self._extract_comments_from_dom()
                            else:
                                for answer_idx, answer in enumerate(all_answers):
                                    try:
                                        print("\n--- 处理第 %d 个回答 ---" % (answer_idx + 1))
                                        
                                        answer_content = "NULL"
                                        try:
                                            content_selectors = [
                                                '.RichContent',
                                                '.RichText',
                                                '[class*="RichContent"]',
                                                '[class*="RichText"]'
                                            ]
                                            for selector in content_selectors:
                                                try:
                                                    content_elem = answer.find_element(By.CSS_SELECTOR, selector)
                                                    answer_content = content_elem.text.strip().replace('\n', ' ').replace('\r', ' ')
                                                    if answer_content:
                                                        break
                                                except:
                                                    continue
                                        except:
                                            pass
                                        
                                        if answer_content and answer_content != "NULL":
                                            print("回答内容: %s..." % answer_content[:100])
                                        
                                        try:
                                            comment_items = answer.find_elements(By.CSS_SELECTOR, '.CommentItem, [class*="CommentItem"], [class*="comment"]')
                                            print("该回答有 %d 条评论" % len(comment_items))
                                            
                                            for comment in comment_items:
                                                try:
                                                    user_name = "未知用户"
                                                    comment_content = ""
                                                    
                                                    try:
                                                        user_elem = comment.find_element(By.CSS_SELECTOR, '.UserLink-link, .AuthorInfo-name, a[href*="/people/"], [class*="author"]')
                                                        user_name = user_elem.text.strip()
                                                    except:
                                                        pass
                                                    
                                                    try:
                                                        content_elem = comment.find_element(By.CSS_SELECTOR, '.RichContent, .RichText, [class*="content"], [class*="body"]')
                                                        comment_content = content_elem.text.strip().replace('\n', ' ').replace('\r', ' ')
                                                    except:
                                                        pass
                                                    
                                                    if comment_content and len(comment_content) > 1:
                                                        comments_data.append({
                                                            "user": user_name,
                                                            "content": comment_content,
                                                            "answer": answer_content[:200] if answer_content else "NULL"
                                                        })
                                                        print("  评论: %s - %s" % (user_name, comment_content[:50]))
                                                except:
                                                    continue
                                        except:
                                            pass
                                    except Exception as e:
                                        print("处理回答失败: %s" % str(e))
                                        continue
                            
                            print("\n共提取到 %d 条评论" % len(comments_data))
                            
                            if len(comments_data) == 0:
                                print("DOM方式未提取到评论，尝试文本方式...")
                                seen_texts = set()
                                try:
                                    all_text = self.driver.find_element(By.TAG_NAME, 'body').text
                                    lines = all_text.split('\n')
                                    print("页面文本行数: %d" % len(lines))
                                    
                                    comment_start_idx = 0
                                    for idx, line in enumerate(lines):
                                        line = line.strip()
                                        if '全部评论' in line or '评论' in line and len(line) < 10:
                                            comment_start_idx = idx + 1
                                            print("找到评论区起始位置: 第%d行" % comment_start_idx)
                                            break
                                    
                                    i = comment_start_idx
                                    while i < len(lines):
                                        line = lines[i].strip()
                                        if not line or len(line) < 2:
                                            i += 1
                                            continue
                                        
                                        filter_words = ['回复', '赞', '踩', '查看', '更多', '收起', '删除', '举报', '分享']
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
                                    comment_row["comment_content"] = c.get("content", "NULL")
                                    comment_row["comment_users"] = c.get("user", "未知用户")
                                    if c.get("answer"):
                                        comment_row["content"] = c.get("answer", post_data["content"])
                                    self.crawl_data.append(comment_row)
                                comment_counter += len(comments_data)
                                print("已保存 %d 条评论，累计 %d 条" % (len(comments_data), comment_counter))
                            else:
                                self.crawl_data.append(post_data)
                                print("未找到评论，保存知乎本身")
                        except Exception as e:
                            print("提取评论失败: %s" % str(e))
                            self.crawl_data.append(post_data)
                        
                        self.driver.close()
                        self.driver.switch_to.window(current_window)
                        
                        processed_urls.append(post_url)
                        post_counter += 1
                        print("\n完成知乎 %d/%d，评论累计 %d/%d" % (post_counter, target_count, comment_counter, target_comments))
                        
                        if comment_counter >= target_comments:
                            print("已达到目标评论数，停止爬取")
                            break
                        time.sleep(random.uniform(2, 4))
                    except Exception as e:
                        print("处理知乎失败: %s" % str(e))
                        try:
                            all_windows = self.driver.window_handles
                            if len(all_windows) > 1:
                                for w in all_windows[1:]:
                                    self.driver.switch_to.window(w)
                                    self.driver.close()
                                self.driver.switch_to.window(all_windows[0])
                        except:
                            pass
                        continue
                
                # 滚动加载更多帖子
                print("正在加载更多知乎...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)
            
            print("\n=== 爬取完成 ===")
            print("共爬取 %d 条知乎" % post_counter)
            print("共保存 %d 条数据（含评论）" % len(self.crawl_data))
            return self.crawl_data
            
        except Exception as e:
            print("[知乎-致命错误] 爬取中断：%s" % str(e))
            return self.crawl_data
    
    def save_comments_to_csv(self, zhihu_data, keyword):
        try:
            raw_dir = os.path.join(self.project_root, "data", "raw")
            date_str = datetime.now().strftime("%Y%m%d")
            csv_path = os.path.join(raw_dir, "zhihu_raw_%s_%s.csv" % (keyword, date_str))
            
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
                
                for row in zhihu_data:
                    formatted_row = {}
                    for field in base_fields:
                        value = row.get(field, "NULL")
                        if value is None or value == "":
                            value = "NULL"
                        formatted_row[field] = value
                    writer.writerow(formatted_row)
            
            print(f"[格式规范] 已保存{len(zhihu_data)}条数据到{csv_path}，格式符合规范")
            
            return csv_path
            
        except Exception as e:
            print("保存数据失败: %s" % str(e))
            return None
    
    def close(self):
        try:
            if self.driver:
                self.driver.quit()
                print("[知乎-结束] 驱动已关闭")
        except Exception as e:
            print("关闭浏览器失败: %s" % str(e))


if __name__ == "__main__":
    print("=" * 80)
    print("知乎爬虫测试 - 简单版")
    print("=" * 80)
    
    try:
        spider = ZhihuSpider(headless=False)
        
        keyword = "北京环球影城"
        print("测试爬取关键词: %s" % keyword)
        print("目标爬取知乎数: 30条（以获取更多评论）")
        
        zhihu_data = spider.crawl(keyword, target_count=30)
        
        csv_path = None
        if zhihu_data:
            print("\n爬取成功！共获取 %d 条数据（每条评论单独一行）" % len(zhihu_data))
            print("\n=== 爬取的数据预览（前10条） ===")
            for i, data in enumerate(zhihu_data[:10]):
                print("\n--- 第%d条数据 ---" % (i+1))
                content_preview = data['content'][:80] if len(data['content']) > 80 else data['content']
                print("知乎内容: %s..." % content_preview)
                print("评论用户: %s" % data['comment_users'])
                print("评论内容: %s" % data['comment_content'])
            
            csv_path = spider.save_comments_to_csv(zhihu_data, keyword)
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
        print("知乎爬虫测试完成！")
        print("=" * 80)
