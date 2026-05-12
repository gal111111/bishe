import os
import sys
import json
import re
import time
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.config.config_manager import PROJECT_ROOT


class ZhihuPlaywrightCrawler:
    """知乎爬虫 - Playwright同步方式，支持搜索+详情页评论抓取"""

    def __init__(self):
        self.platform = 'zhihu'
        self.project_root = str(PROJECT_ROOT)
        self.cookie_dir = os.path.join(self.project_root, 'cookies')
        os.makedirs(self.cookie_dir, exist_ok=True)
        self.cookie_file = os.path.join(self.cookie_dir, 'zhihu_playwright.json')
        self.selenium_cookie_file = os.path.join(self.project_root, 'data', 'zhihu_cookies.json')

    def _load_cookies_list(self):
        """加载Cookie原始列表（用于Playwright）"""
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        if os.path.exists(self.selenium_cookie_file):
            return self._convert_selenium_cookies()
        return []

    def _convert_selenium_cookies(self):
        """将Selenium格式Cookie转换为Playwright格式"""
        try:
            with open(self.selenium_cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            converted = []
            for c in cookies:
                pc = {
                    'name': c.get('name', ''),
                    'value': c.get('value', ''),
                    'domain': c.get('domain', '.zhihu.com'),
                    'path': c.get('path', '/'),
                    'sameSite': 'Lax',
                }
                if 'expiry' in c:
                    pc['expires'] = c['expiry']
                if c.get('secure'):
                    pc['secure'] = True
                if c.get('httpOnly'):
                    pc['httpOnly'] = True
                if pc['name'] and pc['value'] and pc['domain']:
                    converted.append(pc)
            if converted:
                with open(self.cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(converted, f, ensure_ascii=False, indent=2)
                print(f"✅ 知乎Cookie已从Selenium格式转换并保存")
            return converted
        except Exception as e:
            print(f"⚠️ Cookie转换失败: {e}")
            return []

    def _get_chrome_path(self):
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        if os.path.exists(chrome_path):
            return chrome_path
        return None

    def _parse_num(self, text):
        try:
            text = text.strip()
            if '万' in text:
                return int(float(text.replace('万', '')) * 10000)
            if 'k' in text.lower():
                return int(float(text.lower().replace('k', '')) * 1000)
            digits = ''.join([c for c in text if c.isdigit()])
            return int(digits) if digits else 0
        except:
            return 0

    def crawl(self, keyword: str, target_count: int = 20, fetch_comments: bool = True, comment_posts: int = 5) -> pd.DataFrame:
        """爬取知乎数据+评论

        Args:
            keyword: 搜索关键词
            target_count: 目标内容数量
            fetch_comments: 是否抓取评论
            comment_posts: 抓取评论的帖子数量
        """
        print(f"\n{'='*60}")
        print(f"🎯 Playwright知乎爬虫 - 关键词: {keyword}")
        print(f"{'='*60}")

        all_data = []
        cookies_list = self._load_cookies_list()
        chrome_path = self._get_chrome_path()

        with sync_playwright() as p:
            launch_args = {
                'headless': False,
                'args': ['--disable-blink-features=AutomationControlled']
            }
            if chrome_path:
                launch_args['executable_path'] = chrome_path

            browser = p.chromium.launch(**launch_args)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page)

            # 先访问知乎，再加载Cookie
            page.goto('https://www.zhihu.com', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(2000)

            if cookies_list:
                try:
                    context.add_cookies(cookies_list)
                    print(f"✅ 知乎Cookie已加载 ({len(cookies_list)}个)")
                except Exception as e:
                    print(f"⚠️ Cookie加载失败: {e}")
                    # 尝试逐个添加
                    loaded = 0
                    for c in cookies_list:
                        try:
                            context.add_cookies([c])
                            loaded += 1
                        except:
                            pass
                    print(f"✅ 成功加载 {loaded}/{len(cookies_list)} 个Cookie")

            # 刷新页面使Cookie生效
            page.reload(wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(3000)

            # 检查是否需要登录
            current_url = page.url
            if 'signin' in current_url.lower():
                print("⚠️ 知乎Cookie已失效，需要登录！")
                print("🔐 请在浏览器中完成登录...")
                for i in range(120):
                    page.wait_for_timeout(1000)
                    if 'signin' not in page.url.lower():
                        break
                # 保存新Cookie
                new_cookies = context.cookies()
                with open(self.cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(new_cookies, f, ensure_ascii=False, indent=2)
                print("✅ 登录完成，Cookie已保存")

            # 搜索
            import urllib.parse
            encoded_kw = urllib.parse.quote(keyword)
            search_url = f'https://www.zhihu.com/search?q={encoded_kw}&type=content'
            print(f"\n🔍 搜索: {search_url}")
            page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)

            # 滚动加载更多
            for i in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(2000)

            # 提取搜索结果
            items = page.query_selector_all('.ContentItem, [class*="ContentItem"]')
            if not items:
                items = page.query_selector_all('.SearchResult-Card, .List-item, [class*="Card"]')

            print(f"📋 找到 {len(items)} 个搜索结果")

            seen_contents = set()
            for idx, item in enumerate(items[:target_count * 2]):
                try:
                    data = self._extract_search_item(item)
                    if data and data.get('content'):
                        content_key = data['content'][:50]
                        if content_key not in seen_contents:
                            seen_contents.add(content_key)
                            all_data.append(data)
                            print(f"  ✅ [{len(all_data)}] {data.get('author', '未知')}: {data.get('content', '')[:30]}...")
                            if len(all_data) >= target_count:
                                break
                except Exception as e:
                    continue

            # 抓取评论
            if fetch_comments and all_data:
                comments_data = self._fetch_zhihu_comments(page, all_data[:comment_posts])
                if comments_data:
                    print(f"\n💬 获取到 {len(comments_data)} 条知乎评论")
                    for post in all_data:
                        post_comments = [c for c in comments_data if c.get('post_url') == post.get('url')]
                        if post_comments:
                            post['top_comments'] = ' | '.join([c['comment'][:50] for c in post_comments[:3]])
                            post['comments_data'] = post_comments

            # 保存Cookie
            new_cookies = context.cookies()
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(new_cookies, f, ensure_ascii=False, indent=2)

            browser.close()

        print(f"\n✅ 知乎爬取完成：{len(all_data)} 条内容")
        if all_data:
            return pd.DataFrame(all_data)
        else:
            return pd.DataFrame(columns=['platform', 'author', 'content', 'publish_time',
                                         'comments_count', 'upvotes', 'url', 'crawl_time'])

    def _extract_search_item(self, item):
        """从搜索结果卡片中提取数据"""
        result = {
            'platform': '知乎',
            'author': '',
            'content': '',
            'publish_time': datetime.now().strftime('%Y-%m-%d'),
            'comments_count': 0,
            'upvotes': 0,
            'url': '',
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            title_elem = item.query_selector('h3, .ContentItem-title, [class*="Title"]')
            if title_elem:
                result['title'] = title_elem.inner_text().strip()

            content_elem = item.query_selector('.RichContent-inner, .ContentItem-answer, [class*="RichContent"]')
            if content_elem:
                result['content'] = content_elem.inner_text().strip()[:500]

            author_elem = item.query_selector('.AuthorInfo-name, .UserLink-link, [class*="AuthorInfo"] [class*="name"]')
            if author_elem:
                result['author'] = author_elem.inner_text().strip()

            up_elem = item.query_selector('.VoteButton--up, [class*="VoteButton"], button[class*="up"]')
            if up_elem:
                result['upvotes'] = self._parse_num(up_elem.inner_text())

            comment_elem = item.query_selector('[class*="comment"], button[class*="Comment"]')
            if comment_elem:
                result['comments_count'] = self._parse_num(comment_elem.inner_text())

            link_elem = item.query_selector('a[href*="/question/"], a[href*="/answer/"], a[href*="/p/"]')
            if link_elem:
                href = link_elem.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        href = 'https://www.zhihu.com' + href
                    result['url'] = href

            if not result['content'] and result.get('title'):
                result['content'] = result['title']

        except:
            pass

        return result if result.get('content') else None

    def _fetch_zhihu_comments(self, page, posts):
        """进入知乎详情页抓取评论"""
        comments_data = []

        posts_with_url = [p for p in posts if p.get('url')]
        if not posts_with_url:
            print("  ⚠️ 没有可访问的知乎链接")
            return comments_data

        print(f"\n{'='*60}")
        print(f"💬 进入详情页获取评论（前{len(posts_with_url)}条）...")
        print(f"{'='*60}")

        for idx, post in enumerate(posts_with_url):
            post_url = post['url']
            print(f"\n[{idx+1}/{len(posts_with_url)}] {post.get('author', '')}: {post.get('content', '')[:30]}...")
            print(f"   ➡️  {post_url}")

            try:
                page.goto(post_url, wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(5000)

                # 滚动加载评论
                for i in range(15):
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    page.wait_for_timeout(1500)

                # 尝试点击"查看更多评论"
                try:
                    more_btn = page.query_selector('button:has-text("查看更多"), button:has-text("更多评论")')
                    if more_btn:
                        more_btn.click()
                        page.wait_for_timeout(3000)
                        for i in range(10):
                            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                            page.wait_for_timeout(1500)
                except:
                    pass

                # 提取评论 - 方式1：DOM选择器
                comment_items = page.query_selector_all(
                    '.CommentItem, [class*="CommentItem"], [class*="comment-item"]'
                )

                comment_count = 0
                if comment_items:
                    for ci in comment_items:
                        try:
                            user_elem = ci.query_selector('.AuthorInfo-name, .UserLink-link, a[href*="/people/"]')
                            content_elem = ci.query_selector('.RichContent, [class*="content"], [class*="CommentItem"]')

                            user_name = user_elem.inner_text().strip() if user_elem else ''
                            comment_text = content_elem.inner_text().strip() if content_elem else ''

                            if comment_text and len(comment_text) > 2:
                                skip_words = ['回复', '赞', '踩', '查看', '更多', '收起', '删除', '举报', '分享', '评论']
                                if any(w in comment_text and len(comment_text) < 20 for w in skip_words):
                                    continue

                                comments_data.append({
                                    'platform': '知乎',
                                    'post_url': post_url,
                                    'post_author': post.get('author', ''),
                                    'comment_author': user_name,
                                    'comment': comment_text[:500],
                                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                                comment_count += 1
                        except:
                            continue

                # 方式2：如果DOM没找到评论，用页面文本提取
                if comment_count == 0:
                    try:
                        page_text = page.inner_text('body')
                        lines = page_text.split('\n')

                        comment_section = False
                        for line in lines:
                            line = line.strip()
                            if not line or len(line) < 3:
                                continue

                            if '评论' in line and len(line) < 15:
                                comment_section = True
                                continue

                            if comment_section:
                                skip_words = ['回复', '赞', '踩', '查看', '更多', '收起', '删除', '举报', '分享', '赞同', '写评论']
                                if any(w in line and len(line) < 20 for w in skip_words):
                                    continue
                                if line.isdigit():
                                    continue
                                if len(line) > 300:
                                    continue

                                comments_data.append({
                                    'platform': '知乎',
                                    'post_url': post_url,
                                    'post_author': post.get('author', ''),
                                    'comment_author': '',
                                    'comment': line[:500],
                                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                                comment_count += 1
                    except:
                        pass

                print(f"   ✅ 获取到 {comment_count} 条评论")

            except Exception as e:
                print(f"   ⚠️ 失败: {e}")

        # 保存评论
        if comments_data:
            raw_dir = os.path.join(self.project_root, 'data', 'raw')
            os.makedirs(raw_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            comments_csv = os.path.join(raw_dir, f'zhihu_comments_{timestamp}.csv')
            df = pd.DataFrame(comments_data)
            df.to_csv(comments_csv, index=False, encoding='utf-8-sig')
            print(f"\n✅ 知乎评论数据已保存: {comments_csv}")

        return comments_data


def crawl_zhihu_playwright(keyword: str, target_count: int = 20) -> pd.DataFrame:
    """同步版本的知乎爬虫"""
    crawler = ZhihuPlaywrightCrawler()
    return crawler.crawl(keyword, target_count)
