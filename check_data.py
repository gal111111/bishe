

# -*- coding: utf-8 -*-
import pandas as pd
import os

platforms = ['weibo', 'zhihu', 'tieba', 'hupu']
total = 0

print("=" * 50)
print("现有数据统计")
print("=" * 50)

for p in platforms:
    file_path = f'data/raw/{p}_raw_上海迪士尼_20260225.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        count = len(df)
        print(f"{p}: {count}条")
        total += count
    else:
        print(f"{p}: 文件不存在")

print("=" * 50)
print(f"总计: {total}条")
print("=" * 50)

