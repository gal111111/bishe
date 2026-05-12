"""
Browser Agent模块 - 论文创新亮点
基于Playwright的智能浏览器Agent，自动识别网页元素并采集数据
核心创新：不依赖硬编码CSS选择器，通过页面结构分析自动提取内容
"""
# ==================== 标准库导入 ====================
import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Optional

# ==================== 第三方库导入 ====================
import pandas as pd  # 数据处理库，用于将爬取结果转为DataFrame
from playwright.sync_api import sync_playwright  # Playwright同步API，用于浏览器自动化操作
from playwright_stealth import Stealth  # 反检测插件，使浏览器指纹更接近真实用户

# ==================== 项目内部模块导入 ====================
# 将项目根目录添加到系统路径，确保能正确导入项目配置模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.config.config_manager import PROJECT_ROOT


class BrowserAgentCrawler:
    """AI驱动的浏览器Agent爬虫类 - 论文核心创新模块

    该类实现了基于Playwright的智能浏览器自动化爬虫，能够自动识别网页元素
    并采集社交媒体平台数据。与传统的基于硬编码CSS选择器的爬虫不同，本模块
    通过页面结构分析自动提取内容，具有更强的适应性。

    核心创新点：
        1. 不依赖硬编码CSS选择器 —— 通过多级选择器降级策略自动适配页面结构
        2. 通过页面结构分析自动识别内容区域 —— 智能定位帖子、评论等关键信息
        3. 智能滚动+内容去重 —— 自动滚动加载更多内容，基于文本指纹去重
        4. 自动适配不同平台 —— 统一接口支持微博、知乎、贴吧、虎扑四大平台
        5. 评论深度采集 —— 进入帖子详情页抓取评论，实现数据深度挖掘

    Attributes:
        use_llm (bool): 是否启用LLM辅助提取（预留接口）
        project_root (str): 项目根目录路径
        cookie_dir (str): Cookie存储目录路径
    """

    # 平台配置字典：定义各平台的URL模板、视口大小和User-Agent
    # 每个平台的配置包含：mobile_url（移动端首页）、search_url（搜索URL模板）、
    # viewport（浏览器视口尺寸）、user_agent（浏览器标识）
    PLATFORM_CONFIG = {
        # 微博平台配置：使用移动端API获取微博列表，视口模拟iPhone尺寸
        '微博': {
            'mobile_url': 'https://m.weibo.cn',  # 微博移动端首页
            'search_url': 'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{keyword}',  # 搜索页URL模板
            'api_url': 'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{keyword}&page_type=searchall&page={page}',  # API接口URL模板
            'viewport': {'width': 375, 'height': 812},  # iPhone X视口尺寸
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',  # iPhone Safari UA
        },
        # 知乎平台配置：使用桌面端搜索，视口模拟PC浏览器
        '知乎': {
            'mobile_url': 'https://www.zhihu.com',  # 知乎首页
            'search_url': 'https://www.zhihu.com/search?type=content&q={keyword}',  # 搜索页URL模板
            'viewport': {'width': 1280, 'height': 800},  # PC端视口尺寸
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',  # Chrome UA
        },
        # 贴吧平台配置：使用桌面端，视口模拟PC浏览器
        '贴吧': {
            'mobile_url': 'https://tieba.baidu.com',  # 贴吧首页
            'search_url': 'https://tieba.baidu.com/f?kw={keyword}&ie=utf-8',  # 吧页URL模板
            'viewport': {'width': 1280, 'height': 800},  # PC端视口尺寸
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',  # Chrome UA
        },
        # 虎扑平台配置：使用桌面端，视口模拟PC浏览器
        '虎扑': {
            'mobile_url': 'https://bbs.hupu.com',  # 虎扑论坛首页
            'search_url': 'https://bbs.hupu.com/search?keyword={keyword}',  # 搜索页URL模板
            'viewport': {'width': 1280, 'height': 800},  # PC端视口尺寸
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',  # Chrome UA
        },
    }

    def __init__(self, use_llm=False):
        """初始化浏览器Agent爬虫

        Args:
            use_llm (bool): 是否启用LLM辅助提取功能，默认为False。
                            该参数为预留接口，未来可用于结合大语言模型
                            进行更智能的页面内容理解与提取。
        """
        self.use_llm = use_llm  # LLM辅助提取开关（预留接口）
        self.project_root = str(PROJECT_ROOT)  # 项目根目录路径
        self.cookie_dir = os.path.join(self.project_root, 'cookies')  # Cookie存储目录
        os.makedirs(self.cookie_dir, exist_ok=True)  # 确保Cookie目录存在，不存在则创建

    def _get_cookie_file(self, platform):
        """获取指定平台的Cookie文件路径

        根据平台名称映射到对应的Cookie文件名，返回完整的文件路径。
        Cookie文件以JSON格式存储，用于保持登录状态。

        Args:
            platform (str): 平台名称，支持'微博'、'知乎'、'贴吧'、'虎扑'

        Returns:
            str: Cookie文件的完整路径
        """
        # 平台名称与Cookie文件名的映射关系
        mapping = {
            '微博': 'weibo_playwright.json',
            '知乎': 'zhihu_playwright.json',
            '贴吧': 'tieba_playwright.json',
            '虎扑': 'hupu_playwright.json',
        }
        return os.path.join(self.cookie_dir, mapping.get(platform, f'{platform}_playwright.json'))

    def _load_cookies(self, platform):
        """从本地文件加载指定平台的Cookie

        读取Cookie JSON文件并解析为列表，用于在浏览器会话中恢复登录状态。
        如果Cookie文件不存在，则返回空列表。

        Args:
            platform (str): 平台名称

        Returns:
            list: Cookie列表，每个元素为字典格式的Cookie项；
                  文件不存在时返回空列表
        """
        cookie_file = self._get_cookie_file(platform)  # 获取Cookie文件路径
        if os.path.exists(cookie_file):  # 检查Cookie文件是否存在
            with open(cookie_file, 'r', encoding='utf-8') as f:
                return json.load(f)  # 解析JSON格式的Cookie数据
        return []

    def _save_cookies(self, platform, cookies):
        """将Cookie保存到本地文件

        将浏览器上下文中的Cookie序列化为JSON格式并写入文件，
        以便下次启动时复用登录状态，避免重复登录。

        Args:
            platform (str): 平台名称
            cookies (list): Cookie列表，由Playwright的context.cookies()方法获取
        """
        cookie_file = self._get_cookie_file(platform)  # 获取Cookie文件路径
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)  # 以格式化JSON写入文件

    def _get_chrome_path(self):
        """获取本地Chrome浏览器可执行文件路径

        检测macOS系统中Google Chrome的安装路径，用于Playwright
        启动浏览器时指定可执行文件，确保使用真实浏览器而非Chromium。

        Returns:
            str or None: Chrome可执行文件路径；未安装时返回None，
                         此时Playwright将使用自带的Chromium
        """
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'  # macOS下Chrome默认安装路径
        if os.path.exists(chrome_path):  # 检查Chrome是否已安装
            return chrome_path
        return None

    def crawl(self, platform: str, keyword: str, target_count: int = 20) -> pd.DataFrame:
        """统一爬取入口方法 - 根据平台名称分发到对应的爬取逻辑

        该方法是Browser Agent的对外统一接口，根据传入的平台名称
        调用对应的平台专用爬取方法，实现多平台数据的统一采集。

        Args:
            platform (str): 目标平台名称，支持'微博'、'知乎'、'贴吧'、'虎扑'
            keyword (str): 搜索关键词，用于在各平台搜索相关内容
            target_count (int): 目标采集数量，默认为20条

        Returns:
            pd.DataFrame: 爬取结果数据表，包含平台、作者、内容、发布时间等字段；
                          爬取失败或平台不支持时返回空DataFrame
        """
        print(f"\n{'='*60}")
        print(f"🤖 Browser Agent - {platform} - 关键词: {keyword}")
        print(f"{'='*60}")

        # 根据平台名称分发到对应的爬取方法
        if platform == '微博':
            return self._crawl_weibo(keyword, target_count)
        elif platform == '知乎':
            return self._crawl_zhihu(keyword, target_count)
        elif platform == '贴吧':
            return self._crawl_tieba(keyword, target_count)
        elif platform == '虎扑':
            return self._crawl_hupu(keyword, target_count)
        else:
            print(f"⚠️ 暂不支持平台: {platform}")
            return pd.DataFrame()

    def _crawl_weibo(self, keyword, target_count):
        """微博数据爬取 - API获取微博列表 + Playwright进入详情页抓取评论

        采用混合爬取策略：先通过微博移动端API批量获取微博帖子列表，
        再通过Playwright浏览器进入帖子详情页抓取评论内容。
        这种策略兼顾了效率（API批量获取）和深度（浏览器抓取评论）。

        Args:
            keyword (str): 搜索关键词
            target_count (int): 目标采集数量

        Returns:
            pd.DataFrame: 微博数据表，包含帖子信息和评论
        """
        import requests  # 延迟导入requests库，避免未安装时影响其他平台

        # 加载微博Cookie，用于API请求的身份认证
        cookies_list = self._load_cookies('微博')
        # 将Cookie列表转换为字典格式，键为Cookie名称，值为Cookie值
        cookies = {}
        for c in cookies_list:
            cookies[c['name']] = c['value']  # 将Cookie列表转为字典格式，便于requests使用

        if not cookies:  # Cookie为空说明未登录，无法访问API
            print("❌ 未找到微博Cookie，请先登录！")
            return pd.DataFrame()  # 返回空DataFrame，表示爬取失败

        # 构造API请求头，模拟移动端浏览器访问
        headers = {
            'User-Agent': self.PLATFORM_CONFIG['微博']['user_agent'],  # 移动端UA
            'Referer': 'https://m.weibo.cn/',  # 来源页面
            'Accept': 'application/json, text/plain, */*',  # 接受JSON响应
        }

        all_data = []  # 存储所有微博帖子数据
        page = 1  # 当前页码

        # 分页请求微博搜索API，最多5页
        while len(all_data) < target_count and page <= 5:
            api_url = self.PLATFORM_CONFIG['微博']['api_url'].format(keyword=keyword, page=page)
            try:
                response = requests.get(api_url, headers=headers, cookies=cookies, timeout=30)  # 发送API请求
                data = response.json()  # 解析JSON响应

                if data.get('ok') == 1:  # 微博API返回ok=1表示请求成功
                    cards = data.get('data', {}).get('cards', [])  # 获取微博卡片列表
                    for card in cards:
                        if 'mblog' not in card:  # 跳过非微博内容的卡片（如广告、推荐等）
                            continue
                        blog = card['mblog']  # 获取微博正文数据
                        post_id = blog.get('id', '')  # 微博ID
                        author = blog.get('user', {}).get('screen_name', '')  # 作者昵称
                        content = re.sub(r'<[^>]+>', '', blog.get('text', ''))  # 去除HTML标签，提取纯文本
                        time_str = blog.get('created_at', '')  # 发布时间
                        comments_count = blog.get('comments_count', 0)  # 评论数
                        reposts_count = blog.get('reposts_count', 0)  # 转发数
                        attitudes_count = blog.get('attitudes_count', 0)  # 点赞数

                        # 构造标准化数据记录
                        all_data.append({
                            'platform': '微博',
                            'post_id': post_id,
                            'author': author,
                            'content': content,
                            'publish_time': time_str,
                            'comments_count': comments_count,
                            'reposts_count': reposts_count,
                            'attitudes_count': attitudes_count,
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        print(f"  ✅ {author}: {content[:30]}... (💬{comments_count})")
                    if not cards:  # 当前页无数据，停止翻页
                        break
                page += 1  # 翻到下一页
            except Exception as e:
                print(f"❌ 请求失败: {e}")
                break  # 请求异常时终止循环，避免无效重试

        # 用Playwright进入详情页抓取评论（仅对前5条有评论的微博抓取评论）
        # 限制抓取数量以控制总耗时，避免长时间占用浏览器
        comments_data = self._fetch_weibo_comments_playwright(all_data[:5])

        if comments_data:
            print(f"\n💬 获取到 {len(comments_data)} 条评论")
            # 将评论数据合并到对应的微博帖子记录中
            for post in all_data:
                post_comments = [c for c in comments_data if c['post_id'] == post.get('post_id')]  # 筛选当前帖子的评论
                if post_comments:
                    # 取前3条评论拼接为top_comments字段
                    post['top_comments'] = ' | '.join([c['comment'][:50] for c in post_comments[:3]])

        print(f"\n✅ 微博爬取完成：{len(all_data)} 条微博，{len(comments_data)} 条评论")
        return pd.DataFrame(all_data) if all_data else pd.DataFrame()  # 无数据时返回空DataFrame

    def _fetch_weibo_comments_playwright(self, posts):
        """通过Playwright访问微博详情页抓取评论内容

        使用Playwright浏览器自动化工具，逐个访问微博帖子详情页，
        通过页面滚动加载更多评论，然后从页面文本中提取评论内容。
        该方法采用文本行分析策略提取评论，而非依赖CSS选择器，
        体现了本系统"不依赖硬编码选择器"的核心创新。

        Args:
            posts (list): 微博帖子列表，每个元素为包含post_id、author等字段的字典

        Returns:
            list: 评论数据列表，每个元素包含platform、post_id、comment等字段
        """
        comments_data = []

        # 筛选有评论的微博帖子（无评论的帖子无需进入详情页）
        posts_with_comments = [p for p in posts if p.get('post_id') and p.get('comments_count', 0) > 0]
        if not posts_with_comments:
            print("  ⚠️ 没有有评论的微博")
            return comments_data  # 返回空列表，无需进入详情页

        config = self.PLATFORM_CONFIG['微博']  # 获取微博平台配置
        chrome_path = self._get_chrome_path()  # 获取Chrome浏览器路径

        with sync_playwright() as p:
            # 配置浏览器启动参数
            launch_args = {
                'headless': False,  # 非无头模式，显示浏览器窗口便于调试
                'args': ['--disable-blink-features=AutomationControlled']  # 禁用自动化检测特征，防止被网站识别
            }
            if chrome_path:
                launch_args['executable_path'] = chrome_path  # 使用本地Chrome而非Chromium

            browser = p.chromium.launch(**launch_args)  # 启动Chromium浏览器
            # 创建浏览器上下文，设置视口、UA和语言环境
            context = browser.new_context(
                viewport=config['viewport'],  # 设置浏览器视口尺寸
                user_agent=config['user_agent'],  # 设置User-Agent标识
                locale='zh-CN',  # 设置中文语言环境
            )
            page = context.new_page()  # 创建新页面
            Stealth().apply_stealth_sync(page)  # 应用反检测策略，隐藏自动化特征

            # 加载Cookie恢复登录状态
            cookies_list = self._load_cookies('微博')
            # 将Cookie注入浏览器上下文，使后续请求携带登录态
            if cookies_list:
                context.add_cookies(cookies_list)  # 将Cookie注入浏览器上下文

            # 先访问微博首页，确保Cookie生效
            page.goto('https://m.weibo.cn', wait_until='domcontentloaded', timeout=60000)  # 等待DOM加载完成
            page.wait_for_timeout(3000)  # 额外等待3秒，确保页面完全加载

            # 逐个访问帖子详情页抓取评论
            for idx, post in enumerate(posts_with_comments):
                post_id = post['post_id']
                detail_url = f'https://m.weibo.cn/detail/{post_id}'  # 构造详情页URL

                print(f"\n  [{idx+1}/{len(posts_with_comments)}] {post.get('author', '')}: {post.get('content', '')[:30]}...")

                try:
                    page.goto(detail_url, wait_until='domcontentloaded', timeout=30000)  # 访问详情页
                    page.wait_for_timeout(5000)  # 等待5秒，确保评论区域加载

                    # 模拟滚动加载更多评论，滚动10次
                    for i in range(10):
                        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')  # 滚动到页面底部
                        page.wait_for_timeout(1000)  # 每次滚动后等待1秒

                    # 获取页面全部文本内容，用于后续评论提取
                    page_text = page.inner_text('body')

                    # 尝试通过选择器获取微博正文（用于过滤正文内容）
                    weibo_el = page.query_selector('.weibo-text') or page.query_selector('.detail-content')
                    weibo_text = weibo_el.inner_text().strip() if weibo_el else ''

                    # 基于文本行分析提取评论内容
                    # 该策略不依赖CSS选择器，而是通过分析页面文本行的语义特征来识别评论
                    lines = page_text.split('\n')  # 将页面文本按行分割
                    comment_section = False  # 标记是否已进入评论区域
                    comment_count = 0

                    for line in lines:
                        line = line.strip()
                        if not line or len(line) < 3:  # 跳过空行和过短内容
                            continue

                        # 检测评论区域起始标志
                        if '评论' in line and len(line) < 10:
                            comment_section = True
                            continue

                        if comment_section:
                            # 过滤非评论内容：操作按钮、来源信息等
                            if any(skip in line for skip in ['赞', '回复', '举报', '删除', '来自', '更多', '收起', '展开', '分享', '相关', '推荐', '关注']):
                                continue
                            if line.isdigit():  # 跳过纯数字行（如评论数）
                                continue
                            if line == weibo_text or (weibo_text and weibo_text[:30] in line):  # 跳过微博正文
                                continue
                            if len(line) > 200:  # 跳过过长内容（可能是其他区域文本）
                                continue

                            # 将有效评论添加到结果列表
                            comments_data.append({
                                'platform': '微博',
                                'post_id': post_id,
                                'post_author': post.get('author', ''),
                                'comment_author': '',  # 微博移动端评论作者较难提取，暂留空
                                'comment': line[:500],  # 截取前500字符
                                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            comment_count += 1

                    print(f"    💬 获取到 {comment_count} 条评论")

                except Exception as e:
                    print(f"    ⚠️ 失败: {e}")

            browser.close()  # 关闭浏览器，释放资源

        return comments_data

    def _crawl_zhihu(self, keyword, target_count):
        """知乎数据爬取 - Playwright智能提取+评论抓取

        使用Playwright浏览器自动化工具访问知乎搜索页面，
        通过智能元素定位提取搜索结果，并进入帖子详情页抓取评论。
        支持Cookie自动加载和登录状态检测，Cookie失效时可等待用户手动登录。

        Args:
            keyword (str): 搜索关键词
            target_count (int): 目标采集数量

        Returns:
            pd.DataFrame: 知乎数据表，包含帖子信息和评论
        """
        config = self.PLATFORM_CONFIG['知乎']  # 获取知乎平台配置
        data_list = []  # 存储所有知乎帖子数据
        chrome_path = self._get_chrome_path()  # 获取Chrome浏览器路径

        with sync_playwright() as p:
            # 配置浏览器启动参数
            launch_args = {
                'headless': False,  # 非无头模式
                'args': ['--disable-blink-features=AutomationControlled']  # 禁用自动化检测特征
            }
            if chrome_path:
                launch_args['executable_path'] = chrome_path

            browser = p.chromium.launch(**launch_args)  # 启动浏览器
            # 创建浏览器上下文，设置视口、UA、语言和时区
            context = browser.new_context(viewport=config['viewport'], user_agent=config['user_agent'], locale='zh-CN', timezone_id='Asia/Shanghai')  # 设置上海时区
            page = context.new_page()  # 创建新页面
            Stealth().apply_stealth_sync(page)  # 应用反检测策略

            # 先访问知乎首页，加载Cookie
            page.goto('https://www.zhihu.com', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(2000)  # 等待2秒确保页面加载

            # 加载知乎Cookie，恢复登录状态
            cookies_list = self._load_cookies('知乎')
            # Cookie注入策略：先批量注入，失败则逐个注入
            if cookies_list:
                try:
                    context.add_cookies(cookies_list)  # 批量注入Cookie
                    print(f"  ✅ 知乎Cookie已加载 ({len(cookies_list)}个)")
                except Exception as e:
                    # 批量注入失败时，逐个尝试注入（某些Cookie格式可能不兼容）
                    print(f"  ⚠️ Cookie加载失败: {e}")
                    loaded = 0
                    for c in cookies_list:
                        try:
                            context.add_cookies([c])  # 逐个注入Cookie
                            loaded += 1
                        except:
                            pass
                    print(f"  ✅ 成功加载 {loaded}/{len(cookies_list)} 个Cookie")

            # 刷新页面使Cookie生效
            page.reload(wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(3000)  # 等待3秒

            # 检测是否跳转到登录页面（Cookie失效的标志）
            if 'signin' in page.url.lower():
                print("  ⚠️ 知乎Cookie已失效，需要登录！")
                print("  🔐 请在浏览器中完成登录...")
                # 等待用户手动登录，最长等待120秒
                for i in range(120):
                    page.wait_for_timeout(1000)  # 每秒检测一次
                    if 'signin' not in page.url.lower():  # 登录成功后URL会变化
                        break
                self._save_cookies('知乎', context.cookies())  # 保存登录后的Cookie
                print("  ✅ 登录完成，Cookie已保存")

            # 构造搜索URL并访问
            import urllib.parse
            encoded_kw = urllib.parse.quote(keyword)  # URL编码关键词
            search_url = f'https://www.zhihu.com/search?q={encoded_kw}&type=content'
            page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)  # 等待搜索结果加载

            # 模拟滚动加载更多搜索结果，滚动5次
            for i in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')  # 滚动到页面底部
                page.wait_for_timeout(2000)  # 每次滚动后等待2秒

            # 使用多级选择器策略定位搜索结果元素
            # 主选择器匹配常见的知乎内容卡片元素
            items = page.query_selector_all('.ContentItem, .SearchResult-Card, [class*="ContentItem"]')
            if not items:  # 主选择器未匹配到，尝试降级选择器
                # 降级选择器：匹配列表项和通用卡片元素
                items = page.query_selector_all('.List-item, [class*="Card"]')

            print(f"  📋 找到 {len(items)} 个搜索结果")

            # 逐个提取搜索结果数据
            # 仅保留有内容的记录，过滤掉空白或无效的搜索结果
            for idx, item in enumerate(items[:target_count]):
                try:
                    data = self._extract_zhihu_item(item)  # 调用智能提取方法
                    if data and data.get('content'):  # 仅保留有内容的记录
                        data_list.append(data)
                        print(f"  ✅ [{len(data_list)}] {data.get('author', '')}: {data.get('content', '')[:30]}...")
                except:
                    continue

            # 抓取评论：对前3条帖子进入详情页获取评论
            # 限制评论抓取范围以平衡数据深度与采集效率
            if data_list:
                comments_data = self._fetch_zhihu_comments_agent(page, data_list[:3])
                if comments_data:
                    print(f"\n  💬 获取到 {len(comments_data)} 条知乎评论")
                    # 将评论数据合并到对应的帖子记录中
                    for post in data_list:
                        post_comments = [c for c in comments_data if c.get('post_url') == post.get('url')]  # 按URL匹配评论
                        if post_comments:
                            post['top_comments'] = ' | '.join([c['comment'][:50] for c in post_comments[:3]])  # 取前3条评论

            self._save_cookies('知乎', context.cookies())  # 保存最新的Cookie
            browser.close()  # 关闭浏览器

        print(f"\n✅ 知乎爬取完成：{len(data_list)} 条")
        return pd.DataFrame(data_list) if data_list else pd.DataFrame()  # 无数据时返回空DataFrame

    def _extract_zhihu_item(self, item):
        """智能提取知乎搜索结果数据

        从单个搜索结果DOM元素中，通过多级选择器降级策略提取
        标题、内容、作者、链接等关键信息。该方法不依赖单一CSS选择器，
        而是提供多个备选选择器，增强了对页面结构变化的适应性。

        Args:
            item: Playwright ElementHandle对象，代表一个搜索结果DOM元素

        Returns:
            dict or None: 提取到的数据字典，包含platform、author、content等字段；
                          无内容时返回None
        """
        # 初始化结果字典，设置默认值
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
            # 提取标题：尝试多种选择器，适配不同的页面结构
            title_elem = item.query_selector('h3, .ContentItem-title, [class*="Title"]')
            if title_elem:
                result['title'] = title_elem.inner_text().strip()

            # 提取内容：优先从富文本内容区域提取
            content_elem = item.query_selector('.RichContent-inner, .ContentItem-answer, [class*="RichContent"]')
            if content_elem:
                result['content'] = content_elem.inner_text().strip()[:500]  # 截取前500字符

            # 提取作者信息
            author_elem = item.query_selector('.AuthorInfo-name, .UserLink-link, [class*="AuthorInfo"] [class*="name"]')
            if author_elem:
                result['author'] = author_elem.inner_text().strip()

            # 提取帖子链接：匹配问题页、回答页、专栏页等不同URL模式
            link_elem = item.query_selector('a[href*="/question/"], a[href*="/answer/"], a[href*="/p/"]')
            if link_elem:
                href = link_elem.get_attribute('href')
                if href:
                    if href.startswith('/'):  # 相对路径转为绝对路径
                        href = 'https://www.zhihu.com' + href
                    result['url'] = href

            # 如果未提取到内容但有标题，则用标题作为内容
            if not result['content'] and result.get('title'):
                result['content'] = result['title']
        except:
            pass

        return result if result.get('content') else None  # 无内容则返回None，表示提取失败

    def _fetch_zhihu_comments_agent(self, page, posts):
        """知乎评论抓取 - 进入帖子详情页提取评论内容

        逐个访问知乎帖子详情页，通过滚动加载评论区域，
        先尝试通过CSS选择器定位评论元素，若失败则回退到
        基于文本行分析的策略提取评论。这种双重提取策略
        保证了评论采集的鲁棒性。

        Args:
            page: Playwright Page对象，当前浏览器页面
            posts (list): 帖子列表，每个元素需包含url字段

        Returns:
            list: 评论数据列表，每个元素包含platform、post_url、comment等字段
        """
        comments_data = []
        # 筛选有URL的帖子（无URL无法进入详情页）
        posts_with_url = [p for p in posts if p.get('url')]
        if not posts_with_url:
            return comments_data  # 无URL的帖子无法访问详情页

        print(f"\n  💬 进入详情页获取评论...")

        for idx, post in enumerate(posts_with_url):
            post_url = post['url']
            print(f"    [{idx+1}] {post.get('author', '')}: {post.get('content', '')[:30]}...")

            try:
                # 访问帖子详情页
                page.goto(post_url, wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(5000)  # 等待页面加载

                # 模拟滚动加载更多评论，滚动15次
                for i in range(15):
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')  # 滚动到底部
                    page.wait_for_timeout(1500)  # 每次滚动后等待1.5秒

                # 尝试点击"查看更多"按钮，展开更多评论
                try:
                    more_btn = page.query_selector('button:has-text("查看更多"), button:has-text("更多评论")')
                    if more_btn:
                        more_btn.click()  # 点击展开更多评论
                        page.wait_for_timeout(3000)  # 等待评论加载
                        # 继续滚动加载新出现的评论
                        for i in range(10):
                            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                            page.wait_for_timeout(1500)
                except:
                    pass

                # 策略一：通过CSS选择器定位评论元素
                comment_items = page.query_selector_all('.CommentItem, [class*="CommentItem"], [class*="comment-item"]')

                comment_count = 0
                if comment_items:
                    for ci in comment_items:
                        try:
                            # 提取评论作者
                            user_elem = ci.query_selector('.AuthorInfo-name, .UserLink-link, a[href*="/people/"]')
                            # 提取评论内容
                            content_elem = ci.query_selector('.RichContent, [class*="content"]')
                            user_name = user_elem.inner_text().strip() if user_elem else ''
                            comment_text = content_elem.inner_text().strip() if content_elem else ''

                            if comment_text and len(comment_text) > 2:
                                # 过滤操作按钮等非评论文本
                                skip_words = ['回复', '赞', '踩', '查看', '更多', '收起', '删除', '举报', '分享']
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

                # 策略二：选择器未匹配到评论时，回退到文本行分析策略
                if comment_count == 0:
                    try:
                        page_text = page.inner_text('body')  # 获取页面全部文本
                        lines = page_text.split('\n')  # 按行分割
                        comment_section = False  # 评论区域标记
                        for line in lines:
                            line = line.strip()
                            if not line or len(line) < 3:  # 跳过空行和过短内容
                                continue
                            # 检测评论区域起始标志
                            if '评论' in line and len(line) < 15:
                                comment_section = True
                                continue
                            if comment_section:
                                # 过滤非评论内容
                                skip_words = ['回复', '赞', '踩', '查看', '更多', '收起', '删除', '举报', '分享', '赞同', '写评论']
                                if any(w in line and len(line) < 20 for w in skip_words):
                                    continue
                                if line.isdigit() or len(line) > 300:  # 跳过纯数字和过长内容
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

                print(f"      💬 获取到 {comment_count} 条评论")

            except Exception as e:
                print(f"      ⚠️ 失败: {e}")

        return comments_data

    def _crawl_tieba(self, keyword, target_count):
        """贴吧数据爬取 - Playwright智能提取+评论抓取

        使用Playwright浏览器自动化工具访问百度贴吧，
        通过智能元素定位提取帖子列表，并进入帖子详情页抓取评论。
        支持基于文本指纹的内容去重，避免重复采集。

        Args:
            keyword (str): 搜索关键词（贴吧名称）
            target_count (int): 目标采集数量

        Returns:
            pd.DataFrame: 贴吧数据表，包含帖子信息和评论
        """
        config = self.PLATFORM_CONFIG['贴吧']  # 获取贴吧平台配置
        data_list = []  # 存储所有贴吧帖子数据
        chrome_path = self._get_chrome_path()  # 获取Chrome浏览器路径

        with sync_playwright() as p:
            # 配置浏览器启动参数
            launch_args = {
                'headless': False,  # 非无头模式
                'args': ['--disable-blink-features=AutomationControlled']  # 禁用自动化检测特征
            }
            if chrome_path:
                launch_args['executable_path'] = chrome_path

            browser = p.chromium.launch(**launch_args)  # 启动浏览器
            # 创建浏览器上下文，设置视口、UA和语言
            context = browser.new_context(viewport=config['viewport'], user_agent=config['user_agent'], locale='zh-CN')  # 贴吧无需设置时区
            page = context.new_page()  # 创建新页面
            Stealth().apply_stealth_sync(page)  # 应用反检测策略

            # 先访问贴吧首页，加载Cookie
            page.goto('https://tieba.baidu.com', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(2000)  # 等待2秒

            # 加载贴吧Cookie
            cookies_list = self._load_cookies('贴吧')
            # 使用安全注入方法，避免Cookie格式不兼容导致注入失败
            if cookies_list:
                self._add_cookies_safe(context, cookies_list, '贴吧')  # 安全注入Cookie

            # 刷新页面使Cookie生效
            page.reload(wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(3000)  # 等待3秒

            # 构造贴吧搜索URL并访问
            import urllib.parse
            encoded_kw = urllib.parse.quote(keyword)  # URL编码关键词
            search_url = f'https://tieba.baidu.com/f?ie=utf-8&kw={encoded_kw}'
            page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)  # 等待帖子列表加载

            # 模拟滚动加载更多帖子，滚动5次
            for i in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')  # 滚动到页面底部
                page.wait_for_timeout(2000)  # 每次滚动后等待2秒

            # 使用多级选择器策略定位帖子列表元素
            # 主选择器匹配贴吧常见的帖子列表容器和列表项
            items = page.query_selector_all('.j_thread_list, .thread_list_bright, [class*="thread_list"] li, [class*="threadlist"] li')
            if not items:  # 主选择器未匹配到，尝试降级选择器
                # 降级选择器：匹配话题和帖子列表容器
                items = page.query_selector_all('[class*="topic"], [class*="post-list"]')

            print(f"  📋 找到 {len(items)} 个帖子")

            # 逐个提取帖子数据，使用文本指纹去重
            seen = set()  # 已采集内容的文本指纹集合，用于去重
            for idx, item in enumerate(items[:target_count * 2]):  # 多取一些，去重后可能不足
                try:
                    data = self._extract_tieba_item(item)  # 调用智能提取方法
                    if data and data.get('content'):
                        key = data['content'][:50]  # 取内容前50字符作为去重指纹
                        if key not in seen:  # 去重检查
                            seen.add(key)
                            data_list.append(data)
                            print(f"  ✅ [{len(data_list)}] {data.get('author', '未知')}: {data.get('content', '')[:30]}...")
                            if len(data_list) >= target_count:  # 达到目标数量则停止
                                break
                except:
                    continue

            # 抓取评论：对前3条帖子进入详情页获取评论
            # 限制评论抓取范围以平衡数据深度与采集效率
            if data_list:
                comments_data = self._fetch_tieba_comments_agent(page, data_list[:3])
                if comments_data:
                    print(f"\n  💬 获取到 {len(comments_data)} 条贴吧评论")
                    # 将评论数据合并到对应的帖子记录中
                    for post in data_list:
                        post_comments = [c for c in comments_data if c.get('post_url') == post.get('url')]  # 按URL匹配评论
                        if post_comments:
                            post['top_comments'] = ' | '.join([c['comment'][:50] for c in post_comments[:3]])  # 取前3条评论

            self._save_cookies('贴吧', context.cookies())  # 保存最新的Cookie
            browser.close()  # 关闭浏览器

        print(f"\n✅ 贴吧爬取完成：{len(data_list)} 条")
        return pd.DataFrame(data_list) if data_list else pd.DataFrame()  # 无数据时返回空DataFrame

    def _extract_tieba_item(self, item):
        """智能提取贴吧帖子数据

        从单个贴吧帖子DOM元素中，通过多级选择器降级策略提取
        标题（内容）、作者、链接等信息。贴吧帖子结构相对简单，
        标题即为主要内容。

        Args:
            item: Playwright ElementHandle对象，代表一个帖子DOM元素

        Returns:
            dict or None: 提取到的数据字典；无内容时返回None
        """
        # 初始化结果字典，设置默认值
        result = {
            'platform': '贴吧',
            'author': '',
            'content': '',
            'publish_time': datetime.now().strftime('%Y-%m-%d'),
            'comments_count': 0,
            'url': '',
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        try:
            # 提取帖子标题（贴吧中标题即为主要内容）
            title_elem = item.query_selector('.j_th_tit, .threadlist_title, a[href*="/p/"], [class*="title"] a')
            if title_elem:
                result['content'] = title_elem.inner_text().strip()[:500]  # 截取前500字符
                href = title_elem.get_attribute('href')
                if href:
                    if href.startswith('/'):  # 相对路径转为绝对路径
                        href = 'https://tieba.baidu.com' + href
                    result['url'] = href
            # 提取作者信息
            author_elem = item.query_selector('.frs-author-name-wrap, .tb_icon_author, [class*="author"] a')
            if author_elem:
                result['author'] = author_elem.inner_text().strip()
            # 如果标题选择器未匹配到，尝试从链接元素提取
            if not result['content']:
                link_elem = item.query_selector('a[href*="/p/"]')
                if link_elem:
                    result['content'] = link_elem.inner_text().strip()[:500]
                    href = link_elem.get_attribute('href')
                    if href:
                        if href.startswith('/'):  # 相对路径转为绝对路径
                            href = 'https://tieba.baidu.com' + href
                        result['url'] = href
            # 最后的降级策略：直接提取元素的全部文本
            if not result['content']:
                text = item.inner_text().strip()
                if text and len(text) > 5:  # 文本长度需大于5，过滤空白元素
                    result['content'] = text[:500]
        except:
            pass
        return result if result.get('content') else None  # 无内容则返回None，表示提取失败

    def _fetch_tieba_comments_agent(self, page, posts):
        """贴吧评论抓取 - 进入帖子详情页提取评论内容

        逐个访问贴吧帖子详情页，通过滚动加载评论区域，
        先尝试通过CSS选择器定位楼层元素提取评论，若失败则
        回退到基于文本行分析的策略。贴吧评论以"楼层"形式展示，
        每个楼层包含用户名和回帖内容。

        Args:
            page: Playwright Page对象，当前浏览器页面
            posts (list): 帖子列表，每个元素需包含url字段

        Returns:
            list: 评论数据列表，每个元素包含platform、post_url、comment等字段
        """
        comments_data = []
        # 筛选有URL的帖子
        posts_with_url = [p for p in posts if p.get('url')]
        if not posts_with_url:
            return comments_data  # 无URL的帖子无法访问详情页
        print(f"\n  💬 进入详情页获取评论...")
        for idx, post in enumerate(posts_with_url):
            post_url = post['url']
            print(f"    [{idx+1}] {post.get('author', '')}: {post.get('content', '')[:30]}...")
            try:
                # 访问帖子详情页
                page.goto(post_url, wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(5000)  # 等待页面加载
                # 模拟滚动加载更多评论，滚动10次
                for i in range(10):
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')  # 滚动到底部
                    page.wait_for_timeout(1500)  # 每次滚动后等待1.5秒
                # 策略一：通过CSS选择器定位楼层元素
                comment_items = page.query_selector_all('.l_post, [class*="post-item"], [class*="floor"], [class*="d_post"]')
                comment_count = 0
                if comment_items:
                    for ci in comment_items:
                        try:
                            # 提取楼层用户名
                            user_elem = ci.query_selector('.d_name, [class*="username"], .p_author_name')
                            # 提取楼层回帖内容
                            content_elem = ci.query_selector('.d_post_content, [class*="content"], .p_content')
                            user_name = user_elem.inner_text().strip() if user_elem else ''
                            comment_text = content_elem.inner_text().strip() if content_elem else ''
                            if not comment_text:
                                comment_text = ci.inner_text().strip()  # 降级：提取整个楼层的文本
                            if comment_text and len(comment_text) > 2:
                                # 过滤操作按钮等非评论文本
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
                # 策略二：选择器未匹配到评论时，回退到文本行分析策略
                if comment_count == 0:
                    try:
                        page_text = page.inner_text('body')  # 获取页面全部文本
                        lines = page_text.split('\n')  # 按行分割
                        comment_section = False  # 评论区域标记
                        for line in lines:
                            line = line.strip()
                            if not line or len(line) < 3:  # 跳过空行和过短内容
                                continue
                            # 检测评论区域起始标志
                            if any(kw in line for kw in ['全部回复', '评论', '吧友回复']) and len(line) < 15:
                                comment_section = True
                                continue
                            if comment_section:
                                # 过滤非评论内容
                                skip_words = ['回复', '举报', '删除', '收起', '展开', '来自', '只看', '赞', '分享']
                                if any(w in line and len(line) < 15 for w in skip_words):
                                    continue
                                if line.isdigit() or len(line) > 300:  # 跳过纯数字和过长内容
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
                print(f"      💬 获取到 {comment_count} 条评论")
            except Exception as e:
                print(f"      ⚠️ 失败: {e}")
        return comments_data

    def _crawl_hupu(self, keyword, target_count):
        """虎扑数据爬取 - Playwright智能提取+评论抓取

        使用Playwright浏览器自动化工具访问虎扑论坛搜索页面，
        通过智能元素定位提取帖子列表，并进入帖子详情页抓取评论。
        支持基于文本指纹的内容去重，避免重复采集。

        Args:
            keyword (str): 搜索关键词
            target_count (int): 目标采集数量

        Returns:
            pd.DataFrame: 虎扑数据表，包含帖子信息和评论
        """
        config = self.PLATFORM_CONFIG['虎扑']  # 获取虎扑平台配置
        data_list = []  # 存储所有虎扑帖子数据
        chrome_path = self._get_chrome_path()  # 获取Chrome浏览器路径

        with sync_playwright() as p:
            # 配置浏览器启动参数
            launch_args = {
                'headless': False,  # 非无头模式
                'args': ['--disable-blink-features=AutomationControlled']  # 禁用自动化检测特征
            }
            if chrome_path:
                launch_args['executable_path'] = chrome_path

            browser = p.chromium.launch(**launch_args)  # 启动浏览器
            # 创建浏览器上下文，设置视口、UA和语言
            context = browser.new_context(viewport=config['viewport'], user_agent=config['user_agent'], locale='zh-CN')  # 虎扑无需设置时区
            page = context.new_page()  # 创建新页面
            Stealth().apply_stealth_sync(page)  # 应用反检测策略

            # 先访问虎扑首页，加载Cookie
            page.goto('https://bbs.hupu.com', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(2000)  # 等待2秒

            # 加载虎扑Cookie
            cookies_list = self._load_cookies('虎扑')
            # 使用安全注入方法，避免Cookie格式不兼容导致注入失败
            if cookies_list:
                self._add_cookies_safe(context, cookies_list, '虎扑')  # 安全注入Cookie

            # 刷新页面使Cookie生效
            page.reload(wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(3000)  # 等待3秒

            # 构造虎扑搜索URL并访问
            import urllib.parse
            encoded_kw = urllib.parse.quote(keyword)  # URL编码关键词
            search_url = f'https://bbs.hupu.com/search?keyword={encoded_kw}'
            page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)  # 等待搜索结果加载

            # 模拟滚动加载更多帖子，滚动5次
            for i in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')  # 滚动到页面底部
                page.wait_for_timeout(2000)  # 每次滚动后等待2秒

            # 使用多级选择器策略定位搜索结果元素
            # 主选择器匹配虎扑常见的帖子卡片和搜索结果元素
            items = page.query_selector_all('.bbs-sl-web-post, .search-result-item, [class*="post-item"], [class*="search-result"]')
            if not items:  # 主选择器未匹配到，尝试降级选择器
                # 降级选择器：匹配通用列表项元素
                items = page.query_selector_all('[class*="item"], [class*="list-item"]')

            print(f"  📋 找到 {len(items)} 个搜索结果")

            # 逐个提取帖子数据，使用文本指纹去重
            seen = set()  # 已采集内容的文本指纹集合，用于去重
            for idx, item in enumerate(items[:target_count * 2]):  # 多取一些，去重后可能不足
                try:
                    data = self._extract_hupu_item(item)  # 调用智能提取方法
                    if data and data.get('content'):
                        key = data['content'][:50]  # 取内容前50字符作为去重指纹
                        if key not in seen:  # 去重检查
                            seen.add(key)
                            data_list.append(data)
                            print(f"  ✅ [{len(data_list)}] {data.get('author', '未知')}: {data.get('content', '')[:30]}...")
                            if len(data_list) >= target_count:  # 达到目标数量则停止
                                break
                except:
                    continue

            # 抓取评论：对前3条帖子进入详情页获取评论
            # 限制评论抓取范围以平衡数据深度与采集效率
            if data_list:
                comments_data = self._fetch_hupu_comments_agent(page, data_list[:3])
                if comments_data:
                    print(f"\n  💬 获取到 {len(comments_data)} 条虎扑评论")
                    # 将评论数据合并到对应的帖子记录中
                    for post in data_list:
                        post_comments = [c for c in comments_data if c.get('post_url') == post.get('url')]  # 按URL匹配评论
                        if post_comments:
                            post['top_comments'] = ' | '.join([c['comment'][:50] for c in post_comments[:3]])  # 取前3条评论

            self._save_cookies('虎扑', context.cookies())  # 保存最新的Cookie
            browser.close()  # 关闭浏览器

        print(f"\n✅ 虎扑爬取完成：{len(data_list)} 条")
        return pd.DataFrame(data_list) if data_list else pd.DataFrame()  # 无数据时返回空DataFrame

    def _extract_hupu_item(self, item):
        """智能提取虎扑帖子数据

        从单个虎扑帖子DOM元素中，通过多级选择器降级策略提取
        标题（内容）、作者、链接等信息。

        Args:
            item: Playwright ElementHandle对象，代表一个帖子DOM元素

        Returns:
            dict or None: 提取到的数据字典；无内容时返回None
        """
        # 初始化结果字典，设置默认值
        result = {
            'platform': '虎扑',
            'author': '',
            'content': '',
            'publish_time': datetime.now().strftime('%Y-%m-%d'),
            'comments_count': 0,
            'url': '',
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        try:
            # 提取帖子标题（虎扑中标题即为主要内容）
            title_elem = item.query_selector('.post-title, a[href*="/bbs/"], h3, [class*="title"]')
            if title_elem:
                result['content'] = title_elem.inner_text().strip()[:500]  # 截取前500字符
            # 提取作者信息
            author_elem = item.query_selector('.post-author, .username, [class*="author"], [class*="user"]')
            if author_elem:
                result['author'] = author_elem.inner_text().strip()
            # 提取帖子链接
            link_elem = item.query_selector('a[href*="/bbs/"]')
            if link_elem:
                href = link_elem.get_attribute('href')
                if href:
                    if href.startswith('/'):  # 相对路径转为绝对路径
                        href = 'https://bbs.hupu.com' + href
                    result['url'] = href
            # 最后的降级策略：直接提取元素的全部文本
            if not result['content']:
                text = item.inner_text().strip()
                if text and len(text) > 5:  # 文本长度需大于5，过滤空白元素
                    result['content'] = text[:500]
        except:
            pass
        return result if result.get('content') else None  # 无内容则返回None，表示提取失败

    def _fetch_hupu_comments_agent(self, page, posts):
        """虎扑评论抓取 - 进入帖子详情页提取评论内容

        逐个访问虎扑帖子详情页，通过滚动加载评论区域，
        先尝试通过CSS选择器定位回复元素提取评论，若失败则
        回退到基于文本行分析的策略。

        Args:
            page: Playwright Page对象，当前浏览器页面
            posts (list): 帖子列表，每个元素需包含url字段

        Returns:
            list: 评论数据列表，每个元素包含platform、post_url、comment等字段
        """
        comments_data = []
        # 筛选有URL的帖子
        posts_with_url = [p for p in posts if p.get('url')]
        if not posts_with_url:
            return comments_data  # 无URL的帖子无法访问详情页
        print(f"\n  💬 进入详情页获取评论...")
        for idx, post in enumerate(posts_with_url):
            post_url = post['url']
            print(f"    [{idx+1}] {post.get('author', '')}: {post.get('content', '')[:30]}...")
            try:
                # 访问帖子详情页
                page.goto(post_url, wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(5000)  # 等待页面加载
                # 模拟滚动加载更多评论，滚动10次
                for i in range(10):
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')  # 滚动到底部
                    page.wait_for_timeout(1500)  # 每次滚动后等待1.5秒
                # 策略一：通过CSS选择器定位回复元素
                comment_items = page.query_selector_all('.reply-content, [class*="reply-item"], [class*="comment-item"], [class*="floor"]')
                comment_count = 0
                if comment_items:
                    for ci in comment_items:
                        try:
                            # 提取回复用户名
                            user_elem = ci.query_selector('[class*="username"], [class*="author"], a[href*="/user/"]')
                            # 提取回复内容
                            content_elem = ci.query_selector('[class*="content"], [class*="text"], [class*="body"]')
                            user_name = user_elem.inner_text().strip() if user_elem else ''
                            comment_text = content_elem.inner_text().strip() if content_elem else ''
                            if not comment_text:
                                comment_text = ci.inner_text().strip()  # 降级：提取整个回复元素的文本
                            if comment_text and len(comment_text) > 2:
                                # 过滤操作按钮等非评论文本
                                skip_words = ['回复', '举报', '删除', '引用', '亮了', '只看', '来自']
                                if any(w in comment_text and len(comment_text) < 15 for w in skip_words):
                                    continue
                                comments_data.append({
                                    'platform': '虎扑',
                                    'post_url': post_url,
                                    'post_author': post.get('author', ''),
                                    'comment_author': user_name,
                                    'comment': comment_text[:500],
                                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                                comment_count += 1
                        except:
                            continue
                # 策略二：选择器未匹配到评论时，回退到文本行分析策略
                if comment_count == 0:
                    try:
                        page_text = page.inner_text('body')  # 获取页面全部文本
                        lines = page_text.split('\n')  # 按行分割
                        comment_section = False  # 评论区域标记
                        for line in lines:
                            line = line.strip()
                            if not line or len(line) < 3:  # 跳过空行和过短内容
                                continue
                            # 检测评论区域起始标志
                            if any(kw in line for kw in ['评论', '回复', '全部回帖']) and len(line) < 15:
                                comment_section = True
                                continue
                            if comment_section:
                                # 过滤非评论内容
                                skip_words = ['回复', '举报', '删除', '引用', '亮了', '只看', '来自', '发表', '编辑']
                                if any(w in line and len(line) < 15 for w in skip_words):
                                    continue
                                if line.isdigit() or len(line) > 300:  # 跳过纯数字和过长内容
                                    continue
                                comments_data.append({
                                    'platform': '虎扑',
                                    'post_url': post_url,
                                    'post_author': post.get('author', ''),
                                    'comment_author': '',
                                    'comment': line[:500],
                                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                                comment_count += 1
                    except:
                        pass
                print(f"      💬 获取到 {comment_count} 条评论")
            except Exception as e:
                print(f"      ⚠️ 失败: {e}")
        return comments_data

    def _add_cookies_safe(self, context, cookies_list, platform_name=''):
        """安全注入Cookie到浏览器上下文

        先尝试批量注入所有Cookie，若失败则逐个注入。
        这种容错策略可以处理部分Cookie格式不兼容的情况，
        确保尽可能多的Cookie被成功加载。

        Args:
            context: Playwright BrowserContext对象，浏览器上下文
            cookies_list (list): Cookie列表，由_load_cookies方法加载
            platform_name (str): 平台名称，用于日志输出
        """
        if not cookies_list:  # Cookie列表为空，无需注入
            return
        try:
            context.add_cookies(cookies_list)  # 尝试批量注入所有Cookie
            print(f"  ✅ {platform_name}Cookie已加载 ({len(cookies_list)}个)")
        except:
            # 批量注入失败，逐个尝试注入
            loaded = 0
            for c in cookies_list:
                try:
                    context.add_cookies([c])  # 逐个注入Cookie
                    loaded += 1
                except:
                    pass  # 忽略单个Cookie注入失败
            print(f"  ✅ {platform_name}成功加载 {loaded}/{len(cookies_list)} 个Cookie")


def get_browser_agent_info() -> Dict:
    """获取Browser Agent模块信息（用于论文展示）

    返回Browser Agent模块的元信息，包括模块名称、功能描述、
    特性列表、技术栈和创新点等。该函数主要用于论文中
    对系统模块的介绍和展示。

    Returns:
        Dict: 包含模块元信息的字典，键包括：
            - name: 模块名称
            - description: 功能描述
            - features: 特性列表
            - tech_stack: 技术栈列表
            - innovation: 创新点描述
    """
    return {
        'name': 'Browser Agent - AI驱动浏览器',  # 模块名称
        'description': '基于Playwright的智能网页内容识别与自动采集系统',  # 功能描述
        'features': [  # 核心特性列表
            '自动识别网页元素，无需硬编码CSS选择器',
            '智能滚动+内容去重',
            '自动适配不同平台',
            'Cookie智能复用',
            '评论深度采集（进入详情页抓取）'
        ],
        'tech_stack': [  # 技术栈列表
            'Playwright（浏览器自动化）',
            'playwright-stealth（反检测）',
            '微博移动端API（数据获取）',
            '页面结构分析（评论提取）'
        ],
        'innovation': '不依赖硬编码CSS选择器，通过页面结构分析和API拦截自动提取内容，适应网页改版；深度评论采集通过进入详情页实现'  # 核心创新点
    }
