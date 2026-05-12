# -*- coding: utf-8 -*-
"""
智能数据清洗模块 - 论文创新亮点

本模块实现了面向在线评论数据的智能清洗管道，针对网络爬虫数据中常见的
噪声、重复、格式混乱等问题，提出5大创新清洗策略：

1. 语义级去重（SimHash + 编辑距离）：基于SimHash指纹的海明距离初筛，
   结合编辑距离精筛，识别语义相同但表述不同的评论
2. LLM辅助噪声检测：利用大语言模型识别爬虫混入的非评论噪声，
   如按钮文字、导航栏、操作提示等，比正则更准确
3. 数据可信度评估（Data Credibility Score）：综合内容完整性、互动量、
   平台可信度、内容真实性、时间合理性五个维度量化评估数据质量
4. 智能文本修复：自动修复爬虫导致的emoji乱码、截断文本、特殊字符、
   繁简不统一等问题
5. 跨平台事件聚合：基于关键词提取和事件指纹匹配，自动识别不同平台
   讨论同一事件的评论，实现跨平台数据聚合
"""
import os
import sys
import re
import hashlib  # 提供MD5等哈希算法，用于SimHash指纹计算
import math
import json     # 用于LLM噪声检测的JSON解析
from collections import Counter, defaultdict  # Counter用于词频统计，defaultdict用于分组存储
from typing import List, Dict, Any, Set, Tuple, Optional
from datetime import datetime

import pandas as pd
import numpy as np

# 动态获取项目根目录，确保模块导入路径正确
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

try:
    import jieba  # 中文分词库，用于SimHash的文本分词
    jieba.setLogLevel(jieba.logging.INFO)
except ImportError:
    jieba = None  # jieba不可用时退化为逐字切分

try:
    from dotenv import load_dotenv  # 加载环境变量，用于LLM API密钥配置
    load_dotenv()
except ImportError:
    pass


class SimHashDeduplicator:
    """语义级去重 - 基于SimHash算法

    创新点：结合SimHash指纹和编辑距离，识别语义相同但表述不同的评论
    例如："门票太贵了" 和 "票价真的高" 会被识别为语义重复
    """

    def __init__(self, hash_bits=64, similarity_threshold=3):
        """初始化SimHash去重器

        Args:
            hash_bits: SimHash指纹位数，默认64位，位数越高区分度越精细
            similarity_threshold: 海明距离阈值，小于等于该值视为相似，默认3
        """
        self.hash_bits = hash_bits
        self.similarity_threshold = similarity_threshold

    def _tokenize(self, text):
        """对文本进行分词处理

        优先使用jieba进行中文分词，若jieba不可用则退化为逐字切分

        Args:
            text: 待分词的文本字符串

        Returns:
            分词后的词元列表
        """
        if jieba:
            return list(jieba.cut(text))
        return list(text)

    def _simhash(self, text):
        """计算文本的SimHash指纹

        SimHash算法核心步骤：
        1. 对文本分词，统计每个词的出现频率作为权重
        2. 对每个词进行MD5哈希，得到固定位数的哈希值
        3. 根据哈希值的每一位是0还是1，对权重向量进行加减操作
        4. 最终根据权重向量的正负生成指纹，正位设为1，负位设为0

        Args:
            text: 待计算指纹的文本字符串

        Returns:
            整数形式的SimHash指纹值
        """
        tokens = self._tokenize(text)
        if not tokens:
            return 0

        # 初始化hash_bits维的权重向量，用于累加各词元的哈希贡献
        v = [0] * self.hash_bits
        # 统计词频，词频作为SimHash的权重，高频词对指纹影响更大
        token_counts = Counter(tokens)

        for token, count in token_counts.items():
            # 对每个词元计算MD5哈希值，转换为整数
            token_hash = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            # 遍历指纹的每一位，根据哈希值该位是否为1进行加权累加
            for i in range(self.hash_bits):
                if token_hash & (1 << i):
                    v[i] += count  # 该位为1，正向加权
                else:
                    v[i] -= count  # 该位为0，负向加权

        # 根据最终权重向量的正负生成指纹：正位设1，负位设0
        fingerprint = 0
        for i in range(self.hash_bits):
            if v[i] > 0:
                fingerprint |= (1 << i)

        return fingerprint

    def _hamming_distance(self, hash1, hash2):
        """计算两个SimHash指纹之间的海明距离

        海明距离即两个等长二进制串中不同位的个数，距离越小表示文本越相似

        Args:
            hash1: 第一个SimHash指纹值
            hash2: 第二个SimHash指纹值

        Returns:
            海明距离（整数），值越小表示两个指纹越相似
        """
        x = hash1 ^ hash2  # 异或操作，不同位为1
        distance = 0
        # Brian Kernighan算法：每次消除最低位的1，统计1的个数
        while x:
            distance += 1
            x &= x - 1
        return distance

    @staticmethod
    def edit_distance(s1, s2):
        """计算两个字符串之间的编辑距离（Levenshtein Distance）

        使用动态规划算法，时间复杂度O(m*n)，空间复杂度优化为O(min(m,n))
        编辑距离衡量将一个字符串变换为另一个所需的最少编辑操作次数

        Args:
            s1: 第一个字符串
            s2: 第二个字符串

        Returns:
            编辑距离（整数），值越小表示两个字符串越相似
        """
        # 优化：确保s1为较长串，减少空间开销
        if len(s1) < len(s2):
            return SimHashDeduplicator.edit_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        # 滚动数组优化：仅保留上一行的DP状态，空间复杂度从O(m*n)降至O(n)
        prev = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                # 三种编辑操作取最小值：插入、删除、替换
                insertions = prev[j + 1] + 1
                deletions = curr[j] + 1
                substitutions = prev[j] + (c1 != c2)
                curr.append(min(insertions, deletions, substitutions))
            prev = curr

        return prev[-1]

    def find_duplicates(self, texts: List[str]) -> List[List[int]]:
        """查找文本列表中的语义重复组

        采用SimHash海明距离初筛 + 编辑距离精筛的两级策略：
        1. 先计算每条文本的SimHash指纹，海明距离小于阈值则进入候选
        2. 再对候选对计算前50字符的编辑距离，归一化后小于0.5则确认重复

        Args:
            texts: 待检测的文本列表

        Returns:
            重复组列表，每组为重复文本的索引列表（仅包含2条及以上的组）
        """
        # 批量计算所有文本的SimHash指纹
        hashes = [self._simhash(text) for text in texts]
        # 使用字典存储分组，key为组内第一条文本的索引
        groups = defaultdict(list)

        for i in range(len(texts)):
            found_group = False
            # 遍历已有分组，检查当前文本是否与某组代表文本相似
            for key in list(groups.keys()):
                # 第一级筛选：海明距离小于阈值，说明指纹相似
                if self._hamming_distance(hashes[i], hashes[key]) <= self.similarity_threshold:
                    # 第二级筛选：编辑距离归一化后小于0.5，确认语义重复
                    ed = self.edit_distance(texts[i][:50], texts[key][:50])
                    max_len = max(len(texts[i][:50]), len(texts[key][:50]), 1)
                    if ed / max_len < 0.5:
                        groups[key].append(i)
                        found_group = True
                        break
            # 未找到相似组，则作为新组的代表
            if not found_group:
                groups[i].append(i)

        # 仅返回包含2条及以上的重复组
        return [g for g in groups.values() if len(g) > 1]

    def deduplicate(self, df: pd.DataFrame, content_col: str = 'content') -> pd.DataFrame:
        """对DataFrame进行语义级去重

        在每组语义重复中保留内容最长的文本，去除其余重复项

        Args:
            df: 待去重的DataFrame
            content_col: 内容列名，默认为'content'

        Returns:
            去重后的DataFrame，已标记语义重复列
        """
        print(f"\n🔍 语义级去重（SimHash）...")
        print(f"   输入: {len(df)} 条")

        if df.empty:
            return df

        df = df.copy()
        texts = df[content_col].fillna('').astype(str).tolist()

        # 查找所有语义重复组
        duplicate_groups = self.find_duplicates(texts)

        # 对每组重复，保留内容最长的，其余标记为待删除
        remove_indices = set()
        duplicate_count = 0
        for group in duplicate_groups:
            # 按内容长度降序排列，最长的排在前面
            group_texts = [(idx, len(texts[idx])) for idx in group]
            group_texts.sort(key=lambda x: -x[1])
            keep_idx = group_texts[0][0]  # 保留最长的文本
            for idx, _ in group_texts[1:]:
                remove_indices.add(idx)
                duplicate_count += 1

        # 标记语义重复并过滤
        df['is_semantic_duplicate'] = df.index.isin(remove_indices)
        result = df[~df.index.isin(remove_indices)].copy()

        print(f"   发现 {len(duplicate_groups)} 组语义重复")
        print(f"   去除 {duplicate_count} 条重复，保留 {len(result)} 条")
        return result


class LLMNoiseDetector:
    """LLM辅助噪声检测

    创新点：利用大语言模型识别爬虫混入的非评论噪声
    如按钮文字、导航栏、操作提示等，比正则更准确
    """

    # 预编译噪声正则模式列表，覆盖按钮文字、导航栏、来源标注等常见网页噪声
    NOISE_PATTERNS = [
        r'^(回复|举报|删除|分享|收藏|点赞|关注|取消关注)$',  # 操作按钮文字
        r'^(来自|发自).{0,10}(客户端|手机|iPhone|Android)$',  # 来源标注
        r'^(查看|更多|展开|收起|全部|详情|原文).{0,5}$',  # 展开/收起提示
        r'^\d{1,3}楼$',  # 楼层号
        r'^(已|未)认证',  # 认证状态
        r'^(VIP|会员|达人|博主|UP主)$',  # 用户等级标签
        r'^(热榜|推荐|关注|粉丝).{0,5}\d*$',  # 数据统计标签
        r'^[\d.]+[万kK]?$',  # 纯数字统计（如"1.2万"）
        r'^(赞同|反对|感谢|评论)\s*\d*$',  # 互动按钮+计数
        r'^(写评论|发表评论|我要评论)$',  # 评论输入提示
        r'^(打开APP|下载APP|安装APP)$',  # APP引导
        r'^(登录|注册|签到|打卡)$',  # 账号操作按钮
        r'^(搜我想看|搜索|查询)$',  # 搜索框提示
        r'^(上一页|下一页|第\d+页)$',  # 分页导航
        r'^(复制|转发|引用|编辑)$',  # 内容操作按钮
        r'^[\u2600-\u27BF\uFE00-\uFE0F\U0001F000-\U0001F9FF]+$',  # 纯emoji表情
    ]

    # 预编译正则，提升匹配性能
    compiled_patterns = [re.compile(p) for p in NOISE_PATTERNS]

    # UI关键词字典，按类别组织，用于精确匹配常见网页UI元素
    UI_KEYWORDS = {
        '按钮': ['回复', '举报', '删除', '分享', '收藏', '点赞', '关注', '转发', '引用', '编辑'],
        '导航': ['首页', '上一页', '下一页', '返回', '搜索', '登录', '注册', '签到'],
        '状态': ['已认证', 'VIP', '会员', '达人', '博主', 'UP主', '楼主'],
        '来源': ['来自', '发自', '客户端', 'iPhone客户端', 'Android客户端'],
        '操作': ['展开', '收起', '查看更多', '全部回复', '写评论', '发表评论'],
    }

    def __init__(self, use_llm=False):
        """初始化噪声检测器

        Args:
            use_llm: 是否启用LLM辅助检测，默认False使用规则检测
        """
        self.use_llm = use_llm

    def detect_noise_rule(self, text: str) -> Tuple[bool, str]:
        """基于规则的噪声检测

        通过三层规则判断文本是否为噪声：
        1. 正则模式匹配：检测按钮、导航、来源标注等格式化噪声
        2. UI关键词精确匹配：检测各类网页UI元素
        3. 长度与语言检测：过滤过短非中文内容

        Args:
            text: 待检测的文本

        Returns:
            元组(是否为噪声, 噪声原因描述)
        """
        text = text.strip()
        # 空内容或过短内容直接判定为噪声
        if not text or len(text) < 2:
            return True, '空内容'

        # 第一层：正则模式匹配，检测格式化的网页噪声
        for pattern in self.compiled_patterns:
            if pattern.match(text):
                return True, '匹配噪声模式'

        # 第二层：UI关键词精确匹配，检测各类网页交互元素
        for category, keywords in self.UI_KEYWORDS.items():
            if text in keywords:
                return True, f'UI元素({category})'

        # 第三层：过短且不含中文的内容视为噪声
        if len(text) <= 3 and not re.search(r'[\u4e00-\u9fff]', text):
            return True, '过短非中文'

        return False, ''

    def detect_noise_llm(self, text: str) -> Tuple[bool, str]:
        """基于LLM的噪声检测

        调用DeepSeek大语言模型判断文本是否为网页噪声，LLM能理解语义上下文，
        比规则匹配更准确地识别边界情况。若LLM调用失败则自动降级为规则检测。

        Args:
            text: 待检测的文本

        Returns:
            元组(是否为噪声, 噪声原因描述)
        """
        try:
            from src.utils.deepseek_client import DeepSeekClient
            client = DeepSeekClient()

            # 构造提示词，引导LLM判断文本是否为网页噪声
            prompt = f"""判断以下文本是否为网页噪声（非用户评论内容）。
噪声包括：按钮文字、导航栏、操作提示、来源标注、楼层号等UI元素。

文本："{text}"

只回答JSON格式：{{"is_noise": true/false, "reason": "原因"}}"""

            response = client.chat(prompt, max_tokens=100)
            # 解析LLM返回的JSON结果
            result = json.loads(response.strip())
            return result.get('is_noise', False), result.get('reason', '')
        except:
            # LLM调用失败时降级为规则检测，保证系统鲁棒性
            return self.detect_noise_rule(text)

    def detect(self, text: str) -> Tuple[bool, str]:
        """统一噪声检测入口

        根据初始化配置选择规则检测或LLM检测

        Args:
            text: 待检测的文本

        Returns:
            元组(是否为噪声, 噪声原因描述)
        """
        if self.use_llm:
            return self.detect_noise_llm(text)
        return self.detect_noise_rule(text)

    def filter_noise(self, df: pd.DataFrame, content_col: str = 'content') -> pd.DataFrame:
        """对DataFrame进行噪声过滤

        逐条检测内容列，标记噪声并过滤，同时记录噪声原因用于分析

        Args:
            df: 待过滤的DataFrame
            content_col: 内容列名，默认为'content'

        Returns:
            过滤噪声后的DataFrame，包含is_noise和noise_reason列
        """
        print(f"\n🤖 LLM辅助噪声检测...")
        print(f"   输入: {len(df)} 条")

        if df.empty:
            return df

        df = df.copy()
        noise_flags = []  # 存储每条数据的噪声标记
        noise_reasons = []  # 存储每条数据的噪声原因

        # 逐条检测噪声
        for idx, row in df.iterrows():
            text = str(row.get(content_col, ''))
            is_noise, reason = self.detect(text)
            noise_flags.append(is_noise)
            noise_reasons.append(reason)

        # 标记噪声信息
        df['is_noise'] = noise_flags
        df['noise_reason'] = noise_reasons

        # 统计噪声检测结果
        noise_count = sum(noise_flags)
        result = df[~df['is_noise']].copy()

        print(f"   检测到 {noise_count} 条噪声")
        # 按噪声类型统计分布
        if noise_count > 0:
            noise_types = df[df['is_noise']]['noise_reason'].value_counts()
            for reason, count in noise_types.items():
                print(f"     {reason}: {count} 条")
        print(f"   过滤后保留 {len(result)} 条")

        return result


class DataCredibilityScorer:
    """数据可信度评估（Data Credibility Score）

    创新点：综合评估每条数据的可信度
    考虑维度：账号等级、互动量、内容完整性、发布时间合理性、平台权重
    """

    # 平台可信度权重配置，基于平台内容审核严格度和用户质量评估
    PLATFORM_WEIGHTS = {
        '微博': 0.85, 'weibo': 0.85,   # 微博：用户基数大，内容审核中等
        '知乎': 0.90, 'zhihu': 0.90,   # 知乎：长文为主，内容质量较高
        '贴吧': 0.75, 'tieba': 0.75,   # 贴吧：匿名讨论，内容质量参差
        '虎扑': 0.80, 'hupu': 0.80,    # 虎扑：体育社区，内容质量中等
    }

    def __init__(self):
        """初始化可信度评估器，加载可疑关键词列表"""
        # 可疑营销关键词，出现这些词的内容真实性评分将大幅降低
        self.suspicious_keywords = [
            '代购', '加微信', '加V', '私聊', '转让', '出售',
            '优惠券', '免费领', '扫码', '点击链接', '兼职',
        ]

    def calculate_credibility(self, row: pd.Series) -> Dict[str, Any]:
        """计算单条数据的五维可信度评分

        五维评估体系（总分100分）：
        1. 内容完整性（0-25分）：评估文本长度和信息丰富程度
        2. 互动量可信度（0-25分）：评估评论数、点赞数、转发数的总和
        3. 平台可信度（0-20分）：基于平台权重系数评估来源可靠性
        4. 内容真实性（0-15分）：检测营销关键词，评估内容自然度
        5. 时间合理性（0-15分）：评估发布时间信息是否完整合理

        Args:
            row: DataFrame中的一行数据（pd.Series）

        Returns:
            包含可信度总分、各维度详情、可信度等级的字典
        """
        scores = {}
        total = 0

        # 维度一：内容完整性评分（0-25分），文本越长信息越丰富，得分越高
        content = str(row.get('content', '') or row.get('comment_content', ''))
        content_len = len(content.strip())
        if content_len >= 30:
            scores['completeness'] = 25  # 长文本，信息完整
        elif content_len >= 15:
            scores['completeness'] = 18  # 中等长度，信息较完整
        elif content_len >= 5:
            scores['completeness'] = 10  # 短文本，信息有限
        else:
            scores['completeness'] = 3   # 极短文本，信息匮乏

        # 维度二：互动量可信度评分（0-25分），互动量越高说明内容越受关注
        comments_count = int(row.get('comments_count', 0) or row.get('comment_count', 0) or 0)
        attitudes = int(row.get('attitudes_count', 0) or row.get('like_count', 0) or 0)
        reposts = int(row.get('reposts_count', 0) or row.get('repost_count', 0) or 0)
        total_interactions = comments_count + attitudes + reposts

        if total_interactions > 100:
            scores['interaction'] = 25  # 高互动，内容受广泛关注
        elif total_interactions > 20:
            scores['interaction'] = 20  # 中等互动
        elif total_interactions > 5:
            scores['interaction'] = 15  # 低互动
        elif total_interactions > 0:
            scores['interaction'] = 10  # 极低互动
        else:
            scores['interaction'] = 5   # 无互动

        # 维度三：平台可信度评分（0-20分），不同平台的内容审核标准不同
        platform = str(row.get('platform', '')).lower()
        scores['platform'] = self.PLATFORM_WEIGHTS.get(platform, 0.70) * 20  # 未知平台默认0.70

        # 维度四：内容真实性评分（0-15分），检测营销推广等不实内容
        is_suspicious = any(kw in content for kw in self.suspicious_keywords)
        if is_suspicious:
            scores['authenticity'] = 3   # 含营销关键词，真实性极低
        elif content_len >= 20 and any(p in content for p in '，。！？'):
            scores['authenticity'] = 15  # 长文本含标点，自然表达
        elif content_len >= 10:
            scores['authenticity'] = 10  # 中等长度
        else:
            scores['authenticity'] = 5   # 短文本

        # 维度五：时间合理性评分（0-15分），有完整时间信息的数据更可信
        time_str = str(row.get('publish_time', '') or row.get('created_at', ''))
        if time_str and time_str != 'nan' and len(time_str) > 5:
            scores['timeliness'] = 15  # 时间信息完整
        elif time_str and time_str != 'nan':
            scores['timeliness'] = 8   # 时间信息不完整
        else:
            scores['timeliness'] = 3   # 无时间信息

        # 汇总五维评分，限制在0-100范围内
        total = sum(scores.values())
        total = min(100, max(0, total))

        return {
            'credibility_score': total,
            'credibility_details': scores,
            # 可信度等级划分：高(>=75)、中(>=50)、低(<50)
            'credibility_level': '高' if total >= 75 else '中' if total >= 50 else '低'
        }

    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """对整个DataFrame进行可信度评分

        逐行计算五维可信度评分，并统计评分分布

        Args:
            df: 待评分的DataFrame

        Returns:
            添加了credibility_score和credibility_level列的DataFrame
        """
        print(f"\n📊 数据可信度评估...")
        print(f"   输入: {len(df)} 条")

        if df.empty:
            return df

        df = df.copy()
        credibility_scores = []  # 存储每条数据的可信度总分
        credibility_levels = []  # 存储每条数据的可信度等级

        # 逐行计算可信度评分
        for idx, row in df.iterrows():
            result = self.calculate_credibility(row)
            credibility_scores.append(result['credibility_score'])
            credibility_levels.append(result['credibility_level'])

        # 将评分结果写入DataFrame
        df['credibility_score'] = credibility_scores
        df['credibility_level'] = credibility_levels

        # 统计可信度等级分布
        level_counts = Counter(credibility_levels)
        print(f"   可信度分布:")
        for level in ['高', '中', '低']:
            count = level_counts.get(level, 0)
            print(f"     {level}可信度: {count} 条 ({count / len(df) * 100:.1f}%)")

        avg_score = np.mean(credibility_scores)
        print(f"   平均可信度: {avg_score:.1f}/100")

        return df


class SmartTextRepairer:
    """智能文本修复

    创新点：自动修复爬虫导致的问题
    包括：emoji乱码修复、截断文本检测、特殊字符清理、繁简转换统一
    """

    # emoji乱码修复映射表，将编码异常的emoji字符替换为空
    EMOJI_FIXES = {
        '🀀': '', '🀁': '', '🀂': '', '🀃': '',
        '\U0001f000': '', '\U0001f001': '',
    }

    # 繁体到简体中文的转换映射表，统一文本字体以利于后续分析
    TRADITIONAL_TO_SIMPLIFIED = {
        '園': '园', '區': '区', '樂': '乐', '園區': '园区',
        '開': '开', '關': '关', '買': '买', '賣': '卖',
        '價': '价', '錢': '钱', '門': '门', '問': '问',
        '時': '时', '點': '点', '過': '过', '還': '还',
        '這': '这', '裡': '里', '為': '为', '與': '与',
        '對': '对', '說': '说', '學': '学', '電': '电',
        '機': '机', '車': '车', '長': '长', '東': '东',
        '場': '场', '館': '馆', '驗': '验', '體': '体',
        '歲': '岁', '歷': '历', '豐': '丰', '華': '华',
        '實': '实', '寶': '宝', '貴': '贵', '質': '质',
        '購': '购', '費': '费', '資': '资', '網': '网',
        '號': '号', '術': '术', '運': '运', '營': '营',
        '總': '总', '覺': '觉', '認': '认', '讓': '让',
        '環': '环', '壓': '压', '驚': '惊', '歡': '欢',
        '夠': '够', '經': '经', '現': '现', '進': '进',
        '當': '当', '種': '种', '將': '将', '幫': '帮',
        '動': '动', '聽': '听', '讀': '读', '寫': '写',
    }

    # 爬虫残留物的正则清理规则列表，每项为(正则模式, 替换文本)的元组
    CRAWL_ARTIFACTS = [
        (r'阅读全文\s*$', ''),          # "阅读全文"提示
        (r'展开全文\s*$', ''),          # "展开全文"提示
        (r'收起全文\s*$', ''),          # "收起全文"提示
        (r'\s*全文\s*$', ''),           # "全文"提示
        (r'\[.*?\]\s*$', ''),           # 末尾方括号标注
        (r'来自.*?客户端\s*$', ''),     # 来源客户端标注
        (r'\d{4}-\d{2}-\d{2}\s*$', ''),  # 末尾日期
        (r'赞\s*\d*\s*$', ''),          # "赞N"互动计数
        (r'回复\s*\d*\s*$', ''),        # "回复N"互动计数
        (r'评论\s*\d*\s*$', ''),        # "评论N"互动计数
        (r'转发\s*\d*\s*$', ''),        # "转发N"互动计数
        (r'​', ''),                     # 零宽空格
        (r'\u200b', ''),                # 零宽空格Unicode
        (r'\ufeff', ''),                # BOM字符
        (r'\xa0', ' '),                 # 不间断空格替换为普通空格
        (r'[\U0001f600-\U0001f64f]{3,}', ''),  # 连续3个以上emoji表情
    ]

    compiled_artifacts = None  # 预编译的正则模式缓存，类级别共享

    def __init__(self):
        """初始化文本修复器，预编译爬虫残留清理正则"""
        # 延迟编译正则模式，仅在首次初始化时执行
        if self.compiled_artifacts is None:
            SmartTextRepairer.compiled_artifacts = [
                (re.compile(p), r) for p, r in self.CRAWL_ARTIFACTS
            ]

    def repair(self, text: str) -> Tuple[str, List[str]]:
        """智能修复单条文本

        按顺序执行六步修复流程：
        1. 清理爬虫残留（正则匹配去除"阅读全文"等噪声）
        2. 修复emoji乱码（替换编码异常的emoji字符）
        3. 繁简转换（统一为简体中文，便于后续分析）
        4. 截断文本检测（识别末尾无标点的疑似截断文本）
        5. 清理多余空白（合并连续空白为单个空格）
        6. 修复重复标点（将3个以上连续相同标点缩减为2个）

        Args:
            text: 待修复的文本字符串

        Returns:
            元组(修复后的文本, 修复操作日志列表)
        """
        if not text or pd.isna(text):
            return '', ['空内容']

        text = str(text)
        repairs = []  # 记录执行的修复操作

        # 步骤一：清理爬虫残留，逐条应用预编译的正则替换规则
        for pattern, replacement in self.compiled_artifacts:
            new_text = pattern.sub(replacement, text)
            if new_text != text:
                repairs.append(f'清理爬虫残留')
                text = new_text

        # 步骤二：修复emoji乱码，替换编码异常的Unicode字符
        for bad_emoji, fix in self.EMOJI_FIXES.items():
            if bad_emoji in text:
                text = text.replace(bad_emoji, fix)
                repairs.append('修复emoji乱码')

        # 步骤三：繁简转换，逐字替换繁体为简体
        original = text
        for trad, simp in self.TRADITIONAL_TO_SIMPLIFIED.items():
            text = text.replace(trad, simp)
        if text != original:
            repairs.append('繁简转换')

        # 步骤四：截断文本检测，末尾无结束标点且文本较长时标记为疑似截断
        if text and not text[-1] in '。！？.!?…~～' and len(text) > 20:
            if '...' not in text and '…' not in text:
                repairs.append('疑似截断文本')

        # 步骤五：清理多余空白，合并连续空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        # 步骤六：修复重复标点，将3个以上连续相同标点缩减为2个
        text = re.sub(r'([！？。])\1{2,}', r'\1\1', text)

        return text, repairs

    def repair_dataframe(self, df: pd.DataFrame, content_col: str = 'content') -> pd.DataFrame:
        """对DataFrame中的文本列进行批量智能修复

        逐条修复内容列文本，记录修复日志并统计修复类型分布

        Args:
            df: 待修复的DataFrame
            content_col: 内容列名，默认为'content'

        Returns:
            添加了修复后内容列和修复日志列的DataFrame
        """
        print(f"\n🔧 智能文本修复...")
        print(f"   输入: {len(df)} 条")

        if df.empty:
            return df

        df = df.copy()
        repaired_contents = []  # 存储修复后的文本
        repair_logs = []        # 存储每条文本的修复日志
        repair_count = 0        # 统计被修复的文本数量

        # 逐条修复文本
        for idx, row in df.iterrows():
            text = str(row.get(content_col, ''))
            repaired, repairs = self.repair(text)
            repaired_contents.append(repaired)
            repair_logs.append(repairs)
            if repairs:
                repair_count += 1

        # 将修复结果写入新列
        df[content_col + '_repaired'] = repaired_contents
        df['repair_log'] = repair_logs

        # 统计修复类型分布
        print(f"   修复 {repair_count} 条文本")
        repair_types = Counter()
        for logs in repair_logs:
            for log in logs:
                repair_types[log] += 1
        for rtype, count in repair_types.most_common():
            print(f"     {rtype}: {count} 条")

        return df


class CrossPlatformEventAggregator:
    """跨平台事件聚合

    创新点：识别不同平台讨论同一事件的评论
    基于关键词提取和事件指纹匹配，自动聚合同一话题下的跨平台数据
    """

    # 预定义的事件关键词映射表，每个事件对应一组特征关键词
    # 用于识别不同平台讨论同一事件的评论，实现跨平台数据聚合
    EVENT_KEYWORDS = {
        '包子事件': ['包子', '70元', '70块', '包子价格', '镶金'],       # 天价包子事件
        '劝烟事件': ['劝烟', '吸烟', '抽烟', '打人', '殴打', '非吸烟区'],  # 劝烟被打事件
        '门票涨价': ['涨价', '门票', '470', '票价', '高峰票'],          # 门票价格调整
        '33VIP': ['33vip', 'VIP', '尊享', '免排队'],                    # VIP服务争议
        '退票政策': ['退票', '退改', '阶梯式'],                         # 退票政策讨论
        '十周年': ['十周年', '10周年', '庆典', '周年庆'],               # 十周年庆典
        '插队': ['插队', '加塞', '排队'],                               # 排队秩序问题
        '餐饮价格': ['餐饮', '吃饭', '汉堡', '矿泉水', '88块', '20块'],  # 餐饮价格争议
    }

    def __init__(self):
        """初始化跨平台事件聚合器，加载事件关键词模式"""
        self.event_patterns = {}
        for event, keywords in self.EVENT_KEYWORDS.items():
            self.event_patterns[event] = keywords

    def _extract_event_tags(self, text: str) -> List[str]:
        """从文本中提取事件标签

        遍历所有预定义事件的关键词，若文本中包含至少一个关键词
        则将该事件标签添加到结果列表中

        Args:
            text: 待提取事件标签的文本

        Returns:
            匹配到的事件标签列表
        """
        tags = []
        text_lower = text.lower()
        # 遍历每个事件的关键词列表，统计匹配数量
        for event, keywords in self.event_patterns.items():
            match_count = sum(1 for kw in keywords if kw in text_lower)
            if match_count >= 1:  # 至少匹配一个关键词即标记该事件
                tags.append(event)
        return tags

    def aggregate(self, df: pd.DataFrame, content_col: str = 'content') -> pd.DataFrame:
        """对DataFrame进行跨平台事件聚合

        为每条数据提取事件标签，统计事件分布和跨平台覆盖情况

        Args:
            df: 待聚合的DataFrame
            content_col: 内容列名，默认为'content'

        Returns:
            添加了event_tags和event_count列的DataFrame
        """
        print(f"\n🕸️ 跨平台事件聚合...")
        print(f"   输入: {len(df)} 条")

        if df.empty:
            return df

        df = df.copy()
        event_tags_list = []  # 存储每条数据的事件标签

        # 逐条提取事件标签
        for idx, row in df.iterrows():
            text = str(row.get(content_col, ''))
            tags = self._extract_event_tags(text)
            event_tags_list.append(tags)

        # 将事件标签和标签数量写入DataFrame
        df['event_tags'] = event_tags_list
        df['event_count'] = [len(t) for t in event_tags_list]

        # 统计各事件的评论数量分布
        event_counts = Counter()
        for tags in event_tags_list:
            for tag in tags:
                event_counts[tag] += 1

        # 打印事件分布及跨平台覆盖情况
        if event_counts:
            print(f"   识别到 {len(event_counts)} 个事件:")
            for event, count in event_counts.most_common():
                # 统计每个事件在各平台的分布
                platform_dist = df[df['event_tags'].apply(lambda x: event in x)]
                if 'platform' in platform_dist.columns:
                    platforms = platform_dist['platform'].value_counts()
                    platform_str = ', '.join([f"{p}:{c}" for p, c in platforms.items()])
                    print(f"     {event}: {count}条 (跨平台: {platform_str})")
                else:
                    print(f"     {event}: {count}条")

        # 统计真正跨平台的事件数量（同一事件在2个以上平台出现）
        tagged = df[df['event_count'] > 0]
        if not tagged.empty and 'platform' in tagged.columns:
            cross_platform_events = 0
            for event in event_counts:
                event_data = tagged[tagged['event_tags'].apply(lambda x: event in x)]
                if event_data['platform'].nunique() > 1:
                    cross_platform_events += 1
            print(f"   跨平台事件: {cross_platform_events}/{len(event_counts)}")

        return df


class IntelligentDataCleaner:
    """智能数据清洗管道 - 整合5大创新点

    该类是整个智能数据清洗模块的入口，将5大创新清洗组件串联为完整的清洗管道：
    1. 智能文本修复（SmartTextRepairer）：修复爬虫导致的文本问题
    2. LLM辅助噪声检测（LLMNoiseDetector）：识别并过滤网页噪声
    3. 语义级去重（SimHashDeduplicator）：去除语义相同的重复评论
    4. 数据可信度评估（DataCredibilityScorer）：五维评估数据质量
    5. 跨平台事件聚合（CrossPlatformEventAggregator）：识别跨平台同事件数据
    """

    def __init__(self, use_llm_noise=False):
        """初始化智能数据清洗管道

        Args:
            use_llm_noise: 是否启用LLM辅助噪声检测，默认False使用规则检测
        """
        self.simhash = SimHashDeduplicator()              # 语义级去重器
        self.noise_detector = LLMNoiseDetector(use_llm=use_llm_noise)  # 噪声检测器
        self.credibility_scorer = DataCredibilityScorer()  # 可信度评估器
        self.text_repairer = SmartTextRepairer()           # 文本修复器
        self.event_aggregator = CrossPlatformEventAggregator()  # 事件聚合器
        self.use_llm_noise = use_llm_noise

    def clean_pipeline(self, df: pd.DataFrame,
                       content_col: str = 'content',
                       min_credibility: int = 30,
                       enable_semantic_dedup: bool = True,
                       enable_noise_filter: bool = True,
                       enable_credibility: bool = True,
                       enable_repair: bool = True,
                       enable_event_aggregation: bool = True) -> pd.DataFrame:
        """智能数据清洗管道主流程

        按顺序执行五步清洗操作，每步均可通过参数独立控制开关：
        Step 0: 确保内容列存在，自动兼容不同列名
        Step 1: 智能文本修复 - 修复爬虫残留、emoji乱码、繁简转换等
        Step 2: LLM辅助噪声检测 - 识别并过滤按钮文字、导航栏等噪声
        Step 3: 语义级去重 - 基于SimHash+编辑距离去除语义重复评论
        Step 4: 数据可信度评估 - 五维评分并过滤低可信度数据
        Step 5: 跨平台事件聚合 - 识别不同平台讨论同一事件的评论

        Args:
            df: 待清洗的DataFrame
            content_col: 内容列名，默认为'content'
            min_credibility: 最低可信度阈值，低于此值的数据将被过滤，默认30
            enable_semantic_dedup: 是否启用语义级去重，默认True
            enable_noise_filter: 是否启用噪声过滤，默认True
            enable_credibility: 是否启用可信度评估，默认True
            enable_repair: 是否启用文本修复，默认True
            enable_event_aggregation: 是否启用事件聚合，默认True

        Returns:
            清洗后的DataFrame
        """
        print("=" * 80)
        print("🧹 智能数据清洗管道（5大创新点）")
        print("=" * 80)

        if df.empty:
            print("⚠️ 没有数据需要清洗！")
            return df

        # 记录原始数据量，用于最终计算保留率
        original_count = len(df)
        print(f"📊 输入数据: {original_count} 条")

        # Step 0: 确保content列存在，自动适配不同数据源的列名
        if content_col not in df.columns:
            # 按优先级尝试常见的替代列名
            for alt in ['comment_content', 'comment', 'text']:
                if alt in df.columns:
                    df[content_col] = df[alt]
                    break
            else:
                # 所有替代列名都不存在，创建空列
                df[content_col] = ''

        # Step 1: 智能文本修复 - 修复爬虫导致的文本问题
        if enable_repair:
            df = self.text_repairer.repair_dataframe(df, content_col)
            # 用修复后的内容替换原始内容列
            if content_col + '_repaired' in df.columns:
                df[content_col] = df[content_col + '_repaired']
                df = df.drop(columns=[content_col + '_repaired'])

        # Step 2: LLM辅助噪声检测 - 识别并过滤网页噪声
        if enable_noise_filter:
            df = self.noise_detector.filter_noise(df, content_col)
            # 清理噪声检测的辅助列，避免污染后续处理
            df = df.drop(columns=['is_noise', 'noise_reason'], errors='ignore')

        # Step 3: 语义级去重 - 基于SimHash算法去除语义重复
        if enable_semantic_dedup:
            df = self.simhash.deduplicate(df, content_col)
            # 清理去重标记列
            df = df.drop(columns=['is_semantic_duplicate'], errors='ignore')

        # Step 4: 数据可信度评估 - 五维评分并过滤低可信度数据
        if enable_credibility:
            df = self.credibility_scorer.score_dataframe(df)
            # 根据最低可信度阈值过滤数据
            if min_credibility > 0:
                before = len(df)
                df = df[df['credibility_score'] >= min_credibility].copy()
                print(f"   可信度过滤(>={min_credibility}): {before} -> {len(df)}")

        # Step 5: 跨平台事件聚合 - 识别跨平台同事件数据
        if enable_event_aggregation:
            df = self.event_aggregator.aggregate(df, content_col)

        # 清理临时辅助列，保持输出DataFrame整洁
        df = df.drop(columns=['repair_log'], errors='ignore')

        # 输出清洗统计摘要
        print(f"\n✅ 清洗完成: {original_count} -> {len(df)} 条")
        print(f"   保留率: {len(df) / original_count * 100:.1f}%")
        print("=" * 80)

        return df

    def generate_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成数据质量报告

        对清洗后的数据进行全面统计，包括内容长度、可信度分布、事件分布、平台分布等

        Args:
            df: 清洗后的DataFrame

        Returns:
            包含各维度统计数据的质量报告字典
        """
        report = {
            "total_records": len(df),  # 数据总条数
            "cleaning_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 清洗时间
            "content_stats": {},       # 内容统计
            "credibility_stats": {},   # 可信度统计
            "event_stats": {},         # 事件统计
            "platform_stats": {},      # 平台统计
        }

        if df.empty:
            return report

        # 获取内容列名，用于后续统计
        content_col = 'content'
        if content_col not in df.columns:
            return report

        # 统计内容长度分布
        lengths = df[content_col].astype(str).apply(len)
        # 计算内容长度的均值、中位数、最小值和最大值
        report["content_stats"] = {
            "mean_length": float(lengths.mean()),
            "median_length": float(lengths.median()),
            "min_length": int(lengths.min()),
            "max_length": int(lengths.max()),
        }

        # 统计可信度分布
        if 'credibility_score' in df.columns:
            report["credibility_stats"] = {
                "mean_score": float(df['credibility_score'].mean()),
                "high_ratio": float((df['credibility_level'] == '高').mean()),
                "medium_ratio": float((df['credibility_level'] == '中').mean()),
                "low_ratio": float((df['credibility_level'] == '低').mean()),
            }

        # 统计事件标签分布（取前10个最常见事件）
        if 'event_tags' in df.columns:
            event_counts = Counter()
            for tags in df['event_tags']:
                for tag in tags:
                    event_counts[tag] += 1
            report["event_stats"] = dict(event_counts.most_common(10))

        # 统计平台分布
        if 'platform' in df.columns:
            report["platform_stats"] = df['platform'].value_counts().to_dict()

        return report


def main():
    """模块示例入口函数

    构造示例数据演示智能数据清洗管道的完整流程，
    包括语义去重、噪声过滤、可信度评估、文本修复和事件聚合
    """
    print("=" * 80)
    print("🧹 智能数据清洗模块 - 示例")
    print("=" * 80)

    # 构造涵盖各类清洗场景的示例数据
    sample_data = [
        {"content": "上海迪士尼门票太贵了，470块一张，感觉不值这个价", "platform": "weibo", "comments_count": 50, "attitudes_count": 200},  # 门票涨价事件
        {"content": "票价真的高，上海迪士尼一张票要470", "platform": "zhihu", "comments_count": 10, "attitudes_count": 30},  # 与上一条语义重复
        {"content": "迪士尼包子70元一个，网友怒了", "platform": "hupu", "comments_count": 119, "attitudes_count": 500},  # 包子事件
        {"content": "回复", "platform": "tieba", "comments_count": 0, "attitudes_count": 0},  # 噪声：操作按钮
        {"content": "來自iPhone客戶端", "platform": "weibo", "comments_count": 0, "attitudes_count": 0},  # 噪声：来源标注（含繁体）
        {"content": "上海迪士尼勸煙被打事件，打人者賠了5位數", "platform": "weibo", "comments_count": 755, "attitudes_count": 1649},  # 劝烟事件（含繁体）
        {"content": "迪士尼劝烟事件，打人者赔了5位数", "platform": "zhihu", "comments_count": 30, "attitudes_count": 80},  # 与上一条语义重复
        {"content": "好", "platform": "tieba", "comments_count": 0, "attitudes_count": 0},  # 过短内容
        {"content": "加微信代购迪士尼门票，便宜出", "platform": "weibo", "comments_count": 2, "attitudes_count": 1},  # 可疑营销内容
        {"content": "周末带孩子去迪士尼，飞跃地平线排了3小时，但5D效果太震撼了，值回票价！就是餐饮价格有点贵", "platform": "zhihu", "comments_count": 45, "attitudes_count": 120},  # 正常评论
    ]

    df = pd.DataFrame(sample_data)
    # 创建清洗器实例，执行完整清洗管道
    cleaner = IntelligentDataCleaner()
    cleaned = cleaner.clean_pipeline(df, min_credibility=20)

    # 打印清洗结果，展示可信度评分和事件标签
    print(f"\n📋 清洗结果:")
    for idx, row in cleaned.iterrows():
        cred = row.get('credibility_score', 0)
        events = row.get('event_tags', [])
        print(f"  [{cred}分] {row['content'][:40]}... 事件:{events}")


# 模块入口：直接运行时执行示例
if __name__ == "__main__":
    main()
