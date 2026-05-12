# -*- coding: utf-8 -*-
"""
精确率/召回率实验 V4：关键词预标注作为平衡GT
用关键词筛选构建三类均衡测试集，关键词标注作为Ground Truth
计算SnowNLP/情感词典/DeepSeek三种方法的P/R/F1
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

RESULT_FILE = os.path.join(DATA_DIR, "precision_recall_experiment.json")


def progress_bar(current, total, prefix="", suffix="", bar_len=40):
    pct = current / total
    filled = int(bar_len * pct)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r  {prefix} |{bar}| {current}/{total} ({pct*100:.1f}%) {suffix}", end="", flush=True)
    if current == total:
        print()


def load_all_comments():
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
    if not dfs:
        return None
    df = pd.concat(dfs, ignore_index=True)
    col = "comment" if "comment" in df.columns else "content"
    df = df.dropna(subset=[col])
    df = df[df[col].astype(str).str.len() > 5].reset_index(drop=True)
    return df, col


def call_deepseek(messages, temperature=0.0, max_retries=3):
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    base_url = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    import requests
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 50
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(base_url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"\n  [RETRY {attempt+1}] API错误: {e}, {wait}秒后重试...")
                time.sleep(wait)
            else:
                return "[ERROR]"


def parse_label(text):
    text = str(text)
    if "积极" in text or "正面" in text or "positive" in text.lower():
        return "积极"
    elif "消极" in text or "负面" in text or "negative" in text.lower():
        return "消极"
    else:
        return "中性"


def snownlp_pred(text):
    from snownlp import SnowNLP
    try:
        s = SnowNLP(str(text)).sentiments
        return "积极" if s > 0.55 else ("消极" if s < 0.45 else "中性")
    except:
        return "中性"


def dict_pred(text):
    text = str(text)
    score, factor = 0.0, 1.0
    pos_words = ["好","棒","优秀","满意","喜欢","赞","推荐","舒服","方便","干净",
                 "快速","热情","专业","贴心","精彩","值得","开心","不错","实惠","丰富",
                 "惊喜","完美","感动","欢乐","有趣","好玩","漂亮","壮观","震撼","温馨"]
    neg_words = ["差","糟糕","失望","不满","讨厌","坑","贵","慢","脏","乱",
                 "吵","拥挤","冷漠","不专业","敷衍","无聊","不值","离谱","太差","破",
                 "难吃","难喝","恶心","黑心","骗","坑人","垃圾","烂","坑爹","宰"]
    for w in pos_words:
        if w in text:
            score += 1.0
    for w in neg_words:
        if w in text:
            score -= 1.0
    for adv, f in {"非常":1.5,"特别":1.4,"很":1.3,"相当":1.2,"极其":1.6,"超级":1.5,
                    "比较":0.8,"有点":0.6,"稍微":0.5,"不":-1,"没":-1,"无":-1,"非":-1}.items():
        if adv in text:
            factor *= f
    score *= factor
    return "积极" if score > 0.3 else ("消极" if score < -0.3 else "中性")


def deepseek_pred(text, temperature=0.0):
    label = parse_label(call_deepseek([
        {"role": "system", "content": "你是情感分析师。对评论进行情感分类。包含赞美/满意/开心→积极，包含抱怨/不满/失望→消极，纯客观无情感→中性。尽量减少中性判断。只回答一个词：积极、消极 或 中性。"},
        {"role": "user", "content": f"判断这条评论的情感倾向：{str(text)[:200]}"}
    ], temperature=temperature))
    return label


def compute_metrics(preds, gts, labels):
    total_correct = sum(1 for p, g in zip(preds, gts) if p == g)
    accuracy = total_correct / len(gts)

    per_class = {}
    for cls in labels:
        tp = sum(1 for p, g in zip(preds, gts) if p == cls and g == cls)
        fp = sum(1 for p, g in zip(preds, gts) if p == cls and g != cls)
        fn = sum(1 for p, g in zip(preds, gts) if p != cls and g == cls)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-6)
        support = sum(1 for g in gts if g == cls)
        per_class[cls] = {
            "P": round(precision, 4),
            "R": round(recall, 4),
            "F1": round(f1, 4),
            "TP": tp, "FP": fp, "FN": fn, "Support": support
        }

    macro_p = np.mean([per_class[cls]["P"] for cls in labels])
    macro_r = np.mean([per_class[cls]["R"] for cls in labels])
    macro_f1 = np.mean([per_class[cls]["F1"] for cls in labels])
    weighted_p = sum(per_class[cls]["P"] * per_class[cls]["Support"] for cls in labels) / len(gts)
    weighted_r = sum(per_class[cls]["R"] * per_class[cls]["Support"] for cls in labels) / len(gts)
    weighted_f1 = sum(per_class[cls]["F1"] * per_class[cls]["Support"] for cls in labels) / len(gts)

    return {
        "accuracy": round(accuracy, 4),
        "macro_P": round(macro_p, 4),
        "macro_R": round(macro_r, 4),
        "macro_F1": round(macro_f1, 4),
        "weighted_P": round(weighted_p, 4),
        "weighted_R": round(weighted_r, 4),
        "weighted_F1": round(weighted_f1, 4),
        "per_class": per_class,
        "pred_dist": dict(Counter(preds)),
        "gt_dist": dict(Counter(gts)),
    }


POS_KW = ["好","棒","满意","喜欢","推荐","值得","开心","不错","精彩","好玩",
          "惊喜","完美","欢乐","漂亮","壮观","震撼","温馨","舒服","方便","热情"]
NEG_KW = ["差","糟糕","失望","不满","讨厌","坑","贵","慢","脏","乱",
          "吵","拥挤","冷漠","无聊","不值","离谱","破","恶心","垃圾","烂"]
NEU_KW = ["觉得","认为","就是","可以","还行","一般","普通","不过","但是","其实"]


def keyword_label(text):
    has_pos = any(k in text for k in POS_KW)
    has_neg = any(k in text for k in NEG_KW)
    if has_pos and not has_neg:
        return "积极"
    elif has_neg and not has_pos:
        return "消极"
    else:
        return "中性"


def run_experiment():
    print("=" * 70)
    print("  情感分析精确率/召回率实验 V4（关键词GT + 平衡测试集）")
    print("  Ground Truth: 关键词预标注（互斥筛选）")
    print("  对比方法: SnowNLP / 情感词典 / DeepSeek(独立调用)")
    print("=" * 70)

    result = load_all_comments()
    if result is None:
        print("  ❌ 未找到数据文件")
        return
    df, col = result
    print(f"  数据总量: {len(df)}条")

    # Step 0: 关键词标注 + 平衡抽样
    print(f"\n  关键词标注中...")
    df["kw_label"] = df[col].astype(str).apply(keyword_label)
    kw_dist = dict(Counter(df["kw_label"]))
    print(f"  关键词标注分布: {kw_dist}")

    pos_df = df[df["kw_label"] == "积极"]
    neg_df = df[df["kw_label"] == "消极"]
    neu_df = df[df["kw_label"] == "中性"]

    n_per_class = min(150, len(pos_df), len(neg_df), len(neu_df))
    print(f"  每类抽取: {n_per_class}条, 共{n_per_class*3}条")

    df_pos = pos_df.sample(n=n_per_class, random_state=42)
    df_neg = neg_df.sample(n=n_per_class, random_state=42)
    df_neu = neu_df.sample(n=n_per_class, random_state=42)

    df_s = pd.concat([df_pos, df_neg, df_neu], ignore_index=True)
    df_s = df_s.sample(frac=1, random_state=42).reset_index(drop=True)
    n = len(df_s)

    gt = df_s["kw_label"].tolist()
    gt_dist = dict(Counter(gt))
    print(f"  GT分布: {gt_dist}")

    # ========== Step 1: SnowNLP预测 ==========
    print(f"\n{'='*70}")
    print(f"  Step 1/3: SnowNLP预测")
    print(f"{'='*70}")

    t0 = time.time()
    snownlp_preds = []
    for i, text in enumerate(df_s[col]):
        snownlp_preds.append(snownlp_pred(text))
        progress_bar(i + 1, n, prefix="SnowNLP")
    snownlp_time = time.time() - t0
    print(f"\n  ✅ SnowNLP完成！耗时={snownlp_time:.2f}s, 分布={dict(Counter(snownlp_preds))}")

    # ========== Step 2: 情感词典预测 ==========
    print(f"\n{'='*70}")
    print(f"  Step 2/3: 情感词典预测")
    print(f"{'='*70}")

    t0 = time.time()
    dict_preds = []
    for i, text in enumerate(df_s[col]):
        dict_preds.append(dict_pred(text))
        progress_bar(i + 1, n, prefix="情感词典")
    dict_time = time.time() - t0
    print(f"\n  ✅ 情感词典完成！耗时={dict_time:.2f}s, 分布={dict(Counter(dict_preds))}")

    # ========== Step 3: DeepSeek独立调用预测 ==========
    print(f"\n{'='*70}")
    print(f"  Step 3/3: DeepSeek独立调用预测 ({n}条)")
    print(f"{'='*70}")

    t0 = time.time()
    ds_preds = []
    for i, text in enumerate(df_s[col]):
        text = str(text)[:200]
        label = deepseek_pred(text, temperature=0.1)
        ds_preds.append(label)
        progress_bar(i + 1, n, prefix="DeepSeek", suffix=f"分布={dict(Counter(ds_preds))}")
        time.sleep(0.12)
    ds_time = time.time() - t0
    print(f"\n  ✅ DeepSeek完成！耗时={ds_time:.2f}s, 分布={dict(Counter(ds_preds))}")

    # ========== 计算指标 ==========
    labels = ["积极", "中性", "消极"]

    print(f"\n{'='*70}")
    print(f"  计算评估指标")
    print(f"{'='*70}")

    snownlp_metrics = compute_metrics(snownlp_preds, gt, labels)
    dict_metrics = compute_metrics(dict_preds, gt, labels)
    ds_metrics = compute_metrics(ds_preds, gt, labels)

    snownlp_metrics["time_sec"] = round(snownlp_time, 2)
    dict_metrics["time_sec"] = round(dict_time, 2)
    ds_metrics["time_sec"] = round(ds_time, 2)

    results = {
        "n": n,
        "gt_method": "关键词预标注（互斥筛选）",
        "gt_dist": gt_dist,
        "SnowNLP": snownlp_metrics,
        "情感词典": dict_metrics,
        "DeepSeek": ds_metrics,
    }

    # ========== 打印结果 ==========
    print(f"\n{'='*70}")
    print(f"  📊 实验结果汇总")
    print(f"{'='*70}")
    print(f"  Ground Truth: 关键词预标注, 分布: {gt_dist}")
    print(f"  样本量: {n}")
    print()

    print(f"  {'方法':<10} {'准确率':>8} {'Macro-P':>8} {'Macro-R':>8} {'Macro-F1':>8} {'W-P':>8} {'W-R':>8} {'W-F1':>8} {'耗时(s)':>8}")
    print(f"  {'-'*80}")
    for name, m in [("SnowNLP", snownlp_metrics), ("情感词典", dict_metrics), ("DeepSeek", ds_metrics)]:
        print(f"  {name:<10} {m['accuracy']:>8.4f} {m['macro_P']:>8.4f} {m['macro_R']:>8.4f} {m['macro_F1']:>8.4f} {m['weighted_P']:>8.4f} {m['weighted_R']:>8.4f} {m['weighted_F1']:>8.4f} {m['time_sec']:>8.2f}")

    print()
    for name, m in [("SnowNLP", snownlp_metrics), ("情感词典", dict_metrics), ("DeepSeek", ds_metrics)]:
        print(f"  {name} 各类别指标:")
        print(f"    {'类别':<6} {'P':>8} {'R':>8} {'F1':>8} {'Support':>8}")
        for cls in labels:
            pc = m["per_class"][cls]
            print(f"    {cls:<6} {pc['P']:>8.4f} {pc['R']:>8.4f} {pc['F1']:>8.4f} {pc['Support']:>8d}")

    # ========== 保存结果 ==========
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  ✅ 结果已保存: {RESULT_FILE}")

    # ========== 生成Markdown表格 ==========
    md_path = os.path.join(DATA_DIR, "precision_recall_experiment.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 情感分析精确率/召回率实验结果\n\n")
        f.write(f"**实验数据**: {n}条迪士尼评论（关键词筛选+平衡抽样，每类{n_per_class}条）\n")
        f.write(f"**Ground Truth**: 关键词预标注（互斥筛选：含积极词且不含消极词→积极，含消极词且不含积极词→消极，其余→中性）\n")
        f.write(f"**GT分布**: 积极{gt_dist.get('积极',0)} / 中性{gt_dist.get('中性',0)} / 消极{gt_dist.get('消极',0)}\n\n")

        f.write("## 总体指标对比\n\n")
        f.write("| 方法 | 准确率 | Macro-P | Macro-R | Macro-F1 | Weighted-P | Weighted-R | Weighted-F1 | 耗时(秒) |\n")
        f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        for name, m in [("SnowNLP", snownlp_metrics), ("情感词典", dict_metrics), ("DeepSeek", ds_metrics)]:
            f.write(f"| {name} | {m['accuracy']:.4f} | {m['macro_P']:.4f} | {m['macro_R']:.4f} | {m['macro_F1']:.4f} | {m['weighted_P']:.4f} | {m['weighted_R']:.4f} | {m['weighted_F1']:.4f} | {m['time_sec']:.2f} |\n")

        f.write("\n## 各类别详细指标\n\n")
        for name, m in [("SnowNLP", snownlp_metrics), ("情感词典", dict_metrics), ("DeepSeek", ds_metrics)]:
            f.write(f"### {name}\n\n")
            f.write("| 类别 | 精确率(P) | 召回率(R) | F1值 | 样本数 |\n")
            f.write("|:---:|:---:|:---:|:---:|:---:|\n")
            for cls in labels:
                pc = m["per_class"][cls]
                f.write(f"| {cls} | {pc['P']:.4f} | {pc['R']:.4f} | {pc['F1']:.4f} | {pc['Support']} |\n")
            f.write(f"\n预测分布: {m['pred_dist']}\n\n")

        f.write("## 论文可用数据（替换估算值）\n\n")
        f.write("| 方法 | 精确率(Macro) | 召回率(Macro) | F1(Macro) | 精确率(Weighted) | 召回率(Weighted) | F1(Weighted) |\n")
        f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        for name, m in [("SnowNLP", snownlp_metrics), ("情感词典", dict_metrics), ("DeepSeek", ds_metrics)]:
            f.write(f"| {name} | {m['macro_P']:.4f} | {m['macro_R']:.4f} | {m['macro_F1']:.4f} | {m['weighted_P']:.4f} | {m['weighted_R']:.4f} | {m['weighted_F1']:.4f} |\n")

    print(f"  ✅ Markdown已保存: {md_path}")
    print(f"\n🎉 实验完成！")


if __name__ == "__main__":
    run_experiment()
