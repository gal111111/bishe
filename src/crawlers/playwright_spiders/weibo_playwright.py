import os
import sys
import json
import re
import pandas as pd
from datetime import datetime
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.config.config_manager import PROJECT_ROOT


class WeiboPlaywrightCrawler:
    """微博爬虫 - API获取微博内容 + Playwright进入详情页抓取评论"""

    def __init__(self):
        self.platform = 'weibo'
        self.project_root = str(PROJECT_ROOT)
        self.cookie_dir = os.path.join(self.project_root, 'cookies')
        os.makedirs(self.cookie_dir, exist_ok=True)
        self.cookie_file = os.path.join(self.cookie_dir, 'weibo_playwright.json')

    def _load_cookies(self):
        """加载Cookie"""
        for cookie_file in [self.cookie_file, os.path.join(self.project_root, 'data', 'weibo_cookies.json')]:
            if os.path.exists(cookie_file):
                with open(cookie_file, 'r') as f:
                    cookies_list = json.load(f)
                    cookies = {}
                    for c in cookies_list:
                        cookies[c['name']] = c['value']
                    return cookies
        return {}

    def _load_cookies_list(self):
        """加载Cookie原始列表（用于Playwright）"""
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r') as f:
                return json.load(f)
        alt = os.path.join(self.project_root, 'data', 'weibo_cookies.json')
        if os.path.exists(alt):
            with open(alt, 'r') as f:
                return json.load(f)
        return []

    def _get_chrome_path(self):
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        if os.path.exists(chrome_path):
            return chrome_path
        return None

    def crawl(self, keyword: str, target_count: int = 50, fetch_comments: bool = True, comment_posts: int = 5) -> pd.DataFrame:
        """爬取微博数据+评论

        Args:
            keyword: 搜索关键词
            target_count: 目标微博数量
            fetch_comments: 是否抓取评论
            comment_posts: 抓取评论的微博数量（取评论数最多的前N条）
        """
        print(f"\n{'='*60}")
        print(f"🎯 Playwright微博爬虫 - 关键词: {keyword}")
        print(f"{'='*60}")

        cookies = self._load_cookies()
        if not cookies:
            print("❌ 未找到Cookie！")
            return pd.DataFrame()

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Referer': 'https://m.weibo.cn/',
            'Accept': 'application/json, text/plain, */*',
        }

        all_data = []
        page = 1

        while len(all_data) < target_count and page <= 10:
            print(f"\n📄 第{page}页...")

            search_url = f'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{keyword}&page_type=searchall&page={page}'

            try:
                response = requests.get(search_url, headers=headers, cookies=cookies, timeout=30)
                data = response.json()

                if data.get('ok') == 1:
                    cards = data.get('data', {}).get('cards', [])

                    for card in cards:
                        if 'mblog' not in card:
                            continue

                        blog = card['mblog']
                        post_id = blog.get('id', '')
                        author = blog.get('user', {}).get('screen_name', '')
                        content = blog.get('text', '')
                        content = re.sub(r'<[^>]+>', '', content)

                        time_str = blog.get('created_at', '')
                        comments_count = blog.get('comments_count', 0)
                        reposts_count = blog.get('reposts_count', 0)
                        attitudes_count = blog.get('attitudes_count', 0)

                        all_data.append({
                            'platform': '微博',
                            'post_id': post_id,
                            'author': author,
                            'content': content,
                            'publish_time': time_str,
                            'comments_count': comments_count,
                            'reposts_count': reposts_count,
                            'attitudes_count': attitudes_count,
                            'total_interactions': comments_count + reposts_count + attitudes_count,
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })

                        print(f"   ✅ {author}: {content[:30]}... (👍{attitudes_count} 💬{comments_count} 🔁{reposts_count})")

                    if not cards:
                        break

                page += 1

            except Exception as e:
                print(f"❌ 获取失败: {e}")
                break

        print(f"\n✅ 微博内容爬取完成！共 {len(all_data)} 条微博")

        # 抓取评论
        if fetch_comments and all_data:
            comments_df = self.crawl_comments(all_data, comment_posts)
            if not comments_df.empty:
                print(f"💬 评论爬取完成！共 {len(comments_df)} 条评论")

        if all_data:
            df = pd.DataFrame(all_data)
            return df
        else:
            return pd.DataFrame(columns=['platform', 'post_id', 'author', 'content', 'publish_time',
                                         'comments_count', 'reposts_count', 'attitudes_count',
                                         'total_interactions', 'crawl_time'])

    def crawl_comments(self, posts_data, target_posts=5):
        """通过Playwright访问详情页抓取评论

        Args:
            posts_data: 微博数据列表（需包含post_id和comments_count）
            target_posts: 抓取评论的微博数量
        """
        posts_with_comments = [
            p for p in posts_data
            if p.get('post_id') and p.get('comments_count', 0) > 0
        ]
        posts_with_comments.sort(key=lambda x: x.get('comments_count', 0), reverse=True)
        posts_with_comments = posts_with_comments[:target_posts]

        if not posts_with_comments:
            print("⚠️ 没有有评论的微博")
            return pd.DataFrame()

        print(f"\n{'='*60}")
        print(f"💬 进入详情页获取评论（前{len(posts_with_comments)}条热门微博）...")
        print(f"{'='*60}")

        all_comments = []
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
                viewport={'width': 375, 'height': 812},
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                locale='zh-CN',
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page)

            if cookies_list:
                context.add_cookies(cookies_list)

            page.goto('https://m.weibo.cn', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(3000)

            for idx, post in enumerate(posts_with_comments):
                post_id = post['post_id']
                detail_url = f'https://m.weibo.cn/detail/{post_id}'

                print(f"\n[{idx+1}/{len(posts_with_comments)}] {post.get('author', '')}: {post.get('content', '')[:30]}...")
                print(f"   ➡️  {detail_url}")

                try:
                    page.goto(detail_url, wait_until='domcontentloaded', timeout=30000)
                    page.wait_for_timeout(5000)

                    for i in range(10):
                        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        page.wait_for_timeout(1000)

                    page_text = page.inner_text('body')

                    weibo_el = page.query_selector('.weibo-text') or page.query_selector('.detail-content')
                    weibo_text = weibo_el.inner_text().strip() if weibo_el else ''

                    lines = page_text.split('\n')
                    comment_section = False
                    comment_count = 0

                    for line in lines:
                        line = line.strip()
                        if not line or len(line) < 3:
                            continue

                        if '评论' in line and len(line) < 10:
                            comment_section = True
                            continue

                        if comment_section:
                            if any(skip in line for skip in ['赞', '回复', '举报', '删除', '来自', '更多', '收起', '展开', '分享', '相关', '推荐', '关注']):
                                continue
                            if line.isdigit():
                                continue
                            if line == weibo_text or (weibo_text and weibo_text[:30] in line):
                                continue
                            if len(line) > 200:
                                continue

                            all_comments.append({
                                'platform': '微博',
                                'post_id': post_id,
                                'post_author': post.get('author', ''),
                                'post_content': post.get('content', '')[:50],
                                'comment': line[:500],
                                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            comment_count += 1
                            print(f"      💬 {line[:30]}...")

                    print(f"   ✅ 获取到 {comment_count} 条评论")

                except Exception as e:
                    print(f"   ⚠️ 失败: {e}")

            browser.close()

        if all_comments:
            raw_dir = os.path.join(self.project_root, 'data', 'raw')
            os.makedirs(raw_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            comments_csv = os.path.join(raw_dir, f'weibo_comments_{timestamp}.csv')
            df = pd.DataFrame(all_comments)
            df.to_csv(comments_csv, index=False, encoding='utf-8-sig')
            print(f"\n✅ 评论数据已保存: {comments_csv}")

        return pd.DataFrame(all_comments)


def crawl_weibo_playwright(keyword: str, target_count: int = 50) -> pd.DataFrame:
    """同步版本的微博爬虫"""
    crawler = WeiboPlaywrightCrawler()
    return crawler.crawl(keyword, target_count)
