# -*- coding: utf-8 -*-
"""
数据清洗与去重模块
提升爬取数据的质量，去除重复内容
"""
import os
import sys
import re
import random
import hashlib
import pandas as pd
from typing import List, Set, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# 尝试导入分词库
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False
    print("[WARN] 未安装jieba，将使用基础分词功能")

try:
    import pynlpir
    HAS_PYNLPIR = True
    # 初始化pynlpir
    try:
        pynlpir.open()
    except:
        HAS_PYNLPIR = False
        print("[WARN] pynlpir初始化失败，将使用jieba分词")
except ImportError:
    HAS_PYNLPIR = False
    print("[WARN] 未安装pynlpir，将使用jieba分词")


class DataCleaner:
    """数据清洗器 - 提升数据质量"""
    
    def __init__(self):
        self.min_content_length = 3
        self.max_content_length = 500
        self.seen_contents: Set[str] = set()
        self.seen_user_contents: dict = {}
        
        # 表情符号映射
        self.emoji_map = {
            "😡": "愤怒", "😠": "愤怒", "😤": "愤怒",
            "😊": "满意", "😃": "满意", "😄": "满意", "🎉": "满意",
            "😢": "悲伤", "😔": "悲伤", "😟": "悲伤",
            "😲": "惊讶", "😮": "惊讶", "😯": "惊讶",
            "👍": "支持", "👎": "反对",
            "❤️": "喜欢", "💔": "不喜欢",
            "🔥": "热门", "💯": "满分",
            "⏰": "时间", "⌛": "时间", "🕒": "时间",
            "💳": "价格", "💰": "价格", "💸": "价格",
            "🚶": "排队", "👥": "排队", "👫": "排队",
            "🏰": "乐园", "🎡": "乐园", "🎢": "乐园",
            "🎠": "乐园", "🎪": "乐园", "🎭": "乐园"
        }
        
        # 同音异形字映射
        self.homophone_map = {
            "排对": "排队", "对列": "队列", "对伍": "队伍",
            "快通": "快速通", "快票": "快速通", "速通": "快速通",
            "迪士呢": "迪士尼", "迪士泥": "迪士尼", "迪士霓": "迪士尼",
            "乐园": "乐园", "乐圆": "乐园", "乐苑": "乐园",
            "服务": "服务", "服物": "服务", "服雾": "服务",
            "环境": "环境", "环镜": "环境", "环竟": "环境",
            "卫生": "卫生", "卫升": "卫生", "卫声": "卫生",
            "设施": "设施", "设失": "设施", "设世": "设施",
            "价格": "价格", "价个": "价格", "价阁": "价格",
            "时间": "时间", "时简": "时间", "时见": "时间"
        }
        
        # 迪士尼领域词典
        self.disney_dict = {
            "迪士尼", "迪士尼乐园", "上海迪士尼", "迪士尼度假区",
            "快速通", "快速通行证", "FP", "尊享卡",
            "排队卡", "排队时间", "等候时间",
            "游乐项目", "过山车", "旋转木马", "城堡", "烟花表演",
            "米奇大街", "明日世界", "梦幻世界", "探险岛", "宝藏湾",
            "餐饮", "购物", "住宿", "酒店",
            "工作人员", "服务态度", "客服", "员工",
            "门票", "票价", "年卡", "季卡",
            "卫生", "环境", "拥挤度", "人流量"
        }
        
        # 噪声词列表
        self.noise_words = {
            "广告", "推广", "代购", "刷单", "兼职",
            "加微信", "加QQ", "联系方式", "电话", "手机号",
            "网址", "链接", "官网", "网站",
            "抽奖", "中奖", "活动", "优惠", "折扣",
            "免费", "送", "赠", "领取", "兑换",
            "关注", "点赞", "转发", "分享", "评论"
        }
        
        self.emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001f926-\U0001f937"
            u"\u2600-\u2B55"
            u"\u200d"
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\ufe0f"
            u"\u3030"
            "]+", 
            flags=re.UNICODE
        )
        
        self.bracket_pattern = re.compile(r'\[.*?\]')
        self.url_pattern = re.compile(r'http[s]?://\S+|www\.\S+')
        self.mention_pattern = re.compile(r'@\S+')
        self.hashtag_pattern = re.compile(r'#\S+')
        
        # 加载自定义词典
        if HAS_JIEBA:
            # 添加迪士尼领域词汇到jieba词典
            for word in self.disney_dict:
                jieba.add_word(word)
        elif HAS_PYNLPIR:
            # pynlpir不需要手动添加词典
            pass
    
    def _normalize_content(self, content: str) -> str:
        """内容标准化"""
        if not content or not isinstance(content, str):
            return ""
        
        content = content.strip()
        
        # 1. 表情符号映射
        for emoji, meaning in self.emoji_map.items():
            if emoji in content:
                content = content.replace(emoji, f" {meaning} ")
        
        # 2. 同音异形字归一化
        for wrong, correct in self.homophone_map.items():
            if wrong in content:
                content = content.replace(wrong, correct)
        
        # 3. 去除括号内容
        content = self.bracket_pattern.sub('', content)
        
        # 4. 去除URL
        content = self.url_pattern.sub('', content)
        
        # 5. 去除@提及
        content = self.mention_pattern.sub('', content)
        
        # 6. 去除#话题
        content = self.hashtag_pattern.sub('', content)
        
        # 7. 噪声词过滤
        for noise_word in self.noise_words:
            if noise_word in content:
                content = content.replace(noise_word, '')
        
        # 8. 去除多余空白
        content = re.sub(r'\s+', ' ', content)
        
        # 9. 去除特殊符号
        content = re.sub(r'[\s\u00A0\u2000-\u200F\u2028-\u202F\u205F-\u206F\ufeff\u3000]+', ' ', content)
        
        return content.strip()
    
    def _get_content_hash(self, content: str) -> str:
        """获取内容的哈希值用于去重（直接使用原始内容）"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _is_short_content(self, content: str) -> bool:
        """判断是否是过短的内容"""
        normalized = self._normalize_content(content)
        return len(normalized) < self.min_content_length
    
    def _is_meaningless_content(self, content: str) -> bool:
        """判断是否是无意义内容（更宽松）"""
        normalized = self._normalize_content(content)
        
        strict_meaningless = [
            '哈哈', '呵呵', '嗯嗯', '哦哦',
            '👍', '👏', '😊', '😂', '❤️', '🙏', '🎉', '🔥',
        ]
        
        for keyword in strict_meaningless:
            if normalized == keyword:
                return True
        
        if len(normalized) <= 2 and len(normalized) > 0:
            return True
        
        return False
    
    def _is_duplicate_by_user(self, content: str, author: str) -> bool:
        """判断是否是同一用户的重复发言"""
        if not author or author == '匿名':
            return False
        
        content_hash = self._get_content_hash(content)
        
        if author not in self.seen_user_contents:
            self.seen_user_contents[author] = set()
        
        if content_hash in self.seen_user_contents[author]:
            return True
        
        self.seen_user_contents[author].add(content_hash)
        return False
    
    def _is_duplicate_content(self, content: str) -> bool:
        """判断是否是重复内容（全局）"""
        content_hash = self._get_content_hash(content)
        
        if content_hash in self.seen_contents:
            return True
        
        self.seen_contents.add(content_hash)
        return False
    
    def clean_dataframe(self, df: pd.DataFrame, content_col: str = 'content', 
                       author_col: Optional[str] = None) -> pd.DataFrame:
        """清洗DataFrame（更宽松模式）"""
        print("\n" + "=" * 70)
        print("🧹 [数据清洗] 开始提升数据质量（宽松模式）")
        print("=" * 70)
        
        original_count = len(df)
        print(f"\n📊 原始数据量: {original_count} 条")
        
        self.seen_contents.clear()
        self.seen_user_contents.clear()
        
        valid_rows = []
        removed_stats = {
            'short_content': 0,
            'meaningless': 0,
            'duplicate_global': 0,
            'duplicate_user': 0,
        }
        
        for idx, row in df.iterrows():
            content = str(row.get(content_col, ''))
            
            original_content = content
            
            if self._is_duplicate_content(content):
                removed_stats['duplicate_global'] += 1
                continue
            
            if author_col and author_col in row:
                author = str(row.get(author_col, ''))
                if self._is_duplicate_by_user(content, author):
                    removed_stats['duplicate_user'] += 1
                    continue
            
            valid_rows.append(row)
        
        df_cleaned = pd.DataFrame(valid_rows).reset_index(drop=True)
        
        print(f"\n📈 清洗后数据量: {len(df_cleaned)} 条")
        print(f"📉 去除数据: {original_count - len(df_cleaned)} 条")
        print(f"\n📋 去除原因统计:")
        print(f"   - 全局重复内容: {removed_stats['duplicate_global']} 条")
        print(f"   - 同一用户重复发言: {removed_stats['duplicate_user']} 条")
        
        print(f"\n✅ 数据清洗完成！数据保留率: {(len(df_cleaned)/original_count*100):.1f}%")
        
        return df_cleaned
    
    def reset(self):
        """重置状态"""
        self.seen_contents.clear()
        self.seen_user_contents.clear()
    
    def eda_augmentation(self, text: str, num_aug: int = 4) -> List[str]:
        """
        基于EDA的文本数据增强
        
        Args:
            text: 原始文本
            num_aug: 生成的增强文本数量
            
        Returns:
            增强后的文本列表
        """
        if not text or len(text) < 5:
            return []
        
        augmented_texts = []
        
        # 1. 同义词替换
        def synonym_replacement(sentence, n=1):
            """随机替换句子中的n个词为同义词"""
            if HAS_JIEBA:
                words = list(jieba.cut(sentence))
            else:
                words = sentence.split()
            
            # 迪士尼领域的同义词字典
            synonyms = {
                "排队": ["等候", "等待", "站队", "排对"],
                "快速通": ["快速通行证", "FP", "尊享卡"],
                "乐园": ["主题公园", "游乐园", "公园"],
                "服务": ["服务态度", "客服", "服务质量"],
                "环境": ["卫生", "环境整洁", "场地"],
                "设施": ["设备", "设施设备", "游乐设施"],
                "价格": ["票价", "费用", "花费"],
                "时间": ["时长", "时间长度", "耗时"],
                "满意": ["喜欢", "满意", "满意"],
                "失望": ["不满", "失望", "不高兴"],
                "愤怒": ["生气", "愤怒", "恼火"],
                "惊讶": ["意外", "惊讶", "吃惊"]
            }
            
            new_words = words.copy()
            replaceable_words = [word for word in words if word in synonyms]
            
            for _ in range(n):
                if replaceable_words:
                    word_to_replace = replaceable_words[0]
                    synonyms_list = synonyms[word_to_replace]
                    if synonyms_list:
                        new_word = synonyms_list[0]
                        idx = new_words.index(word_to_replace)
                        new_words[idx] = new_word
                        replaceable_words.remove(word_to_replace)
            
            return ''.join(new_words)
        
        # 2. 随机插入
        def random_insertion(sentence, n=1):
            """随机插入n个词到句子中"""
            if HAS_JIEBA:
                words = list(jieba.cut(sentence))
            else:
                words = sentence.split()
            
            if len(words) < 2:
                return sentence
            
            new_words = words.copy()
            insert_words = ["非常", "特别", "很", "比较", "相当", "十分", "极其", "超级"]
            
            for _ in range(n):
                if insert_words:
                    insert_word = insert_words[0]
                    insert_pos = random.randint(0, len(new_words))
                    new_words.insert(insert_pos, insert_word)
            
            return ''.join(new_words)
        
        # 3. 随机删除
        def random_deletion(sentence, p=0.1):
            """以概率p随机删除句子中的词"""
            if HAS_JIEBA:
                words = list(jieba.cut(sentence))
            else:
                words = sentence.split()
            
            if len(words) <= 1:
                return sentence
            
            new_words = [word for word in words if random.random() > p]
            
            if not new_words:
                return words[0]
            
            return ''.join(new_words)
        
        # 4. 随机交换
        def random_swap(sentence, n=1):
            """随机交换句子中的n对词"""
            if HAS_JIEBA:
                words = list(jieba.cut(sentence))
            else:
                words = sentence.split()
            
            if len(words) < 2:
                return sentence
            
            new_words = words.copy()
            
            for _ in range(n):
                idx1, idx2 = random.sample(range(len(new_words)), 2)
                new_words[idx1], new_words[idx2] = new_words[idx2], new_words[idx1]
            
            return ''.join(new_words)
        
        # 生成增强文本
        augmented_texts.append(synonym_replacement(text))
        augmented_texts.append(random_insertion(text))
        augmented_texts.append(random_deletion(text))
        augmented_texts.append(random_swap(text))
        
        # 去重
        augmented_texts = list(set(augmented_texts))
        
        # 限制数量
        return augmented_texts[:num_aug]
    
    def augment_dataframe(self, df: pd.DataFrame, content_col: str = 'content', target_col: str = 'polarity_label', 
                        min_samples: int = 1000) -> pd.DataFrame:
        """
        对DataFrame进行数据增强，解决样本不均衡问题
        
        Args:
            df: 原始DataFrame
            content_col: 内容列名
            target_col: 目标列名
            min_samples: 每个类别的最小样本数
            
        Returns:
            增强后的DataFrame
        """
        if target_col not in df.columns:
            return df
        
        print("\n" + "=" * 70)
        print("📈 [数据增强] 开始处理样本不均衡问题")
        print("=" * 70)
        
        # 统计每个类别的样本数
        class_counts = df[target_col].value_counts()
        print(f"\n原始类别分布:")
        for cls, count in class_counts.items():
            print(f"  {cls}: {count} 条")
        
        augmented_data = []
        
        # 对每个类别进行增强
        for cls, count in class_counts.items():
            class_data = df[df[target_col] == cls]
            augmented_data.extend(class_data.to_dict('records'))
            
            # 如果样本数不足，进行增强
            if count < min_samples:
                needed = min_samples - count
                print(f"\n🔄 增强 {cls} 类别，需要生成 {needed} 条数据")
                
                augmented_count = 0
                for _, row in class_data.iterrows():
                    if augmented_count >= needed:
                        break
                    
                    text = str(row.get(content_col, ''))
                    augmented_texts = self.eda_augmentation(text)
                    
                    for aug_text in augmented_texts:
                        if augmented_count >= needed:
                            break
                        
                        new_row = row.copy()
                        new_row[content_col] = aug_text
                        augmented_data.append(new_row)
                        augmented_count += 1
                
                print(f"✅ 已生成 {augmented_count} 条增强数据")
        
        # 创建增强后的DataFrame
        df_augmented = pd.DataFrame(augmented_data)
        
        # 统计增强后的类别分布
        new_class_counts = df_augmented[target_col].value_counts()
        print(f"\n增强后类别分布:")
        for cls, count in new_class_counts.items():
            print(f"  {cls}: {count} 条")
        
        print(f"\n✅ 数据增强完成！总数据量: {len(df_augmented)} 条")
        
        return df_augmented


def clean_crawled_data(df: pd.DataFrame, content_col: str = 'content', 
                      author_col: Optional[str] = None) -> pd.DataFrame:
    """
    便捷函数：清洗爬取的数据
    
    Args:
        df: 原始DataFrame
        content_col: 内容列名
        author_col: 作者列名（可选，用于同一用户去重）
    
    Returns:
        清洗后的DataFrame
    """
    cleaner = DataCleaner()
    return cleaner.clean_dataframe(df, content_col, author_col)


if __name__ == "__main__":
    test_data = [
        {"content": "工作人员辛苦啦[求关注]", "author": "user1"},
        {"content": "[good]", "author": "user2"},
        {"content": "[皱眉]", "author": "user1"},
        {"content": "我的出没时间已经关门[允悲]", "author": "user3"},
        {"content": "[good][good][good]", "author": "user4"},
        {"content": "[心]", "author": "user5"},
        {"content": "📢广图2026春节开放时间定啦！9点到16点，书友们别跑空~", "author": "user6"},
        {"content": "[心][心][心]", "author": "user7"},
        {"content": "[心][心][心]", "author": "user8"},
        {"content": "[皱眉]", "author": "user9"},
        {"content": "工作人员辛苦啦[求关注]", "author": "user1"},
        {"content": "[good]", "author": "user2"},
        {"content": "我的出没时间已经关门[允悲]", "author": "user3"},
        {"content": "广州图书馆的环境真的很不错，书籍种类丰富，服务态度也很好，推荐大家去！", "author": "user10"},
        {"content": "座位有点紧张，建议早点去", "author": "user11"},
    ]
    
    df_test = pd.DataFrame(test_data)
    print("=" * 70)
    print("测试数据清洗功能")
    print("=" * 70)
    print("\n原始数据:")
    print(df_test)
    
    df_cleaned = clean_crawled_data(df_test, 'content', 'author')
    
    print("\n清洗后数据:")
    print(df_cleaned)
