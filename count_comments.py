#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计项目Python文件的注释率"""
import os

def count_comments(filepath):
    total = 0
    comment = 0
    blank = 0
    in_docstring = False
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                total += 1
                stripped = line.strip()
                if not stripped:
                    blank += 1
                    continue
                # 检测docstring
                if '"""' in stripped or "'''" in stripped:
                    count = stripped.count('"""') + stripped.count("'''")
                    if count >= 2:
                        comment += 1
                    elif count == 1:
                        in_docstring = not in_docstring
                        comment += 1
                elif in_docstring:
                    comment += 1
                elif stripped.startswith('#'):
                    comment += 1
    except:
        return None
    code = total - blank - comment
    rate = comment / max(total, 1) * 100
    return (total, comment, blank, code, rate)

py_files = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__' and d != 'venv' and d != '.venv']
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(root, f)
            r = count_comments(fp)
            if r and r[3] > 10:
                py_files.append((fp, r))

py_files.sort(key=lambda x: x[1][3], reverse=True)

print(f"{'文件':<60} {'总行':>5} {'注释':>5} {'空行':>5} {'代码':>5} {'注释率':>7}")
print('-' * 95)
total_lines = 0
total_comments = 0
total_code = 0
for fp, (t, c, b, code, rate) in py_files:
    print(f"{fp:<60} {t:>5} {c:>5} {b:>5} {code:>5} {rate:>6.1f}%")
    total_lines += t
    total_comments += c
    total_code += code

print('-' * 95)
overall_rate = total_comments / max(total_lines, 1) * 100
print(f"{'合计':<60} {total_lines:>5} {total_comments:>5} {total_lines-total_comments-total_code:>5} {total_code:>5} {overall_rate:>6.1f}%")
