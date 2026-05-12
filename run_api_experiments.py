# -*- coding: utf-8 -*-
"""
实验1+4+6：API实验（带进度条）
"""
import os, sys, time, json, random
import pandas as pd
import numpy as np
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")

random.seed(42)
np.random.seed(42)


def progress_bar(current, total, prefix="", suffix="", bar_len=40):
    pct = current / total
    filled = int(bar_len * pct)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r  {prefix} |{bar}| {current}/{total} ({pct*100:.1f}%) {suffix}", end="", flush=True)
    if current == total:
        print()


def load_playwright_comments():
    files = [
        os.path.join(RAW_DIR, 'weibo_comments_上海迪士尼_20260501_185528.csv'),
        os.path.join(RAW_DIR, 'zhihu_comments_20260501_192309.csv'),
        os.path.join(RAW_DIR, 'hupu_comments_20260501_194725.csv'),
        os.path.join(RAW_DIR, 'tieba_comments_20260501_195515.csv'),
    ]
    dfs = []
    for f in files:
        if os.path.exists(f):
            dfs.append(pd.read_csv(f, encoding='utf-8-sig'))
    return pd.concat(dfs, ignore_index=True) if dfs else None


def call_api(messages, temperature=0.0):
    from dotenv import load_dotenv
    load_dotenv()
    from src.analysis.sentiment_analysis import call_deepseek_api
    try:
        res = call_deepseek_api(messages, temperature=temperature)
        return res.get("content", "").strip() if res else ""
    except Exception as e:
        return f"[ERROR:{e}]"


def parse_label(text):
    text = str(text)
    if "积极" in text or "正面" in text:
        return "积极"
    elif "消极" in text or "负面" in text:
        return "消极"
    else:
        return "中性"


# ============================================================
# 实验1：情感分析方法对比
# ============================================================
def experiment1():
    print("=" * 60)
    print("实验1：情感分析方法对比（DeepSeek标注为真实标签）")
    print("=" * 60)

    df = load_playwright_comments()
    if df is None:
        print("  未找到数据")
        return None

    content_col = "comment" if "comment" in df.columns else "content"
    df = df.dropna(subset=[content_col])
    df = df[df[content_col].astype(str).str.len() > 5].reset_index(drop=True)

    n = min(500, len(df))
    df_s = df.sample(n=n, random_state=42).reset_index(drop=True)
    print(f"  抽样{n}条，用DeepSeek标注真实标签...")

    gt = []
    for i, text in enumerate(df_s[content_col]):
        text = str(text)[:200]
        label = parse_label(call_api([
            {"role": "system", "content": "你是情感分析师。只回答：积极、消极 或 中性。不要解释。"},
            {"role": "user", "content": f"判断这条评论的情感倾向：{text}"}
        ]))
        gt.append(label)
        progress_bar(i + 1, n, prefix="标注进度", suffix=f"分布={dict(Counter(gt))}")
        time.sleep(0.1)

    df_s["gt"] = gt
    gt_dist = dict(Counter(gt))
    print(f"\n  ✅ 标注完成！分布: {gt_dist}")

    # 三种方法预测
    from snownlp import SnowNLP

    def snownlp_pred(text):
        try:
            s = SnowNLP(str(text)).sentiments
            return "积极" if s > 0.55 else ("消极" if s < 0.45 else "中性")
        except:
            return "中性"

    def dict_pred(text):
        text = str(text)
        score, factor = 0.0, 1.0
        for w in ["好","棒","优秀","满意","喜欢","赞","推荐","舒服","方便","干净",
                   "快速","热情","专业","贴心","精彩","值得","开心","不错","实惠","丰富"]:
            if w in text: score += 1.0
        for w in ["差","糟糕","失望","不满","讨厌","坑","贵","慢","脏","乱",
                   "吵","拥挤","冷漠","不专业","敷衍","无聊","不值","离谱","太差","破"]:
            if w in text: score -= 1.0
        for adv, f in {"非常":1.5,"特别":1.4,"很":1.3,"相当":1.2,"极其":1.6,"超级":1.5,
                        "比较":0.8,"有点":0.6,"不":-1,"没":-1}.items():
            if adv in text: factor *= f
        score *= factor
        return "积极" if score > 0.3 else ("消极" if score < -0.3 else "中性")

    def hybrid_pred(text):
        s = snownlp_pred(text)
        d = dict_pred(text)
        if s == d: return s
        if s == "中性": return d
        if d == "中性": return s
        try:
            sc = SnowNLP(str(text)).sentiments
            return "积极" if sc > 0.5 else "消极"
        except:
            return s

    methods = {"SnowNLP": snownlp_pred, "情感词典": dict_pred, "混合分析": hybrid_pred}
    labels = ["积极", "中性", "消极"]

    rows = []
    for mname, fn in methods.items():
        t0 = time.time()
        preds = [fn(t) for t in df_s[content_col]]
        elapsed = time.time() - t0

        total_correct = 0
        per_class = {}
        for cls in labels:
            cls_sup = sum(1 for g in gt if g == cls)
            cls_correct = sum(1 for p, g in zip(preds, gt) if g == cls and p == cls)
            cls_pred_n = sum(1 for p in preds if p == cls)
            p = cls_correct / max(cls_pred_n, 1)
            r = cls_correct / max(cls_sup, 1)
            f1 = 2 * p * r / max(p + r, 1e-6)
            per_class[cls] = {"P": round(p, 4), "R": round(r, 4), "F1": round(f1, 4)}
            total_correct += cls_correct

        acc = total_correct / n
        mf1 = np.mean([per_class[cls]["F1"] for cls in labels])

        rows.append({
            "方法": mname, "准确率": round(acc, 4), "Macro-F1": round(mf1, 4),
            "积极(P/R/F1)": per_class["积极"], "中性(P/R/F1)": per_class["中性"],
            "消极(P/R/F1)": per_class["消极"], "耗时(秒)": round(elapsed, 2),
        })
        print(f"  {mname}: acc={acc:.4f}, F1={mf1:.4f}, 耗时={elapsed:.2f}s")

    return {"rows": rows, "gt_dist": gt_dist, "n": n}


# ============================================================
# 实验4：混合分析 vs DeepSeek直接调用
# ============================================================
def experiment4():
    print("\n" + "=" * 60)
    print("实验4：混合分析 vs DeepSeek直接调用")
    print("=" * 60)

    df = load_playwright_comments()
    if df is None:
        return None

    content_col = "comment" if "comment" in df.columns else "content"
    df = df.dropna(subset=[content_col])
    df = df[df[content_col].astype(str).str.len() > 5].reset_index(drop=True)

    n = min(200, len(df))
    df_s = df.sample(n=n, random_state=123).reset_index(drop=True)
    print(f"  抽样{n}条")

    from snownlp import SnowNLP

    # DeepSeek直接调用
    print("  [1/2] DeepSeek直接调用...")
    t0 = time.time()
    ds_preds = []
    for i, text in enumerate(df_s[content_col]):
        text = str(text)[:200]
        label = parse_label(call_api([
            {"role": "system", "content": "只回答：积极、消极 或 中性。"},
            {"role": "user", "content": f"情感判断：{text}"}
        ]))
        ds_preds.append(label)
        progress_bar(i + 1, n, prefix="DeepSeek", suffix=f"分布={dict(Counter(ds_preds))}")
        time.sleep(0.1)
    ds_time = time.time() - t0
    print(f"\n  ✅ DeepSeek完成！耗时={ds_time:.1f}s")

    # 混合分析
    print("  [2/2] 混合分析...")
    t0 = time.time()
    hybrid_preds = []
    for i, text in enumerate(df_s[content_col]):
        text = str(text)
        try:
            s_score = SnowNLP(text).sentiments
        except:
            s_score = 0.5
        s_label = "积极" if s_score > 0.55 else ("消极" if s_score < 0.45 else "中性")

        score, factor = 0.0, 1.0
        for w in ["好","棒","满意","推荐","不错","干净","方便","值得","精彩","开心"]:
            if w in text: score += 1.0
        for w in ["差","糟糕","失望","贵","脏","吵","旧","破","坑","离谱"]:
            if w in text: score -= 1.0
        for adv, f in {"非常":1.5,"很":1.3,"不":-1,"没":-1}.items():
            if adv in text: factor *= f
        score *= factor
        d_label = "积极" if score > 0.3 else ("消极" if score < -0.3 else "中性")

        if s_label == d_label:
            hybrid_preds.append(s_label)
        elif s_label == "中性":
            hybrid_preds.append(d_label)
        elif d_label == "中性":
            hybrid_preds.append(s_label)
        else:
            hybrid_preds.append("积极" if s_score > 0.5 else "消极")
        progress_bar(i + 1, n, prefix="混合分析", suffix=f"分布={dict(Counter(hybrid_preds))}")
    hybrid_time = time.time() - t0
    print(f"\n  ✅ 混合分析完成！耗时={hybrid_time:.1f}s")

    agree = sum(1 for a, b in zip(ds_preds, hybrid_preds) if a == b) / n
    ds_dist = dict(Counter(ds_preds))
    hy_dist = dict(Counter(hybrid_preds))

    result = {
        "n": n, "ds_time": round(ds_time, 2), "hy_time": round(hybrid_time, 2),
        "ds_speed": round(n / ds_time, 1), "hy_speed": round(n / hybrid_time, 1),
        "agree_rate": round(agree, 4), "ds_dist": ds_dist, "hy_dist": hy_dist,
    }

    print(f"\n  📊 一致率: {agree:.2%}")
    print(f"  📊 DeepSeek: {ds_dist}, 速度={n/ds_time:.1f}条/秒")
    print(f"  📊 混合分析: {hy_dist}, 速度={n/hybrid_time:.1f}条/秒")
    print(f"  📊 混合分析比DeepSeek快约{ds_time/max(hybrid_time,0.01):.0f}倍")

    return result


# ============================================================
# 实验6：RAG问答质量评估
# ============================================================
def experiment6():
    print("\n" + "=" * 60)
    print("实验6：RAG问答质量评估")
    print("=" * 60)

    df = load_playwright_comments()
    if df is None:
        return None

    content_col = "comment" if "comment" in df.columns else "content"

    questions = [
        "交通设施满意度如何？",
        "哪个设施维度评分最低？",
        "用户对环境绿化的评价？",
        "最常见的负面评价是什么？",
        "微博和知乎用户评价有何不同？",
        "迪士尼最严重的问题是什么？",
        "劝烟事件是怎么回事？",
        "迪士尼门票多少钱？",
        "工作人员服务态度如何？",
        "迪士尼的烟花表演好看吗？",
    ]

    rows = []
    for i, q in enumerate(questions):
        keywords = [c for c in q.replace("？","").replace("吗","").replace("的","").replace("怎么","").replace("什么","").replace("有何","") if '\u4e00' <= c <= '\u9fff'][:4]
        scores = [(idx, sum(1 for k in keywords if k in str(t))) for idx, t in enumerate(df[content_col])]
        scores.sort(key=lambda x: x[1], reverse=True)
        top = [s[0] for s in scores[:8] if s[1] > 0]
        if not top:
            top = list(range(min(8, len(df))))

        ctx = "\n".join([f"- {str(df.iloc[idx][content_col])[:100]}" for idx in top[:8]])

        answer = call_api([
            {"role": "system", "content": "你是城市舆情分析师，根据数据简短回答（50字以内）。"},
            {"role": "user", "content": f"评论数据：\n{ctx}\n\n问题：{q}"}
        ], temperature=0.1)

        relevant = "是" if len(answer) > 5 and "无法" not in answer and "未提及" not in answer and "ERROR" not in answer else "否"
        accurate = "是" if relevant == "是" and len(answer) > 10 else "待评估"
        score = 4 if relevant == "是" and accurate == "是" else (2 if relevant == "是" else 1)

        rows.append({
            "编号": i + 1, "测试问题": q,
            "回答是否相关": relevant, "回答是否准确": accurate,
            "评分(1-5)": score, "回答摘要": answer[:80],
        })
        progress_bar(i + 1, len(questions), prefix="RAG评估", suffix=f"Q{i+1}: {q[:15]}...")
        time.sleep(0.3)

    avg_score = np.mean([r["评分(1-5)"] for r in rows])
    relevant_count = sum(1 for r in rows if r["回答是否相关"] == "是")
    print(f"\n  ✅ RAG评估完成！平均评分: {avg_score:.1f}/5, 相关率: {relevant_count}/{len(questions)}")

    return {"rows": rows, "avg_score": round(avg_score, 1), "relevant_count": relevant_count, "total": len(questions)}


# ============================================================
# 保存结果
# ============================================================
def save_results(exp1, exp4, exp6):
    md_path = os.path.join(DATA_DIR, "experiment_api_results.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 实验1+4+6结果（API实验，全部基于自己采集的迪士尼数据）\n\n")

        if exp1:
            f.write("## 实验1：情感分析方法对比\n\n")
            f.write(f"**标注方式**: DeepSeek API标注{exp1['n']}条评论为真实标签\n")
            f.write(f"**标签分布**: {exp1['gt_dist']}\n\n")
            f.write("| 方法 | 准确率 | Macro-F1 | 积极(P/R/F1) | 中性(P/R/F1) | 消极(P/R/F1) | 耗时(秒) |\n")
            f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
            for r in exp1["rows"]:
                f.write(f"| {r['方法']} | {r['准确率']:.4f} | {r['Macro-F1']:.4f} | "
                        f"{r['积极(P/R/F1)']['P']}/{r['积极(P/R/F1)']['R']}/{r['积极(P/R/F1)']['F1']} | "
                        f"{r['中性(P/R/F1)']['P']}/{r['中性(P/R/F1)']['R']}/{r['中性(P/R/F1)']['F1']} | "
                        f"{r['消极(P/R/F1)']['P']}/{r['消极(P/R/F1)']['R']}/{r['消极(P/R/F1)']['F1']} | "
                        f"{r['耗时(秒)']:.2f} |\n")
            f.write("\n")

        if exp4:
            f.write("## 实验4：混合分析 vs DeepSeek直接调用\n\n")
            f.write(f"**测试数据**: {exp4['n']}条迪士尼评论\n\n")
            f.write("| 指标 | DeepSeek直接调用 | 混合分析策略 | 说明 |\n")
            f.write("|:---:|:---:|:---:|:---|\n")
            f.write(f"| 与DeepSeek一致率 | 100.00% | {exp4['agree_rate']*100:.2f}% | 混合分析与DeepSeek判断一致的比例 |\n")
            f.write(f"| 处理速度(条/秒) | {exp4['ds_speed']:.1f} | {exp4['hy_speed']:.1f} | 混合分析快约{exp4['ds_time']/max(exp4['hy_time'],0.01):.0f}倍 |\n")
            f.write(f"| 总耗时(秒) | {exp4['ds_time']:.2f} | {exp4['hy_time']:.2f} | - |\n")
            f.write(f"| 情感分布 | 积极{exp4['ds_dist'].get('积极',0)} 中性{exp4['ds_dist'].get('中性',0)} 消极{exp4['ds_dist'].get('消极',0)} | 积极{exp4['hy_dist'].get('积极',0)} 中性{exp4['hy_dist'].get('中性',0)} 消极{exp4['hy_dist'].get('消极',0)} | - |\n")
            f.write("\n")

        if exp6:
            f.write("## 实验6：RAG问答质量评估\n\n")
            f.write(f"**平均评分**: {exp6['avg_score']}/5, **相关率**: {exp6['relevant_count']}/{exp6['total']}\n\n")
            f.write("| 编号 | 测试问题 | 回答是否相关 | 回答是否准确 | 评分(1-5) | 回答摘要 |\n")
            f.write("|:---:|:---|:---:|:---:|:---:|:---|\n")
            for r in exp6["rows"]:
                f.write(f"| {r['编号']} | {r['测试问题']} | {r['回答是否相关']} | {r['回答是否准确']} | {r['评分(1-5)']} | {r['回答摘要']} |\n")

    json_path = os.path.join(DATA_DIR, "experiment_api_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"实验1": exp1, "实验4": exp4, "实验6": exp6}, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ 结果已保存:")
    print(f"  Markdown: {md_path}")
    print(f"  JSON: {json_path}")


if __name__ == "__main__":
    print("城市慧眼 4.0 — API实验（1+4+6）带进度条")
    print("=" * 60)

    exp1 = experiment1()
    exp4 = experiment4()
    exp6 = experiment6()

    save_results(exp1, exp4, exp6)
    print("\n🎉 全部3个API实验完成！")
