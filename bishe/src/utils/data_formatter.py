# -*- coding: utf-8 -*-
import os
import pandas as pd
from datetime import datetime

class DataFormatter:
    """数据格式化和汇总工具"""
    
    @staticmethod
    def format_zhihu_data(csv_path):
        """
        格式化知乎爬虫数据
        """
        print(f"📖 正在读取知乎数据: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            print(f"✅ 读取成功: {len(df)} 条")
            
            # 格式化
            formatted = []
            for _, row in df.iterrows():
                formatted.append({
                    "content": row.get("评论内容", "") or row.get("回答内容", ""),
                    "facility_type": "",
                    "region": "北京",
                    "source": "知乎",
                    "original_data": row.to_dict()
                })
            
            return pd.DataFrame(formatted)
            
        except Exception as e:
            print(f"❌ 读取知乎数据失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def format_weibo_data(csv_path):
        """
        格式化微博爬虫数据
        """
        print(f"📱 正在读取微博数据: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            print(f"✅ 读取成功: {len(df)} 条")
            
            # 格式化
            formatted = []
            for _, row in df.iterrows():
                formatted.append({
                    "content": row.get("评论内容", "") or row.get("微博内容", ""),
                    "facility_type": "",
                    "region": "北京",
                    "source": "微博",
                    "original_data": row.to_dict()
                })
            
            return pd.DataFrame(formatted)
            
        except Exception as e:
            print(f"❌ 读取微博数据失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def merge_data(zhihu_df=None, weibo_df=None, mock_df=None):
        """合并多个数据源"""
        print("\n" + "=" * 60)
        print("🔗 正在合并数据")
        print("=" * 60)
        
        all_dfs = []
        
        if zhihu_df is not None and len(zhihu_df) > 0:
            all_dfs.append(zhihu_df)
            print(f"📖 添加知乎数据: {len(zhihu_df)} 条")
        
        if weibo_df is not None and len(weibo_df) > 0:
            all_dfs.append(weibo_df)
            print(f"📱 添加微博数据: {len(weibo_df)} 条")
        
        if mock_df is not None and len(mock_df) > 0:
            all_dfs.append(mock_df)
            print(f"📊 添加模拟数据: {len(mock_df)} 条")
        
        if not all_dfs:
            print("⚠️  没有数据可合并")
            return pd.DataFrame()
        
        merged = pd.concat(all_dfs, ignore_index=True)
        print(f"✅ 合并完成: {len(merged)} 条数据")
        
        return merged
    
    @staticmethod
    def fill_facility_type(df, facility_name):
        """填充设施类型"""
        df['facility_type'] = facility_name
        return df
    
    @staticmethod
    def save_merged_data(df, output_path):
        """保存合并后的数据"""
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"💾 已保存到: {output_path}")
        return output_path


def quick_merge_and_format(
    facility_name="国家图书馆",
    zhihu_csv=None,
    weibo_csv=None,
    mock_df=None,
    output_dir=None
):
    """快速合并和格式化数据"""
    formatter = DataFormatter()
    
    zhihu_df = None
    weibo_df = None
    
    if zhihu_csv and os.path.exists(zhihu_csv):
        zhihu_df = formatter.format_zhihu_data(zhihu_csv)
    
    if weibo_csv and os.path.exists(weibo_csv):
        weibo_df = formatter.format_weibo_data(weibo_csv)
    
    merged_df = formatter.merge_data(zhihu_df, weibo_df, mock_df)
    
    if len(merged_df) > 0:
        merged_df = formatter.fill_facility_type(merged_df, facility_name)
        
        if output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"merged_{facility_name}_{timestamp}.csv")
            formatter.save_merged_data(merged_df, output_path)
        
        return merged_df
    
    return None
