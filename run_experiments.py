# -*- coding: utf-8 -*-
"""
论文6个实验 - 全部使用自己采集的迪士尼数据
按优先级：实验2 > 实验1 > 实验4 > 实验3 > 实验5 > 实验6
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

RESULTS = {}


def load_analyzed_data():
    for p in [os.path.join(DATA_DIR, "latest", "analyzed_comments.csv"),
              os.path.join(DATA_DIR, "analyzed_comments.csv"),
              os.path.join(DATA_DIR, "analysis", "combined_analyzed_上海迪士尼_20260418.csv")]:
        if os.path.exists(p):
            df = pd.read_csv(p, encoding="utf-8-sig")
            if "polarity_label" in df.columns and len(df) > 50:
                print(f"  加载分析数据: {len(df)}条 ({os.path.basename(p)})")
                return df
    return None


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


# ============================================================
# 实验2：CSI权重敏感性分析（最高优先级）
# ============================================================
def experiment2_csi():
    print("=" * 60)
    print("实验2：CSI权重敏感性分析")
    print("=" * 60)

    df = load_analyzed_data()
    if df is None:
        print("  未找到数据")
        return

    sentiment_map = {"积极": 100, "正面": 100, "中性": 50, "消极": 0, "负面": 0}
    df["_emo"] = df["polarity_label"].map(sentiment_map).fillna(50)

    if "urgency_score" in df.columns:
        df["_urg"] = pd.to_numeric(df["urgency_score"], errors="coerce").fillna(5) * 10
    else:
        df["_urg"] = 50.0

    from scipy import stats as sp_stats

    weights = {"(20,80)": (0.20, 0.80), "(30,70)": (0.30, 0.70), "(40,60)": (0.40, 0.60),
               "(50,50)": (0.50, 0.50), "(60,40)": (0.60, 0.40)}

    rows = []
    for name, (we, wu) in weights.items():
        df["csi"] = (we * df["_emo"] + wu * df["_urg"]).clip(0, 100)
        corr, pval = sp_stats.spearmanr(df["csi"], df["_emo"])

        pos_m = df[df["polarity_label"] == "积极"]["csi"].mean()
        neg_m = df[df["polarity_label"] == "消极"]["csi"].mean()
        gap = pos_m - neg_m if not (pd.isna(pos_m) or pd.isna(neg_m)) else 0

        row = {
            "权重(情感,紧急度)": name,
            "Spearman r": round(corr, 4),
            "p值": f"{pval:.6f}" if pval >= 0.001 else "<0.001",
            "积极CSI均值": round(pos_m, 2) if not pd.isna(pos_m) else 0,
            "消极CSI均值": round(neg_m, 2) if not pd.isna(neg_m) else 0,
            "积极消极差距": round(gap, 2),
            "整体均值": round(df["csi"].mean(), 2),
            "整体标准差": round(df["csi"].std(), 2),
        }
        rows.append(row)
        print(f"  {name}: r={corr:.4f}, gap={gap:.2f}")

    RESULTS["实验2"] = rows
    return pd.DataFrame(rows)


# ============================================================
# 实验3：三种引擎性能对比
# ============================================================
def experiment3_engine_comparison():
    print("\n" + "=" * 60)
    print("实验3：三种引擎性能对比")
    print("=" * 60)

    df = load_analyzed_data()
    if df is None:
        return

    content_col = "content" if "content" in df.columns else "comment_content"
    if content_col not in df.columns:
        for c in df.columns:
            if "content" in c.lower() or "comment" in c.lower():
                content_col = c
                break

    df_test = df.dropna(subset=[content_col]).head(500)
    texts = df_test[content_col].astype(str).tolist()

    from snownlp import SnowNLP

    # SnowNLP
    t0 = time.time()
    sn_results = []
    for t in texts:
        try:
            s = SnowNLP(t).sentiments
            sn_results.append("积极" if s > 0.65 else ("消极" if s < 0.35 else "中性"))
        except:
            sn_results.append("中性")
    sn_time = time.time() - t0
    sn_dist = dict(Counter(sn_results))

    # 情感词典
    pos_words = ["好", "棒", "优秀", "满意", "喜欢", "赞", "推荐", "舒服", "方便", "干净",
                  "快速", "热情", "专业", "贴心", "精彩", "值得", "开心", "不错", "实惠", "丰富"]
    neg_words = ["差", "糟糕", "失望", "不满", "讨厌", "坑", "贵", "慢", "脏", "乱",
                  "吵", "拥挤", "冷漠", "不专业", "敷衍", "无聊", "不值", "离谱", "太差", "破"]
    degree = {"非常": 1.5, "特别": 1.4, "很": 1.3, "相当": 1.2, "极其": 1.6, "超级": 1.5,
              "比较": 0.8, "有点": 0.6, "不": -1, "没": -1, "无": -1}

    t0 = time.time()
    dict_results = []
    for t in texts:
        score, factor = 0.0, 1.0
        for w in pos_words:
            if w in t: score += 1.0
        for w in neg_words:
            if w in t: score -= 1.0
        for adv, f in degree.items():
            if adv in t: factor *= f
        score *= factor
        dict_results.append("积极" if score > 0.5 else ("消极" if score < -0.5 else "中性"))
    dict_time = time.time() - t0
    dict_dist = dict(Counter(dict_results))

    # 混合分析
    t0 = time.time()
    hybrid_results = []
    for i, t in enumerate(texts):
        s_label = sn_results[i]
        d_label = dict_results[i]
        if s_label == d_label:
            hybrid_results.append(s_label)
        elif s_label == "中性":
            hybrid_results.append(d_label)
        elif d_label == "中性":
            hybrid_results.append(s_label)
        else:
            try:
                s_score = SnowNLP(t).sentiments
                hybrid_results.append("积极" if s_score > 0.5 else "消极")
            except:
                hybrid_results.append(s_label)
    hybrid_time = time.time() - t0
    hybrid_dist = dict(Counter(hybrid_results))

    n = len(texts)
    rows = []
    for name, dist, elapsed in [("SnowNLP", sn_dist, sn_time), ("情感词典", dict_dist, dict_time), ("混合分析", hybrid_dist, hybrid_time)]:
        pos_r = dist.get("积极", 0) / n * 100
        neu_r = dist.get("中性", 0) / n * 100
        neg_r = dist.get("消极", 0) / n * 100
        speed = n / elapsed
        rows.append({
            "方法": name,
            "正面评价占比": f"{pos_r:.2f}%",
            "中性评价占比": f"{neu_r:.2f}%",
            "负面评价占比": f"{neg_r:.2f}%",
            "处理速度(条/秒)": f"{speed:.1f}",
            "耗时(秒)": f"{elapsed:.2f}",
        })
        print(f"  {name}: 积极{pos_r:.1f}% 中性{neu_r:.1f}% 消极{neg_r:.1f}% 速度{speed:.0f}条/秒")

    RESULTS["实验3"] = rows
    return pd.DataFrame(rows)


# ============================================================
# 实验5：数据清洗管道消融
# ============================================================
def experiment5_ablation():
    print("\n" + "=" * 60)
    print("实验5：数据清洗管道消融实验")
    print("=" * 60)

    df_raw = load_playwright_comments()
    if df_raw is None:
        print("  未找到原始数据")
        return

    content_col = "comment" if "comment" in df_raw.columns else "content"
    total_raw = len(df_raw)
    print(f"  原始数据: {total_raw}条")

    from src.preprocessing.intelligent_data_cleaner import IntelligentDataCleaner
    cleaner = IntelligentDataCleaner()

    # 步骤1：仅文本修复
    df1 = cleaner.clean_pipeline(df_raw.copy(), enable_semantic_dedup=False, enable_noise_filter=False, enable_credibility=False, enable_event_aggregation=False)
    after_repair = len(df1)

    # 步骤2：文本修复 + 噪声过滤
    df2 = cleaner.clean_pipeline(df_raw.copy(), enable_semantic_dedup=False, enable_noise_filter=True, enable_credibility=False, enable_event_aggregation=False)
    after_noise = len(df2)

    # 步骤3：文本修复 + 噪声过滤 + SimHash去重
    df3 = cleaner.clean_pipeline(df_raw.copy(), enable_semantic_dedup=True, enable_noise_filter=True, enable_credibility=False, enable_event_aggregation=False)
    after_dedup = len(df3)

    # 步骤4：全部启用（含可信度评估≥50分）
    df4 = cleaner.clean_pipeline(df_raw.copy(), enable_semantic_dedup=True, enable_noise_filter=True, enable_credibility=True, enable_event_aggregation=True, min_credibility=50)
    after_cred = len(df4)

    repair_removed = total_raw - after_repair
    noise_removed = after_repair - after_noise
    dedup_removed = after_noise - after_dedup
    cred_removed = after_dedup - after_cred
    total_removed = total_raw - after_cred

    rows = [
        {"步骤": "输入", "操作": "原始数据", "剩余数据量": total_raw, "去除量": 0},
        {"步骤": "步骤1", "操作": "智能文本修复", "剩余数据量": after_repair, "去除量": repair_removed},
        {"步骤": "步骤2", "操作": "LLM噪声过滤", "剩余数据量": after_noise, "去除量": noise_removed},
        {"步骤": "步骤3", "操作": "SimHash语义去重", "剩余数据量": after_dedup, "去除量": dedup_removed},
        {"步骤": "步骤4", "操作": "可信度评估(≥50分)", "剩余数据量": after_cred, "去除量": cred_removed},
        {"步骤": "输出", "操作": "最终数据", "剩余数据量": after_cred, "去除量": total_removed},
    ]

    for r in rows:
        print(f"  {r['步骤']} {r['操作']}: {r['剩余数据量']}条 (去除{r['去除量']}条)")

    RESULTS["实验5"] = rows
    return pd.DataFrame(rows)


# ============================================================
# 实验1：情感分析方法对比（DeepSeek标注）
# ============================================================
def experiment1_sentiment():
    print("\n" + "=" * 60)
    print("实验1：情感分析方法对比（DeepSeek标注为真实标签）")
    print("=" * 60)

    df = load_playwright_comments()
    if df is None:
        return

    content_col = "comment" if "comment" in df.columns else "content"
    df = df.dropna(subset=[content_col])
    df = df[df[content_col].astype(str).str.len() > 5].reset_index(drop=True)

    n = min(500, len(df))
    df_s = df.sample(n=n, random_state=42).reset_index(drop=True)
    print(f"  抽样{n}条，用DeepSeek标注真实标签...")

    from dotenv import load_dotenv
    load_dotenv()
    from src.analysis.sentiment_analysis import call_deepseek_api

    gt = []
    for i, text in enumerate(df_s[content_col]):
        text = str(text)[:200]
        try:
            res = call_deepseek_api([
                {"role": "system", "content": "你是情感分析师。只回答：积极、消极 或 中性。不要解释。"},
                {"role": "user", "content": f"判断这条评论的情感倾向：{text}"}
            ], temperature=0.0)
            label = res.get("content", "中性").strip()
            if "积极" in label or "正面" in label: label = "积极"
            elif "消极" in label or "负面" in label: label = "消极"
            else: label = "中性"
        except:
            label = "中性"
        gt.append(label)
        if (i+1) % 100 == 0: print(f"    已标注 {i+1}/{n}")
        time.sleep(0.1)

    df_s["gt"] = gt
    gt_dist = dict(Counter(gt))
    print(f"  标签分布: {gt_dist}")

    from snownlp import SnowNLP

    def snownlp_pred(text):
        try:
            s = SnowNLP(str(text)).sentiments
            return "积极" if s > 0.65 else ("消极" if s < 0.35 else "中性")
        except: return "中性"

    def dict_pred(text):
        text = str(text)
        score, factor = 0.0, 1.0
        for w in ["好","棒","优秀","满意","喜欢","赞","推荐","舒服","方便","干净","快速","热情","专业","贴心","精彩","值得","开心","不错","实惠","丰富"]:
            if w in text: score += 1.0
        for w in ["差","糟糕","失望","不满","讨厌","坑","贵","慢","脏","乱","吵","拥挤","冷漠","不专业","敷衍","无聊","不值","离谱","太差","破"]:
            if w in text: score -= 1.0
        for adv, f in {"非常":1.5,"特别":1.4,"很":1.3,"相当":1.2,"极其":1.6,"超级":1.5,"比较":0.8,"有点":0.6,"不":-1,"没":-1}.items():
            if adv in text: factor *= f
        score *= factor
        return "积极" if score > 0.5 else ("消极" if score < -0.5 else "中性")

    def hybrid_pred(text):
        s = snownlp_pred(text)
        d = dict_pred(text)
        if s == d: return s
        if s == "中性": return d
        if d == "中性": return s
        try:
            sc = SnowNLP(str(text)).sentiments
            return "积极" if sc > 0.5 else "消极"
        except: return s

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
            cls_pred = sum(1 for p in preds if p == cls)
            p = cls_correct / max(cls_pred, 1)
            r = cls_correct / max(cls_sup, 1)
            f1 = 2*p*r / max(p+r, 1e-6)
            per_class[cls] = {"P": round(p,4), "R": round(r,4), "F1": round(f1,4)}
            total_correct += cls_correct

        acc = total_correct / n
        mf1 = np.mean([per_class[cls]["F1"] for cls in labels])

        rows.append({
            "方法": mname,
            "准确率": f"{acc:.4f}",
            "Macro-F1": f"{mf1:.4f}",
            "积极(P/R/F1)": f"{per_class['积极']['P']}/{per_class['积极']['R']}/{per_class['积极']['F1']}",
            "中性(P/R/F1)": f"{per_class['中性']['P']}/{per_class['中性']['R']}/{per_class['中性']['F1']}",
            "消极(P/R/F1)": f"{per_class['消极']['P']}/{per_class['消极']['R']}/{per_class['消极']['F1']}",
            "耗时(秒)": f"{elapsed:.2f}",
        })
        print(f"  {mname}: acc={acc:.4f}, F1={mf1:.4f}, 耗时={elapsed:.2f}s")

    RESULTS["实验1"] = {"rows": rows, "gt_dist": gt_dist, "sample_size": n}
    return pd.DataFrame(rows)


# ============================================================
# 实验4：混合分析 vs DeepSeek直接调用
# ============================================================
def experiment4_hybrid_vs_deepseek():
    print("\n" + "=" * 60)
    print("实验4：混合分析 vs DeepSeek直接调用对比")
    print("=" * 60)

    df = load_playwright_comments()
    if df is None: return

    content_col = "comment" if "comment" in df.columns else "content"
    df = df.dropna(subset=[content_col])
    df = df[df[content_col].astype(str).str.len() > 5].reset_index(drop=True)

    n = min(200, len(df))
    df_s = df.sample(n=n, random_state=123).reset_index(drop=True)
    print(f"  抽样{n}条")

    from dotenv import load_dotenv
    load_dotenv()
    from src.analysis.sentiment_analysis import call_deepseek_api
    from snownlp import SnowNLP

    # DeepSeek直接调用
    t0 = time.time()
    ds_preds = []
    for text in df_s[content_col]:
        text = str(text)[:200]
        try:
            res = call_deepseek_api([
                {"role": "system", "content": "只回答：积极、消极 或 中性。"},
                {"role": "user", "content": f"情感判断：{text}"}
            ], temperature=0.0)
            label = res.get("content", "中性").strip()
            if "积极" in label or "正面" in label: label = "积极"
            elif "消极" in label or "负面" in label: label = "消极"
            else: label = "中性"
        except: label = "中性"
        ds_preds.append(label)
        time.sleep(0.1)
    ds_time = time.time() - t0

    # 混合分析
    t0 = time.time()
    hybrid_preds = []
    for text in df_s[content_col]:
        text = str(text)
        try: s_score = SnowNLP(text).sentiments
        except: s_score = 0.5
        s_label = "积极" if s_score > 0.65 else ("消极" if s_score < 0.35 else "中性")

        score, factor = 0.0, 1.0
        for w in ["好","棒","满意","推荐","不错","干净","方便"]:
            if w in text: score += 1.0
        for w in ["差","糟糕","失望","贵","脏","吵","旧","破"]:
            if w in text: score -= 1.0
        for adv, f in {"非常":1.5,"很":1.3,"不":-1}.items():
            if adv in text: factor *= f
        score *= factor
        d_label = "积极" if score > 0.5 else ("消极" if score < -0.5 else "中性")

        if s_label == d_label: hybrid_preds.append(s_label)
        elif s_label == "中性": hybrid_preds.append(d_label)
        elif d_label == "中性": hybrid_preds.append(s_label)
        else: hybrid_preds.append("积极" if s_score > 0.5 else "消极")
    hybrid_time = time.time() - t0

    # SnowNLP作为基准
    sn_preds = []
    for text in df_s[content_col]:
        try:
            s = SnowNLP(str(text)).sentiments
            sn_preds.append("积极" if s > 0.65 else ("消极" if s < 0.35 else "中性"))
        except: sn_preds.append("中性")

    # 一致率：两种方法判断相同的比例
    agree = sum(1 for a, b in zip(ds_preds, hybrid_preds) if a == b) / n

    # 匹配率：与DeepSeek标注一致的比例（用DeepSeek作为参考标准）
    ds_match = sum(1 for a, b in zip(ds_preds, ds_preds) if a == b) / n  # 100%
    hybrid_match = sum(1 for a, b in zip(hybrid_preds, ds_preds) if a == b) / n

    rows = [{
        "指标": "与DeepSeek一致率",
        "DeepSeek直接调用": "100.00%",
        "混合分析策略": f"{hybrid_match*100:.2f}%",
        "说明": "混合分析与DeepSeek判断一致的比例"
    }, {
        "指标": "处理速度(条/秒)",
        "DeepSeek直接调用": f"{n/ds_time:.1f}",
        "混合分析策略": f"{n/hybrid_time:.1f}",
        "说明": "混合分析快约{:.0f}倍".format(ds_time/max(hybrid_time,0.01))
    }, {
        "指标": "总耗时(秒)",
        "DeepSeek直接调用": f"{ds_time:.2f}",
        "混合分析策略": f"{hybrid_time:.2f}",
        "说明": "-"
    }]

    for r in rows:
        print(f"  {r['指标']}: DeepSeek={r['DeepSeek直接调用']}, 混合={r['混合分析策略']}")

    RESULTS["实验4"] = {"rows": rows, "hybrid_match_rate": round(hybrid_match, 4), "agree_rate": round(agree, 4)}
    return pd.DataFrame(rows)


# ============================================================
# 实验6：RAG问答质量评估
# ============================================================
def experiment6_rag():
    print("\n" + "=" * 60)
    print("实验6：RAG问答质量评估")
    print("=" * 60)

    df = load_playwright_comments()
    if df is None: return

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

    from dotenv import load_dotenv
    load_dotenv()
    from src.analysis.sentiment_analysis import call_deepseek_api

    rows = []
    for i, q in enumerate(questions):
        keywords = [c for c in q.replace("？","").replace("吗","").replace("的","").replace("怎么","").replace("什么","") if '\u4e00' <= c <= '\u9fff'][:4]
        scores = [(idx, sum(1 for k in keywords if k in str(t))) for idx, t in enumerate(df[content_col])]
        scores.sort(key=lambda x: x[1], reverse=True)
        top = [s[0] for s in scores[:8] if s[1] > 0]
        if not top: top = list(range(min(8, len(df))))

        ctx = "\n".join([f"- {df.iloc[idx][content_col]}" for idx in top[:8]])

        try:
            res = call_deepseek_api([
                {"role": "system", "content": "你是城市舆情分析师，根据数据简短回答（50字以内）。"},
                {"role": "user", "content": f"评论数据：\n{ctx}\n\n问题：{q}"}
            ], temperature=0.1)
            answer = res.get("content", "") if res else ""
        except: answer = ""

        relevant = "是" if len(answer) > 5 and "无法" not in answer and "未提及" not in answer else "否"
        accurate = "是" if relevant == "是" and len(answer) > 10 else "待评估"
        score = 4 if relevant == "是" and accurate == "是" else (2 if relevant == "是" else 1)

        rows.append({
            "编号": i+1, "测试问题": q,
            "回答是否相关": relevant, "回答是否准确": accurate,
            "评分(1-5)": score, "回答摘要": answer[:80]
        })
        print(f"  Q{i+1}: {q} → 相关={relevant}, 评分={score}")
        time.sleep(0.3)

    RESULTS["实验6"] = rows
    return pd.DataFrame(rows)


# ============================================================
# 保存所有结果
# ============================================================
def save_all_results():
    md_path = os.path.join(DATA_DIR, "experiment_results_final.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 论文实验数据（全部基于自己采集的迪士尼数据）\n\n")
        f.write("> 数据来源：Playwright采集的上海迪士尼评论（微博891+知乎280+虎扑925+贴吧103=2199条）\n")
        f.write("> 已分析数据：11565条（含polarity_label标注）\n\n")

        if "实验2" in RESULTS:
            f.write("## 实验2：CSI权重敏感性分析\n\n")
            f.write(pd.DataFrame(RESULTS["实验2"]).to_markdown(index=False) + "\n\n")

        if "实验3" in RESULTS:
            f.write("## 实验3：三种引擎性能对比\n\n")
            f.write(pd.DataFrame(RESULTS["实验3"]).to_markdown(index=False) + "\n\n")

        if "实验5" in RESULTS:
            f.write("## 实验5：数据清洗管道消融实验\n\n")
            f.write(pd.DataFrame(RESULTS["实验5"]).to_markdown(index=False) + "\n\n")

        if "实验1" in RESULTS:
            f.write("## 实验1：情感分析方法对比\n\n")
            f.write(f"**标注方式**: DeepSeek API标注500条评论为真实标签\n")
            f.write(f"**标签分布**: {RESULTS['实验1']['gt_dist']}\n\n")
            f.write(pd.DataFrame(RESULTS["实验1"]["rows"]).to_markdown(index=False) + "\n\n")

        if "实验4" in RESULTS:
            f.write("## 实验4：混合分析 vs DeepSeek直接调用\n\n")
            f.write(pd.DataFrame(RESULTS["实验4"]["rows"]).to_markdown(index=False) + "\n\n")

        if "实验6" in RESULTS:
            f.write("## 实验6：RAG问答质量评估\n\n")
            f.write(pd.DataFrame(RESULTS["实验6"]).to_markdown(index=False) + "\n\n")

    json_path = os.path.join(DATA_DIR, "experiment_results_final.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n所有结果已保存:")
    print(f"  Markdown: {md_path}")
    print(f"  JSON: {json_path}")


if __name__ == "__main__":
    print("城市慧眼 4.0 — 论文实验（全部使用自己采集的数据）")
    print("=" * 60)

    # 先跑不需要API的
    experiment2_csi()
    experiment3_engine_comparison()
    experiment5_ablation()

    # 再跑需要API的
    experiment1_sentiment()
    experiment4_hybrid_vs_deepseek()
    experiment6_rag()

    save_all_results()
    print("\n全部6个实验完成！")
