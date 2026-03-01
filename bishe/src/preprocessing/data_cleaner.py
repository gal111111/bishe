# -*- coding: utf-8 -*-
"""
数据清洗与去重模块
提升爬取数据的质量，去除重复内容
"""
import os
import sys
import re
import hashlib
import pandas as pd
from typing import List, Set, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)


class DataCleaner:
    """数据清洗器 - 提升数据质量"""
    
    def __init__(self):
        self.min_content_length = 3
        self.max_content_length = 500
        self.seen_contents: Set[str] = set()
        self.seen_user_contents: dict = {}
        
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
    
    def _normalize_content(self, content: str) -> str:
        """内容标准化"""
        if not content or not isinstance(content, str):
            return ""
        
        content = content.strip()
        
        content = self.emoji_pattern.sub('', content)
        content = self.bracket_pattern.sub('', content)
        content = self.url_pattern.sub('', content)
        content = self.mention_pattern.sub('', content)
        content = self.hashtag_pattern.sub('', content)
        
        content = re.sub(r'\s+', ' ', content)
        
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
