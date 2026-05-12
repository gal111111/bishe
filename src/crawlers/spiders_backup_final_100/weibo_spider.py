# -*- coding: utf-8 -*-
"""
微博官方账号评论爬取 - 简单版
"""
import os
import sys
import time
import random
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from src.crawlers.selenium_spiders.common import init_csv_header, save_to_csv_standard


class WeiboSpider:
    def __init__(self, headless=False):
        self.project_root = project_root
        self.headless = headless
        self.driver_service = Service(executable_path=os.path.join(project_root, "edgedriver_win64", "msedgedriver.exe"))
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
        print("\n=== 开始处理微博登录 ===")
        cookie_path = os.path.join(self.project_root, "data", "weibo_cookies.json")
        
        if os.path.exists(cookie_path):
            try:
                import json
                self.driver.get("https://weibo.com/404")
                time.sleep(1)
                with open(cookie_path, 'r', encoding='utf-8') as f:
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
                self.driver.get("https://weibo.com")
                self.driver.refresh()
                time.sleep(3)
                
                if "weibo.com" in self.driver.current_url and "登录" not in self.driver.title:
                    print("使用已保存的 Cookie 登录成功！无需扫码！")
                    return True
            except Exception as e:
                print("Cookie加载失败: %s" % str(e))
        
        print("本地Cookie无效/未找到，请在浏览器中登录微博")
        print("请在弹出的浏览器窗口中完成登录，登录后请等待页面跳转到主页...")
        
        self._safe_get("https://weibo.com/login.php")
        
        login_success = False
        wait_time = 0
        max_wait = 120
        
        while wait_time < max_wait:
            try:
                if "weibo.com" in self.driver.current_url and "login" not in self.driver.current_url.lower():
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
            valid_cookies = []
            for cookie in cookies:
                if 'weibo.com' in cookie.get('domain', '') or cookie.get('name') in ['SUB', 'SUBP', 'XSRF-TOKEN', 'WBPSESS']:
                    valid_cookies.append(cookie)
            with open(cookie_path, 'w', encoding='utf-8') as f:
                json.dump(valid_cookies, f, indent=2, ensure_ascii=False)
            print("Cookie 已保存到：%s (共%d个有效Cookie)" % (cookie_path, len(valid_cookies)))
        except Exception as e:
            print("Cookie保存失败: %s" % str(e))
        
        return True
    
    def _extract_comments_from_dom(self):
        comments_data = []
        seen_texts = set()
        
        try:
            comment_container_selectors = [
                '.vue-recycle-scroller__item-view',
                '.comment_item',
                '.list_li',
                '.comment-wrap',
                '[node-type="comment_list"] .list_li',
                '.WB_feed_type .list_li',
                '.comment_list .list_li',
                '[class*="comment"] [class*="item"]',
                '[class*="comment"] [class*="list"] li'
            ]
            
            user_name_selectors = [
                '.user-name',
                '.name',
                '.txt_name',
                '.W_f14',
                '[class*="user"] [class*="name"]',
                '[node-type="comment"] a[href*="/u/"]',
                '[node-type="comment"] a[href*="/n/"]',
                'a[usercard]'
            ]
            
            comment_content_selectors = [
                '.comment-text',
                '.comment_text',
                '.txt',
                '.text',
                '[node-type="comment_text"]',
                '[class*="comment"] [class*="text"]',
                '[class*="comment"] [class*="txt"]'
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
                        filter_words = ['按热度', '按时间', '加载更多', '查看更多', '回复', '赞', '转发', '收藏', '评论', '来自', '热门', '最新', '全部', '消息', '发布于', '播放视频']
                        should_skip = False
                        for word in filter_words:
                            if word in comment_content and len(comment_content) < 30:
                                should_skip = True
                                break
                        
                        if not should_skip:
                            comment_content = comment_content.replace('\n', ' ').replace('\r', ' ')
                            
                            if user_name in comment_content and (':' in comment_content or '：' in comment_content):
                                sep_idx = -1
                                if ':' in comment_content:
                                    sep_idx = comment_content.find(':')
                                if '：' in comment_content and (sep_idx == -1 or comment_content.find('：') < sep_idx):
                                    sep_idx = comment_content.find('：')
                                
                                if sep_idx != -1:
                                    possible_user = comment_content[:sep_idx].strip()
                                    possible_content = comment_content[sep_idx+1:].strip()
                                    
                                    if possible_user and possible_content and len(possible_user) < 50:
                                        user_name = possible_user
                                        comment_content = possible_content
                            
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
    
    def crawl(self, keyword, target_count=20, is_official=True, official_url=None):
        crawl_date = datetime.now().strftime("%Y%m%d")
        
        try:
            if official_url:
                print("[微博-启动] 直接访问官方微博主页: %s" % official_url)
                if not self._safe_get(official_url):
                    print("[微博-错误] 无法访问官方微博主页")
                    return self.crawl_data
            else:
                print("[微博-启动] 正在查找官方账号: %s" % keyword)
                search_url = "https://s.weibo.com/weibo?q=%s" % keyword
                print("正在访问搜索页面: %s" % search_url)
                
                if not self._safe_get(search_url):
                    print("[微博-错误] 无法访问搜索页面")
                    return self.crawl_data
            
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.card-wrap, .vue-recycle-scroller__item-view')))
            
            print("[微博-滚动] 开始预滚动加载更多帖子...")
            for i in range(5):
                print("[滚动] 正在滚动加载更多内容 (%d/5)..." % (i+1))
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
            print("[滚动] 滚动完成")
            
            print("[微博-开始] 从页面提取微博...")
            
            post_counter = 0
            processed_urls = []
            
            while post_counter < target_count:
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                post_selectors = [
                    ".vue-recycle-scroller__item-view",
                    ".card-wrap"
                ]
                
                posts = []
                for selector in post_selectors:
                    try:
                        posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if posts:
                            print("使用选择器 %s 找到 %d 个微博卡片" % (selector, len(posts)))
                            break
                    except:
                        continue
                
                if not posts:
                    print("[微博-错误] 未找到帖子元素")
                    break
                
                found = False
                for idx, post in enumerate(posts):
                    try:
                        print("\n正在处理第 %d 个微博卡片..." % idx)
                        
                        post_url = None
                        
                        try:
                            all_links = post.find_elements(By.TAG_NAME, 'a')
                            print("  该卡片有 %d 个链接" % len(all_links))
                            for link_idx, link in enumerate(all_links):
                                try:
                                    href = link.get_attribute('href')
                                    text = link.text.strip()
                                    print("    链接 %d: %s (文本: %s)" % (link_idx, href, text[:30]))
                                    if href and 'weibo.com/' in href:
                                        if '/u/' not in href and '/100808' not in href and '/p/' not in href:
                                            post_url = href
                                            print("  找到微博链接: %s" % post_url)
                                            break
                                except:
                                    continue
                        except Exception as e:
                            print("  获取链接失败: %s" % str(e))
                        
                        if not post_url:
                            try:
                                links = post.find_elements(By.CSS_SELECTOR, 'a[href*="/detail/"], a[href*="/p/"]')
                                for link in links:
                                    try:
                                        href = link.get_attribute('href')
                                        if href:
                                            post_url = href
                                            print("  使用CSS选择器找到微博链接: %s" % post_url)
                                            break
                                    except:
                                        continue
                            except:
                                pass
                        
                        if not post_url:
                            print("  未找到链接，跳过该卡片")
                            continue
                        
                        if post_url in processed_urls:
                            print("  该链接已处理过，跳过")
                            continue
                        
                        print("\n=== 微博第%d条 ===" % (post_counter + 1))
                        print("微博链接: %s" % post_url)
                        
                        current_window = self.driver.current_window_handle
                        
                        self.driver.execute_script("window.open('%s', '_blank');" % post_url)
                        time.sleep(2)
                        
                        all_windows = self.driver.window_handles
                        new_window = [w for w in all_windows if w != current_window][0]
                        self.driver.switch_to.window(new_window)
                        
                        time.sleep(5)
                        
                        post_data = {
                            "platform": "weibo",
                            "post_id": "weibo_%d_%d" % (post_counter, int(time.time())),
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
                                '.weibo-text',
                                '.WB_text',
                                '[class*="wbtext"]'
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
                            print("微博内容:")
                            print(post_data["content"])
                        except Exception as e:
                            print("提取内容失败: %s" % str(e))
                        
                        print("正在滚动加载评论...")
                        last_height = 0
                        same_count = 0
                        for i in range(30):
                            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(2)
                            try:
                                new_height = self.driver.execute_script("return document.body.scrollHeight")
                                if new_height == last_height:
                                    same_count += 1
                                    if same_count >= 5:
                                        break
                                else:
                                    same_count = 0
                                    last_height = new_height
                            except:
                                pass
                        print("滚动完成")
                        
                        try:
                            more_selectors = [
                                '//a[contains(text(), "后面还有")]',
                                '//a[contains(text(), "查看更多")]',
                                '//a[contains(text(), "点击查看")]',
                                '//span[contains(text(), "查看更多")]'
                            ]
                            for selector in more_selectors:
                                try:
                                    elem = self.driver.find_element(By.XPATH, selector)
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                    time.sleep(1)
                                    elem.click()
                                    print("点击了查看更多评论")
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
                            print("DOM方式提取到 %d 条评论" % len(comments_data))
                            
                            # 如果DOM方式提取不到评论，尝试回退到文本方式
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
                                        if '按热度' in line or '按时间' in line or '全部评论' in line or '最新评论' in line:
                                            comment_start_idx = idx + 1
                                            print("找到评论区起始位置: 第%d行" % comment_start_idx)
                                            break
                                    
                                    i = comment_start_idx
                                    while i < len(lines):
                                        line = lines[i].strip()
                                        if not line or len(line) < 2:
                                            i += 1
                                            continue
                                        
                                        filter_words = ['按热度', '按时间', '加载更多', '查看更多', '回复', '赞', '转发', '收藏', '评论', '按', '热度', '时间', '来自', '热门', '最新', '全部', '消息', '特别关注', '自定义分组', '名人明星', '悄悄关注', '发布于', '播放视频', '分享这条', '次观看', '万次观看']
                                        should_skip = False
                                        for word in filter_words:
                                            if word in line and len(line) < 30:
                                                should_skip = True
                                                break
                                        
                                        if should_skip:
                                            i += 1
                                            continue
                                        
                                        if len(line) > 50:
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
                                print("未找到评论，保存微博本身")
                        except Exception as e:
                            print("提取评论失败: %s" % str(e))
                            self.crawl_data.append(post_data)
                        
                        self.driver.close()
                        self.driver.switch_to.window(current_window)
                        
                        processed_urls.append(post_url)
                        post_counter += 1
                        found = True
                        print("\n完成微博 %d/%d" % (post_counter, target_count))
                        time.sleep(random.uniform(2, 4))
                        break
                    except Exception as e:
                        print("处理微博失败: %s" % str(e))
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
                    print("正在加载更多微博...")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(5)
            
            print("\n=== 爬取完成 ===")
            print("共爬取 %d 条微博" % post_counter)
            print("共保存 %d 条数据（含评论）" % len(self.crawl_data))
            return self.crawl_data
            
        except Exception as e:
            print("[微博-致命错误] 爬取中断：%s" % str(e))
            return self.crawl_data
    
    def save_comments_to_csv(self, weibo_data, keyword):
        try:
            raw_dir = os.path.join(self.project_root, "data", "raw")
            date_str = datetime.now().strftime("%Y%m%d")
            csv_path = os.path.join(raw_dir, "weibo_raw_%s_%s.csv" % (keyword, date_str))
            
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
                
                for row in weibo_data:
                    formatted_row = {}
                    for field in base_fields:
                        value = row.get(field, "NULL")
                        if value is None or value == "":
                            value = "NULL"
                        formatted_row[field] = value
                    writer.writerow(formatted_row)
            
            print(f"[格式规范] 已保存{len(weibo_data)}条数据到{csv_path}，格式符合规范")
            
            return csv_path
            
        except Exception as e:
            print("保存数据失败: %s" % str(e))
            return None
    
    def close(self):
        try:
            if self.driver:
                self.driver.quit()
                print("[微博-结束] 驱动已关闭")
        except Exception as e:
            print("关闭浏览器失败: %s" % str(e))


if __name__ == "__main__":
    print("=" * 80)
    print("微博官方账号爬虫测试 - 简单版")
    print("=" * 80)
    
    try:
        spider = WeiboSpider(headless=False)
        
        keyword = "上海迪士尼"
        official_url = "https://weibo.com/u/5200478600"
        print("测试爬取关键词: %s" % keyword)
        print("直接访问官方微博主页: %s" % official_url)
        print("目标爬取微博数: 20条（以获取约100条评论）")
        
        weibo_data = spider.crawl(keyword, target_count=20, is_official=True, official_url=official_url)
        
        csv_path = None
        if weibo_data:
            print("\n爬取成功！共获取 %d 条数据（每条评论单独一行）" % len(weibo_data))
            print("\n=== 爬取的数据预览（前10条） ===")
            for i, data in enumerate(weibo_data[:10]):
                print("\n--- 第%d条数据 ---" % (i+1))
                content_preview = data['content'][:80] if len(data['content']) > 80 else data['content']
                print("微博内容: %s..." % content_preview)
                print("评论用户: %s" % data['comment_users'])
                print("评论内容: %s" % data['comment_content'])
            
            csv_path = spider.save_comments_to_csv(weibo_data, keyword)
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
        print("微博爬虫测试完成！")
        print("=" * 80)
