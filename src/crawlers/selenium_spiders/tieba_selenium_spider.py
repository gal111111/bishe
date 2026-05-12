
# -*- coding: utf-8 -*-
"""
贴吧爬虫模块 - 基于微博/知乎爬虫的成功经验重构
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
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.crawlers.selenium_spiders.common import init_csv_header, format_time_str, format_numeric_value, save_to_csv_standard


class TiebaSpider:
    """贴吧爬虫"""
    
    def __init__(self, headless=False):
        self.project_root = project_root
        self.headless = headless
        self.chrome_options = Options()
        
        # 添加更多的反检测参数
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        self.chrome_options.add_experimental_option("useAutomationExtension", False)
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        if self.headless:
            self.chrome_options.add_argument("--headless=new")
        
        # 使用项目目录下的ChromeDriver
        chromedriver_path = os.path.join(self.project_root, "drivers", "chromedriver")
        service = Service(chromedriver_path)
        
        # 尝试创建driver，最多重试3次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
                # 执行一个简单的页面访问来验证driver是否正常
                self.driver.get("https://www.baidu.com")
                print(f"✅ 贴吧爬虫 driver 创建成功 (尝试 {attempt+1}/{max_retries})")
                break
            except Exception as e:
                print(f"❌ 贴吧爬虫 driver 创建失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
        self.wait = WebDriverWait(self.driver, 15)
        self.long_wait = WebDriverWait(self.driver, 30)
        self.crawl_data = []
        self.cookie_path = os.path.join(self.project_root, "data", "tieba_cookies.json")
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
        print("\n=== 开始处理贴吧登录 ===")
        
        if os.path.exists(self.cookie_path):
            try:
                import json
                print("正在加载已保存的Cookie...")
                # 先访问贴吧主页
                self.driver.get("https://tieba.baidu.com")
                time.sleep(3)
                
                with open(self.cookie_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                
                print(f"从文件中加载了 {len(cookies)} 个Cookie")
                
                added_count = 0
                for cookie in cookies:
                    cookie_copy = cookie.copy()
                    # 只删除可能导致问题的字段
                    for key in ['sameSite', 'expiry', 'httpOnly', 'secure']:
                        if key in cookie_copy:
                            del cookie_copy[key]
                    try:
                        self.driver.add_cookie(cookie_copy)
                        added_count += 1
                        print(f"✅ 添加Cookie: {cookie.get('name', 'unknown')}")
                    except Exception as e:
                        print(f"❌ 跳过Cookie添加失败: {cookie.get('name', 'unknown')}, 错误: {e}")
                        continue
                
                print(f"\n已成功加载 {added_count}/{len(cookies)} 个Cookie")
                
                # 重新访问贴吧主页以应用cookie
                print("正在重新访问贴吧主页验证登录...")
                self.driver.get("https://tieba.baidu.com")
                time.sleep(10)  # 增加等待时间
                
                print("\n=== 详细登录状态检查 ===")
                current_url = self.driver.current_url
                page_title = self.driver.title
                print(f"当前URL: {current_url}")
                print(f"页面标题: {page_title}")
                
                # 获取当前cookie状态
                current_cookies = self.driver.get_cookies()
                print(f"当前浏览器中的Cookie数量: {len(current_cookies)}")
                key_cookies = ['BDUSS', 'STOKEN', 'TIEBA_SID']
                for key in key_cookies:
                    found = any(c['name'] == key for c in current_cookies)
                    print(f"  {key}: {'✅ 存在' if found else '❌ 缺失'}")
                
                # 检查页面内容
                page_source = self.driver.page_source
                
                # 检查是否真的登录成功 - 多种验证方式
                is_logged_in = False
                
                # 方式1: 检查关键cookie是否存在
                try:
                    cookie_names = [c['name'] for c in current_cookies]
                    if 'BDUSS' in cookie_names:
                        print("✅ 关键Cookie验证通过：找到 BDUSS")
                        is_logged_in = True
                    elif 'STOKEN' in cookie_names:
                        print("✅ 关键Cookie验证通过：找到 STOKEN")
                        is_logged_in = True
                    elif 'TIEBA_SID' in cookie_names:
                        print("✅ 关键Cookie验证通过：找到 TIEBA_SID")
                        is_logged_in = True
                    else:
                        print("❌ 关键Cookie验证失败：未找到 BDUSS、STOKEN 或 TIEBA_SID")
                except Exception as e:
                    print(f"❌ 检查Cookie时出错: {e}")
                
                # 方式2: 检查页面内容（更严格的检查）
                if not is_logged_in:
                    logged_in_indicators = [
                        '退出登录',
                        '我的贴吧',
                        '我的收藏',
                        '我的帖子',
                        '用户中心'
                    ]
                    
                    found_indicators = []
                    for indicator in logged_in_indicators:
                        if indicator in page_source:
                            found_indicators.append(indicator)
                    
                    if found_indicators:
                        print(f"✅ 页面元素验证通过：找到 {found_indicators}")
                        is_logged_in = True
                    else:
                        print("❌ 页面元素验证失败：未找到登录后元素")
                
                # 方式3: 检查是否有登录后的用户元素
                if not is_logged_in:
                    try:
                        user_elements = self.driver.find_elements(By.CSS_SELECTOR, ".user_name, .head_pic, .j_user_card, .u_avatar, .user_info")
                        if user_elements:
                            print(f"✅ 用户元素验证通过：找到 {len(user_elements)} 个用户元素")
                            is_logged_in = True
                        else:
                            print("❌ 用户元素验证失败：未找到用户元素")
                    except Exception as e:
                        print(f"检查用户元素时出错: {e}")
                
                # 方式4: 检查页面是否显示登录按钮
                try:
                    login_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="login"]')
                    if login_buttons:
                        print("❌ 页面仍显示登录链接，未登录")
                        is_logged_in = False
                    else:
                        print("✅ 页面未显示登录链接，可能已登录")
                except Exception as e:
                    print(f"检查登录按钮时出错: {e}")
                
                if is_logged_in:
                    print("\n🎉 使用已保存的 Cookie 登录成功！无需扫码！")
                    return True
                else:
                    print("\n⚠️ Cookie登录失败，需要重新登录")
                    print("可能原因：")
                    print("1. Cookie已过期")
                    print("2. Cookie加载不正确")
                    print("3. 百度检测到自动化登录")
                    
            except Exception as e:
                print(f"\n❌ Cookie加载失败: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n请在弹出的浏览器窗口中登录贴吧")
        print("请完成登录后等待页面跳转到主页...")
        
        self._safe_get("https://tieba.baidu.com/")
        
        login_success = False
        wait_time = 0
        max_wait = 300  # 增加等待时间到5分钟
        
        print("等待登录... (最多等待5分钟)")
        while wait_time < max_wait:
            try:
                page_source = self.driver.page_source
                # 检查登录成功的标志
                if any(indicator in page_source for indicator in ['我的贴吧', '我的收藏', '我的帖子', '退出登录']):
                    login_success = True
                    break
            except Exception:
                pass
            
            time.sleep(3)
            wait_time += 3
            if wait_time % 30 == 0:
                print(f"等待登录中...({wait_time}/{max_wait}秒)")
        
        if not login_success:
            print("❌ 登录超时，请重新运行程序并及时登录")
            return False
        
        print("✅ 登录验证成功！正在保存Cookie...")
        try:
            import json
            cookies = self.driver.get_cookies()
            with open(self.cookie_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print(f"✅ Cookie 已保存到：{self.cookie_path}")
        except Exception as e:
            print(f"❌ Cookie保存失败: {e}")
        
        return True
    
    def _extract_comments_from_dom(self):
        comments_data = []
        seen_texts = set()
        
        try:
            comment_container_selectors = [
                '.d_post_content',
                '[class*="d_post_content"]',
                '.l_post',
                '[class*="l_post"]',
                '.post_content',
                '[class*="post_content"]'
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
                '.d_post_content',
                '[class*="d_post_content"]',
                '.post_content',
                '[class*="post_content"]',
                '.j_d_post_content',
                '[class*="j_d_post_content"]'
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
        """爬取贴吧内容"""
        print("\n开始爬取贴吧：%s" % keyword)
        
        try:
            import urllib.parse
            # 直接访问"上海迪士尼吧"，而不是全局搜索
            encoded_keyword = urllib.parse.quote(keyword)
            # 先尝试直接访问贴吧
            tieba_url = "https://tieba.baidu.com/f?kw=%s" % encoded_keyword
            print("正在访问贴吧主页: %s" % tieba_url)
            if not self._safe_get(tieba_url):
                print("[贴吧-警告] 无法访问贴吧主页，尝试搜索页面")
                # 如果直接访问失败，再使用搜索
                search_url = "https://tieba.baidu.com/f/search/res?ie=utf-8&qw=%s" % encoded_keyword
                print("正在搜索: %s" % search_url)
                if not self._safe_get(search_url):
                    print("[贴吧-错误] 无法访问搜索页面")
                    return self.crawl_data
            
            print("[贴吧-滚动] 开始预滚动加载更多帖子...")
            for i in range(5):
                print("[滚动] 正在滚动加载更多内容 (%d/5)..." % (i+1))
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
            print("[滚动] 滚动完成")
            
            print("从搜索结果页提取贴吧...")
            
            post_counter = 0
            processed_urls = []
            max_loops = 10  # 最大循环次数，避免死循环
            loop_count = 0
            
            while post_counter < target_count and loop_count < max_loops:
                loop_count += 1
                print(f"\n=== 循环 {loop_count}/{max_loops} ===")
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                post_selectors = [
                    '.j_thread_list',
                    '[class*="j_thread_list"]',
                    '.threadlist_title',
                    '[class*="threadlist_title"]',
                    '.threadlist_item',
                    '[class*="threadlist_item"]',
                    '.tl_shadow',
                    '[class*="tl_shadow"]',
                    '.t_con',
                    '[class*="t_con"]',
                    '.thread_con',
                    '[class*="thread_con"]',
                    '.pb_list_p',
                    '[class*="pb_list_p"]',
                    '.forum_list',
                    '[class*="forum_list"]',
                    '.threadlist_text',
                    '[class*="threadlist_text"]',
                    'a[href*="/p/"]',
                    '.l_post',
                    '[class*="l_post"]',
                    '.core_title',
                    '[class*="core_title"]',
                    '.post_content',
                    '[class*="post_content"]',
                    '.d_post_content',
                    '[class*="d_post_content"]',
                    '.topic-content'
                ]
                
                posts = []
                for selector in post_selectors:
                    try:
                        posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if posts:
                            print("使用选择器 %s 找到 %d 个贴吧卡片" % (selector, len(posts)))
                            # 尝试直接从页面查找所有帖子链接
                            if len(posts) > 0:
                                break
                    except Exception as e:
                        print("选择器 %s 错误: %s" % (selector, e))
                        continue
                
                # 如果没有找到帖子元素，尝试直接查找所有/p/链接
                if not posts:
                    print("[贴吧-调试] 尝试直接查找所有/p/链接")
                    try:
                        all_links = self.driver.find_elements(By.TAG_NAME, 'a')
                        print("[贴吧-调试] 找到 %d 个链接" % len(all_links))
                        post_links = []
                        for link in all_links:
                            try:
                                href = link.get_attribute('href')
                                if href and '/p/' in href and 'tieba.baidu.com' in href:
                                    post_links.append(href)
                                    print("[贴吧-调试] 找到帖子链接: %s" % href)
                            except:
                                continue
                        if post_links:
                            print("[贴吧-调试] 找到 %d 个帖子链接" % len(post_links))
                            # 直接使用链接列表作为帖子
                            posts = post_links
                    except Exception as e:
                        print("[贴吧-错误] 查找链接失败: %s" % e)
                
                if not posts:
                    print("[贴吧-错误] 未找到帖子元素")
                    break
                
                found = False
                for idx, post in enumerate(posts):
                    try:
                        print("\n正在处理第 %d 个贴吧卡片..." % idx)
                        
                        post_url = None
                        
                        # 检查post是元素还是字符串链接
                        if isinstance(post, str):
                            # 如果是直接的链接字符串
                            post_url = post
                            print("  直接使用找到的链接: %s" % post_url)
                        else:
                            # 先检查这个元素本身是不是链接
                            try:
                                href = post.get_attribute('href')
                                if href and 'tieba.baidu.com/p/' in href:
                                    post_url = href
                                    print("  元素本身就是链接: %s" % post_url)
                            except:
                                pass
                            
                            # 如果不是，再尝试从元素中查找链接
                            if not post_url:
                                try:
                                    all_links = post.find_elements(By.TAG_NAME, 'a')
                                    print("  该卡片有 %d 个链接" % len(all_links))
                                    for link_idx, link in enumerate(all_links):
                                        try:
                                            href = link.get_attribute('href')
                                            text = link.text.strip()
                                            print("    链接 %d: %s (文本: %s)" % (link_idx, href, text[:30]))
                                            if href and 'tieba.baidu.com/p/' in href:
                                                post_url = href
                                                print("  找到贴吧链接: %s" % post_url)
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
                        
                        print("\n=== 贴吧第%d条 ===" % (post_counter + 1))
                        print("贴吧链接: %s" % post_url)
                        
                        # 既然我们已经在"上海迪士尼吧"了，就不需要检查URL了
                        # 直接处理，后面检查页面内容是否相关
                        
                        current_window = self.driver.current_window_handle
                        print(f"当前窗口句柄: {current_window}")
                        
                        # 安全地打开新窗口
                        try:
                            self.driver.execute_script("window.open(arguments[0], '_blank');", post_url)
                            time.sleep(3)
                            
                            # 获取所有窗口句柄
                            all_windows = self.driver.window_handles
                            print(f"所有窗口句柄: {all_windows}")
                            
                            # 找到新窗口
                            new_windows = [w for w in all_windows if w != current_window]
                            if not new_windows:
                                print("错误: 没有找到新窗口")
                                continue
                            
                            new_window = new_windows[0]
                            print(f"切换到新窗口: {new_window}")
                            self.driver.switch_to.window(new_window)
                            
                            # 等待页面加载
                            time.sleep(5)
                        except Exception as e:
                            print(f"打开新窗口失败: {e}")
                            # 清理可能打开的窗口
                            try:
                                all_windows = self.driver.window_handles
                                for w in all_windows:
                                    if w != current_window:
                                        self.driver.switch_to.window(w)
                                        self.driver.close()
                                self.driver.switch_to.window(current_window)
                            except:
                                pass
                            continue
                        
                        # 检查页面内容是否包含关键词
                        page_source = self.driver.page_source
                        page_title = self.driver.title
                        print(f"页面标题: {page_title}")
                        
                        if keyword not in page_source and '迪士尼' not in page_source:
                            print(f"⚠️ 页面内容不包含关键词，跳过")
                            # 关闭窗口并返回
                            try:
                                self.driver.close()
                                time.sleep(1)
                                self.driver.switch_to.window(current_window)
                                time.sleep(1)
                            except:
                                pass
                            continue
                        
                        print("✅ 页面内容包含关键词，继续处理")
                        
                        post_data = {
                            "platform": "tieba",
                            "post_id": "tieba_%d_%d" % (post_counter, int(time.time())),
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
                                '.d_post_content',
                                '[class*="d_post_content"]',
                                '.post_content',
                                '[class*="post_content"]',
                                '.j_d_post_content',
                                '[class*="j_d_post_content"]'
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
                            print("贴吧内容:")
                            print(post_data["content"])
                        except Exception as e:
                            print("提取内容失败: %s" % str(e))
                        
                        print("正在滚动加载评论...")
                        last_height = 0
                        same_count = 0
                        max_scrolls = 20  # 限制最大滚动次数
                        for i in range(max_scrolls):
                            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(2)
                            try:
                                new_height = self.driver.execute_script("return document.body.scrollHeight")
                                if new_height == last_height:
                                    same_count += 1
                                    if same_count >= 3:
                                        break
                                else:
                                    same_count = 0
                                    last_height = new_height
                            except:
                                pass
                            print(f"  滚动 {i+1}/{max_scrolls}")
                        print("滚动完成")
                        
                        try:
                            more_selectors = [
                                '//a[contains(text(), "下一页")]',
                                '//span[contains(text(), "下一页")]',
                                '//button[contains(text(), "下一页")]'
                            ]
                            for selector in more_selectors:
                                try:
                                    elem = self.driver.find_element(By.XPATH, selector)
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                    time.sleep(1)
                                    elem.click()
                                    print("点击了下一页")
                                    time.sleep(3)
                                    for i in range(20):
                                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                        time.sleep(2)
                                    break
                                except:
                                    continue
                        except:
                            pass
                        
                        comments_data = []
                        try:
                            print("正在使用DOM方式提取评论...")
                            comments_data = self._extract_comments_from_dom()
                            if comments_data is not None:
                                print("DOM方式提取到 %d 条评论" % len(comments_data))
                            else:
                                comments_data = []
                            
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
                                print("已保存 %d 条评论，累计爬取 %d 条数据" % (len(comments_data), len(self.crawl_data)))
                            else:
                                self.crawl_data.append(post_data)
                                print("未找到评论，保存贴吧本身")
                        except Exception as e:
                            print("提取评论失败: %s" % str(e))
                            self.crawl_data.append(post_data)
                        
                        # 安全关闭窗口并切换回来
                        try:
                            print(f"关闭当前窗口，切换回: {current_window}")
                            self.driver.close()
                            time.sleep(1)
                            self.driver.switch_to.window(current_window)
                            time.sleep(1)
                        except Exception as e:
                            print(f"关闭窗口时出错: {e}")
                            # 确保切换回原窗口
                            try:
                                all_windows = self.driver.window_handles
                                if current_window in all_windows:
                                    self.driver.switch_to.window(current_window)
                            except:
                                pass
                        
                        processed_urls.append(post_url)
                        post_counter += 1
                        found = True
                        print("\n完成贴吧 %d/%d" % (post_counter, target_count))
                        time.sleep(random.uniform(2, 4))
                        # 不要break，继续处理下一个帖子
                    except Exception as e:
                        print("处理贴吧失败: %s" % str(e))
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
                
                if not found:
                    print("正在加载更多贴吧...")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(5)
            
            print("\n=== 爬取完成 ===")
            print("共爬取 %d 条贴吧" % post_counter)
            print("共保存 %d 条数据（含评论）" % len(self.crawl_data))
            return self.crawl_data
            
        except Exception as e:
            print("[贴吧-致命错误] 爬取中断：%s" % str(e))
            return self.crawl_data
    
    def save_comments_to_csv(self, tieba_data, keyword):
        try:
            raw_dir = os.path.join(self.project_root, "data", "latest")
            date_str = datetime.now().strftime("%Y%m%d")
            csv_path = os.path.join(raw_dir, "tieba_raw_%s_%s.csv" % (keyword, date_str))
            
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
                
                for row in tieba_data:
                    formatted_row = {}
                    for field in base_fields:
                        value = row.get(field, "NULL")
                        if value is None or value == "":
                            value = "NULL"
                        formatted_row[field] = value
                    writer.writerow(formatted_row)
            
            print("[格式规范] 已保存%d条数据到%s，格式符合规范" % (len(tieba_data), csv_path))
            
            return csv_path
            
        except Exception as e:
            print("保存数据失败: %s" % str(e))
            return None
    
    def close(self):
        try:
            if self.driver:
                self.driver.quit()
                print("[贴吧-结束] 驱动已关闭")
        except Exception as e:
            print("关闭浏览器失败: %s" % str(e))


if __name__ == "__main__":
    print("=" * 80)
    print("贴吧爬虫测试 - 简单版")
    print("=" * 80)
    
    try:
        spider = TiebaSpider(headless=False)
        
        keyword = "上海迪士尼"
        print("测试爬取关键词: %s" % keyword)
        print("目标爬取贴吧数: 20条（以获取约100条评论）")
        
        tieba_data = spider.crawl(keyword, target_count=20)
        
        csv_path = None
        if tieba_data:
            print("\n爬取成功！共获取 %d 条数据（每条评论单独一行）" % len(tieba_data))
            print("\n=== 爬取的数据预览（前10条） ===")
            for i, data in enumerate(tieba_data[:10]):
                print("\n--- 第%d条数据 ---" % (i+1))
                content_preview = data['content'][:80] if len(data['content']) > 80 else data['content']
                print("贴吧内容: %s..." % content_preview)
                print("评论用户: %s" % data['comment_users'])
                print("评论内容: %s" % data['comment_content'])
            
            csv_path = spider.save_comments_to_csv(tieba_data, keyword)
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
        print("贴吧爬虫测试完成！")
        print("=" * 80)

