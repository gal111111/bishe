import os
import sys
import json
import re
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.config.config_manager import PROJECT_ROOT


class TiebaPlaywrightCrawler:
    """贴吧爬虫 - Playwright同步方式，支持搜索+详情页评论抓取"""

    def __init__(self):
        self.platform = 'tieba'
        self.project_root = str(PROJECT_ROOT)
        self.cookie_dir = os.path.join(self.project_root, 'cookies')
        os.makedirs(self.cookie_dir, exist_ok=True)
        self.cookie_file = os.path.join(self.cookie_dir, 'tieba_playwright.json')
        self.selenium_cookie_file = os.path.join(self.project_root, 'data', 'tieba_cookies.json')

    def _load_cookies_list(self):
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        if os.path.exists(self.selenium_cookie_file):
            return self._convert_selenium_cookies()
        return []

    def _convert_selenium_cookies(self):
        try:
            with open(self.selenium_cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            converted = []
            for c in cookies:
                pc = {
                    'name': c.get('name', ''),
                    'value': c.get('value', ''),
                    'domain': c.get('domain', '.baidu.com'),
                    'path': c.get('path', '/'),
                    'sameSite': 'Lax',
                }
                if 'expiry' in c:
                    pc['expires'] = c['expiry']
                if c.get('secure'):
                    pc['secure'] = True
                if pc['name'] and pc['value'] and pc['domain']:
                    converted.append(pc)
            if converted:
                with open(self.cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(converted, f, ensure_ascii=False, indent=2)
                print(f"✅ 贴吧Cookie已从Selenium格式转换并保存")
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

    def _add_cookies_safe(self, context, cookies_list):
        if not cookies_list:
            return
        try:
            context.add_cookies(cookies_list)
            print(f"✅ 贴吧Cookie已加载 ({len(cookies_list)}个)")
        except:
            loaded = 0
            for c in cookies_list:
                try:
                    context.add_cookies([c])
                    loaded += 1
                except:
                    pass
            print(f"✅ 成功加载 {loaded}/{len(cookies_list)} 个Cookie")

    def crawl(self, keyword: str, target_count: int = 20, fetch_comments: bool = True, comment_posts: int = 5) -> pd.DataFrame:
        print(f"\n{'='*60}")
        print(f"🎯 Playwright贴吧爬虫 - 关键词: {keyword}")
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
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page)

            page.goto('https://tieba.baidu.com', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(2000)

            self._add_cookies_safe(context, cookies_list)

            page.reload(wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(3000)

            # 搜索 - 进入贴吧
            import urllib.parse
            encoded_kw = urllib.parse.quote(keyword)
            search_url = f'https://tieba.baidu.com/f?ie=utf-8&kw={encoded_kw}'
            print(f"\n🔍 进入贴吧: {search_url}")
            page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)

            for i in range(5):
                try:
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    page.wait_for_timeout(2000)
                except:
                    page.wait_for_timeout(2000)

            # 提取帖子列表
            items = page.query_selector_all('.j_thread_list, .thread_list_bright, [class*="thread_list"] li, [class*="threadlist"] li')
            if not items:
                items = page.query_selector_all('[class*="topic"], [class*="post-list"]')

            print(f"📋 找到 {len(items)} 个帖子")

            seen_contents = set()
            for idx, item in enumerate(items[:target_count * 2]):
                try:
                    data = self._extract_thread_item(item)
                    if data and data.get('content'):
                        content_key = data['content'][:50]
                        if content_key not in seen_contents:
                            seen_contents.add(content_key)
                            all_data.append(data)
                            print(f"  ✅ [{len(all_data)}] {data.get('author', '未知')}: {data.get('content', '')[:30]}...")
                            if len(all_data) >= target_count:
                                break
                except:
                    continue

            # 抓取评论
            if fetch_comments and all_data:
                comments_data = self._fetch_tieba_comments(page, all_data[:comment_posts])
                if comments_data:
                    print(f"\n💬 获取到 {len(comments_data)} 条贴吧评论")
                    for post in all_data:
                        post_comments = [c for c in comments_data if c.get('post_url') == post.get('url')]
                        if post_comments:
                            post['top_comments'] = ' | '.join([c['comment'][:50] for c in post_comments[:3]])

            # 保存Cookie
            new_cookies = context.cookies()
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(new_cookies, f, ensure_ascii=False, indent=2)

            browser.close()

        print(f"\n✅ 贴吧爬取完成：{len(all_data)} 条内容")
        if all_data:
            return pd.DataFrame(all_data)
        else:
            return pd.DataFrame(columns=['platform', 'author', 'content', 'publish_time',
                                         'comments_count', 'upvotes', 'url', 'crawl_time'])

    def _extract_thread_item(self, item):
        result = {
            'platform': '贴吧',
            'author': '',
            'content': '',
            'publish_time': datetime.now().strftime('%Y-%m-%d'),
            'comments_count': 0,
            'upvotes': 0,
            'url': '',
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            # 先找帖子链接
            link_elem = item.query_selector('a[href*="/p/"], a.j_th_tit, a.threadlist_title')
            if not link_elem:
                link_elem = item.query_selector('a[href*="tieba.baidu.com/p/"]')
            if not link_elem:
                all_links = item.query_selector_all('a')
                for al in all_links:
                    href = al.get_attribute('href') or ''
                    if '/p/' in href:
                        link_elem = al
                        break

            if link_elem:
                result['content'] = link_elem.inner_text().strip()[:500]
                href = link_elem.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        href = 'https://tieba.baidu.com' + href
                    elif href.startswith('//'):
                        href = 'https:' + href
                    result['url'] = href

            author_elem = item.query_selector('.frs-author-name-wrap a, .tb_icon_author a, [class*="author"] a, [class*="username"] a')
            if not author_elem:
                author_elem = item.query_selector('[class*="author"]')
            if author_elem:
                result['author'] = author_elem.inner_text().strip()

            reply_elem = item.query_selector('.threadlist_rep_num, [class*="reply"] span, [class*="comment"] span')
            if reply_elem:
                result['comments_count'] = self._parse_num(reply_elem.inner_text())

            if not result['content']:
                text = item.inner_text().strip()
                if text and len(text) > 5:
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if len(line) > 5 and len(line) < 200:
                            result['content'] = line[:500]
                            break
        except:
            pass

        return result if result.get('content') else None

    def _fetch_tieba_comments(self, page, posts):
        comments_data = []
        posts_with_url = [p for p in posts if p.get('url')]
        if not posts_with_url:
            print("  ⚠️ 没有可访问的贴吧链接")
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

                for i in range(10):
                    try:
                        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        page.wait_for_timeout(1500)
                    except:
                        page.wait_for_timeout(1500)

                # 方式1：DOM选择器
                comment_items = page.query_selector_all(
                    '.l_post, [class*="post-item"], [class*="floor"], [class*="d_post"]'
                )

                comment_count = 0
                if comment_items:
                    for ci in comment_items:
                        try:
                            user_elem = ci.query_selector('.d_name, [class*="username"], [class*="author"] a, .p_author_name')
                            content_elem = ci.query_selector('.d_post_content, [class*="content"], [class*="text"], .p_content')

                            user_name = user_elem.inner_text().strip() if user_elem else ''
                            comment_text = content_elem.inner_text().strip() if content_elem else ''

                            if not comment_text:
                                comment_text = ci.inner_text().strip()

                            if comment_text and len(comment_text) > 2:
                                skip_words = ['回复', '举报', '删除', '收起', '展开', '来自', '只看', '赞']
                                if any(w in comment_text and len(comment_text) < 15 for w in skip_words):
                                    continue

                                comments_data.append({
                                    'platform': '贴吧',
                                    'post_url': post_url,
                                    'post_author': post.get('author', ''),
                                    'comment_author': user_name,
                                    'comment': comment_text[:500],
                                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                                comment_count += 1
                        except:
                            continue

                # 方式2：页面文本提取
                if comment_count == 0:
                    try:
                        page_text = page.inner_text('body')
                        lines = page_text.split('\n')
                        comment_section = False
                        for line in lines:
                            line = line.strip()
                            if not line or len(line) < 3:
                                continue
                            if any(kw in line for kw in ['全部回复', '评论', '吧友回复']) and len(line) < 15:
                                comment_section = True
                                continue
                            if comment_section:
                                skip_words = ['回复', '举报', '删除', '收起', '展开', '来自', '只看', '赞', '分享', '1楼', '2楼', '3楼']
                                if any(w in line and len(line) < 15 for w in skip_words):
                                    continue
                                if line.isdigit() or len(line) > 300:
                                    continue
                                comments_data.append({
                                    'platform': '贴吧',
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

        if comments_data:
            raw_dir = os.path.join(self.project_root, 'data', 'raw')
            os.makedirs(raw_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            comments_csv = os.path.join(raw_dir, f'tieba_comments_{timestamp}.csv')
            df = pd.DataFrame(comments_data)
            df.to_csv(comments_csv, index=False, encoding='utf-8-sig')
            print(f"\n✅ 贴吧评论数据已保存: {comments_csv}")

        return comments_data


def crawl_tieba_playwright(keyword: str, target_count: int = 20) -> pd.DataFrame:
    crawler = TiebaPlaywrightCrawler()
    return crawler.crawl(keyword, target_count)
