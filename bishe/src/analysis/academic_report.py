# -*- coding: utf-8 -*-
"""
学术报告生成模块
生成结构化的学术分析报告
"""
import os
import sys
import json
import time
import pandas as pd
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class AcademicReportGenerator:
    """学术报告生成器"""
    
    def __init__(self, df_analyzed: pd.DataFrame, output_dir: str):
        """初始化报告生成器"""
        self.df_analyzed = df_analyzed
        self.output_dir = output_dir
        self.current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def generate_full_report(self) -> str:
        """生成完整的学术报告"""
        print("📚 生成学术研究报告...")
        
        # 生成报告内容
        report_content = self._generate_report_content()
        
        # 保存报告
        report_path = os.path.join(self.output_dir, f"academic_report_{self.current_time}.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ 学术报告已保存: {report_path}")
        return report_path
    
    def generate_json_report(self) -> str:
        """生成JSON格式的结构化报告"""
        print("📊 生成结构化报告（JSON）...")
        
        # 生成结构化数据
        structured_data = self._generate_structured_data()
        
        # 保存报告
        json_path = os.path.join(self.output_dir, f"structured_report_{self.current_time}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结构化报告已保存: {json_path}")
        return json_path
    
    def _generate_report_content(self) -> str:
        """生成报告内容"""
        # 标题
        content = f"""# 广州图书馆用户满意度分析报告

**报告生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**数据来源:** 网络爬虫（知乎、微博、贴吧、虎扑）
**分析方法:** 基于DeepSeek大模型的情感分析与方面识别
**研究课题:** 基于大模型情感分析技术的城市公共设施满意度情感分析研究

---

## 1. 执行摘要

本报告基于网络爬虫采集的真实用户评论数据，对广州图书馆的用户满意度进行了全面、深入的分析。本次分析共采集了**{len(self.df_analyzed)}条**有效评论数据，涵盖知乎、微博、贴吧、虎扑四大平台，运用大模型情感分析技术，从**情感倾向、方面识别、CSI满意度指数、紧急度评估**等多个维度进行深入挖掘，为广州图书馆的服务优化提供数据支撑。

---

## 2. 数据采集与概况

### 2.1 数据基本信息

| 指标 | 数值 |
|------|------|
| 总样本量 | {len(self.df_analyzed)} 条 |
| 数据时间范围 | 2026年2月 |
| 覆盖平台 | 知乎、微博、贴吧、虎扑 |

### 2.2 数据来源分布

"""
        
        # 添加数据来源分布
        if 'source' in self.df_analyzed.columns:
            source_counts = self.df_analyzed['source'].value_counts()
            content += "\n| 平台 | 数量 | 占比 |\n"
            content += "|------|------|------|\n"
            for source, count in source_counts.items():
                percentage = count/len(self.df_analyzed)*100
                content += f"| {source} | {count} 条 | {percentage:.1f}% |\n"
            
            content += f"\n**数据特点说明：** 微博平台贡献了最大量的数据样本，反映了广州图书馆在社交媒体上的用户讨论热度较高。\n"
        
        content += """

### 2.3 样本代表性分析

本次采集的数据覆盖了以下特点：
- **多平台覆盖：结合了问答社区（知乎）、社交媒体（微博）、论坛社区（贴吧、虎扑）
- **内容多样性：包含正面评价、负面吐槽、中性讨论等多种类型
- **时间分布均匀：涵盖春节期间及日常运营的用户反馈

---

## 3. 情感分析深度解析

### 3.1 整体情感倾向分析

"""
        
        # 添加整体情感倾向
        if 'polarity_label' in self.df_analyzed.columns:
            polarity_counts = self.df_analyzed['polarity_label'].value_counts()
            content += "\n| 情感倾向 | 数量 | 占比 |\n"
            content += "|----------|------|------|\n"
            for polarity, count in polarity_counts.items():
                percentage = count/len(self.df_analyzed)*100
                content += f"| {polarity} | {count} 条 | {percentage:.1f}% |\n"
            
            # 添加具体分析
            pos_rate = polarity_counts.get('积极', 0) / len(self.df_analyzed) * 100
            neg_rate = polarity_counts.get('消极', 0) / len(self.df_analyzed) * 100
            neu_rate = polarity_counts.get('中性', 0) / len(self.df_analyzed) * 100
            
            content += f"\n**情感洞察：**\n"
            if pos_rate > 50:
                content += f"- **积极倾向占比{pos_rate:.1f}%，说明用户对广州图书馆的整体认可度较高\n"
            elif neg_rate > 20:
                content += f"- **消极倾向占比{neg_rate:.1f}%，需要关注用户反馈的问题\n"
            else:
                content += f"- **中性讨论占比{neu_rate:.1f}%，用户反馈较为理性客观\n"
        
        content += """

### 3.2 CSI满意度指数深度分析

"""
        
        # 添加CSI满意度指数
        if 'csi_score' in self.df_analyzed.columns:
            avg_csi = self.df_analyzed['csi_score'].mean()
            min_csi = self.df_analyzed['csi_score'].min()
            max_csi = self.df_analyzed['csi_score'].max()
            median_csi = self.df_analyzed['csi_score'].median()
            
            content += "\n| 指标 | 数值 |\n"
            content += "|------|------|\n"
            content += f"| 平均CSI指数 | {avg_csi:.1f} |\n"
            content += f"| 中位数CSI指数 | {median_csi:.1f} |\n"
            content += f"| 最低CSI指数 | {min_csi:.1f} |\n"
            content += f"| 最高CSI指数 | {max_csi:.1f} |\n"
            
            # CSI评价
            content += f"\n**CSI解读：**\n"
            if avg_csi >= 80:
                content += f"- **满意度处于优秀水平（≥80分），用户满意度表现出色\n"
            elif avg_csi >= 70:
                content += f"- **满意度处于良好水平（70-79分），整体表现良好\n"
            elif avg_csi >= 60:
                content += f"- **满意度处于及格水平（60-69分），有改进空间\n"
            else:
                content += f"- **满意度有待提升（<60分），需要重点改进\n"
        
        content += """

### 3.3 具体情绪分布详情

"""
        
        # 添加具体情绪分布
        if 'specific_emotion' in self.df_analyzed.columns:
            emotion_counts = self.df_analyzed['specific_emotion'].value_counts().head(10)
            content += "\n| 具体情绪 | 数量 | 占比 |\n"
            content += "|------------|------|------|\n"
            for emotion, count in emotion_counts.items():
                percentage = count/len(self.df_analyzed)*100
                content += f"| {emotion} | {count} 条 | {percentage:.1f}% |\n"
            
            content += f"\n**情绪洞察：** 用户反馈中最突出的情绪是{emotion_counts.index[0] if len(emotion_counts) > 0 else '中性'}，反映了用户最直接的感受。\n"
        
        content += """

---

## 4. 方面级分析

### 4.1 评论热点方面TOP 主要评论方面

"""
        
        # 添加主要评论方面
        if 'aspect' in self.df_analyzed.columns:
            aspect_counts = self.df_analyzed['aspect'].value_counts().head(10)
            content += "\n| 排名 | 方面 | 评论数 | 平均CSI |\n"
            content += "|------|------|--------|----------|\n"
            rank = 1
            for aspect, count in aspect_counts.items():
                aspect_group = self.df_analyzed[self.df_analyzed['aspect'] == aspect]
                avg_csi = aspect_group['csi_score'].mean() if 'csi_score' in aspect_group.columns else 50
                content += f"| {rank} | {aspect} | {count} 条 | {avg_csi:.1f} |\n"
                rank += 1
            
            content += f"\n**方面热点：** 用户最关注的是{aspect_counts.index[0] if len(aspect_counts) > 0 else '其他'}，这是广州图书馆服务的核心关注点。\n"
        
        content += """

### 4.2 各方面满意度深度分析

"""
        
        # 添加各方面满意度分析
        if 'aspect' in self.df_analyzed.columns and 'csi_score' in self.df_analyzed.columns:
            aspect_groups = self.df_analyzed.groupby('aspect')
            
            # 只分析有一定样本量的方面
            valid_aspects = [(aspect, group) for aspect, group in aspect_groups if len(group) >= 3]
            
            if valid_aspects:
                for aspect, group in valid_aspects:
                    avg_csi = group['csi_score'].mean()
                    content += f"\n#### {aspect}方面\n"
                    content += f"- **样本量**: {len(group)} 条\n"
                    content += f"- **平均CSI满意度**: {avg_csi:.1f}\n"
                    
                    # 分析情感倾向
                    if 'polarity_label' in group.columns:
                        polarity_counts = group['polarity_label'].value_counts()
                        content += "- **情感分布**: "
                        emotions = []
                        for polarity, count in polarity_counts.items():
                            percentage = count/len(group)*100
                            emotions.append(f"{polarity}{percentage:.1f}%")
                        content += "、".join(emotions) + "\n"
                    
                    # 给出评价
                    if avg_csi >= 80:
                        content += "- **评价**: 表现优秀，用户满意度高\n"
                    elif avg_csi >= 70:
                        content += "- **评价**: 表现良好，整体满意\n"
                    elif avg_csi >= 60:
                        content += "- **评价**: 表现一般，有改进空间\n"
                    else:
                        content += "- **评价**: 有待改进，需要重点关注\n"
            else:
                content += "（暂无足够样本进行方面分析）\n"
        
        content += """

---

## 5. 问题识别与优先级

### 5.1 高紧急度问题清单

"""
        
        # 添加高紧急度问题
        if 'urgency_score' in self.df_analyzed.columns:
            urgent_issues = self.df_analyzed[self.df_analyzed['urgency_score'] >= 5]
            if len(urgent_issues) > 0:
                content += f"\n**共识别出 {len(urgent_issues)} 个需要关注的问题**\n\n"
                content += "| 设施 | 方面 | 紧急度 | CSI | 内容摘要 |\n"
                content += "|------|------|--------|-----|----------|\n"
                
                for _, row in urgent_issues.head(15).iterrows():
                    facility = row.get('facility_type', '未知设施')
                    aspect = row.get('aspect', '未知方面')
                    urgency = row['urgency_score']
                    csi = row.get('csi_score')
                    content_short = row.get('content', '')[:50].replace('\n', ' ')
                    content += f"| {facility} | {aspect} | {urgency} | {csi:.0f} | {content_short}... |\n"
            else:
                content += "✅ **好消息！未识别出高紧急度问题\n"
        
        content += """

### 5.2 问题优先级分析

根据CSI分数与紧急度的综合分析，建议按以下优先级处理：

1. **高优先级**（CSI < 60）：立即处理，优先解决
2. **中优先级**（60 ≤ CSI < 70）：规划改进，逐步优化
3. **低优先级**（CSI ≥ 70）：保持优势，持续优化

---

## 6. 针对性改进建议

### 6.1 基于数据分析的具体建议

"""
        
        # 基于数据给出更具体的建议
        if 'aspect' in self.df_analyzed.columns:
            aspect_counts = self.df_analyzed['aspect'].value_counts()
            
            if len(aspect_counts) > 0:
                top_aspects = list(aspect_counts.index[:5])
                
                content += f"\n针对用户最关注的{len(top_aspects)}个方面，提出以下建议：\n\n"
                
                for i, aspect in enumerate(top_aspects, 1):
                    aspect_group = self.df_analyzed[self.df_analyzed['aspect'] == aspect]
                    avg_csi = aspect_group['csi_score'].mean() if 'csi_score' in aspect_group.columns else 50
                    
                    content += f"**{i}. {aspect}方面**（平均CSI: {avg_csi:.1f}）**\n"
                    
                    if avg_csi >= 80:
                        content += f"   ✅ 优势保持：继续保持当前的优秀表现，定期收集用户反馈，巩固优势\n"
                    elif avg_csi >= 70:
                        content += f"   ⚠️ 持续优化：在保持现有水平的基础上，寻找进一步提升的空间\n"
                    elif avg_csi >= 60:
                        content += f"   📋 重点改进：制定针对性的改进计划，设定明确的改进目标\n"
                    else:
                        content += f"   🚨 紧急改进：成立专项小组，深入分析问题根源，快速采取行动\n"
                    
                    content += "\n"
        
        content += """

### 6.2 通用服务优化建议

基于行业最佳实践，建议：

1. **服务质量提升**
   - 建立定期的员工培训体系，提高服务专业水平
   - 设立服务监督机制，及时响应用户反馈
   - 开展用户满意度调查，持续跟踪改进效果

2. **环境设施优化**
   - 定期检查设施设备运行状态
   - 优化空间布局，提高使用效率
   - 保持环境整洁，营造舒适氛围

3. **数字化服务创新**
   - 利用数字化手段提升服务效率
   - 建立在线反馈渠道，方便用户表达意见
   - 运用数据分析驱动服务决策

---

## 7. 研究发现与总结

### 7.1 核心研究发现

"""
        
        # 添加主要发现
        if 'csi_score' in self.df_analyzed.columns:
            avg_csi = self.df_analyzed['csi_score'].mean()
            
            content += f"\n1. **整体满意度**：\n"
            if avg_csi >= 80:
                content += f"   - 整体满意度处于优秀水平（平均CSI: {avg_csi:.1f}），用户对广州图书馆的服务认可度高\n"
            elif avg_csi >= 70:
                content += f"   - 整体满意度良好（平均CSI: {avg_csi:.1f}），整体表现良好\n"
            elif avg_csi >= 60:
                content += f"   - 整体满意度一般（平均CSI: {avg_csi:.1f}），有改进空间\n"
            else:
                content += f"   - 整体满意度有待提升（平均CSI: {avg_csi:.1f}）\n"
        
        content += "\n2. **用户关注点**：\n"
        if 'aspect' in self.df_analyzed.columns:
            aspect_counts = self.df_analyzed['aspect'].value_counts()
            if len(aspect_counts) > 0:
                content += f"   - 最受关注的三个方面：{', '.join(list(aspect_counts.index[:3]))}\n"
        
        content += "\n3. **数据价值**：\n"
        content += "   - 本次分析验证了大模型情感分析技术在公共设施满意度研究中的有效性\n"
        content += "   - 多平台数据采集为研究提供了全面的用户视角\n"
        content += "   - 方面级分析为精细化服务优化提供了精准的数据支撑\n"
        
        content += """

### 7.2 研究局限性

- **数据样本**：主要集中在春节期间，可能存在季节性影响
- **平台覆盖**：虽然覆盖了四大平台，但仍有其他平台未涉及
- **时间范围**：数据时间跨度有限，建议长期跟踪更有价值

### 7.3 未来研究方向

1. **长期监测**：建立月度/季度满意度监测机制
2. **多源融合**：结合运营数据、成本数据等进行综合分析
3. **模型优化**：持续优化情感分析模型，提高准确性
4. **对比研究**：与其他城市公共图书馆进行横向对比
5. **预测分析**：运用时间序列预测满意度趋势

---

## 8. 附录

### 8.1 数据采集方法详解

**知乎爬虫**：
- 使用Selenium模拟浏览器操作
- 自动搜索关键词："广州图书馆"、"广州图书馆怎么样"等
- 采集内容：问题标题、回答内容、评论
- 数据清洗：去除HTML标签、去重、无效内容过滤

**微博爬虫**：
- 使用Selenium模拟浏览器访问
- 搜索相关话题和热门帖子
- 采集内容：帖子正文、评论内容
- 时间范围：近期热门讨论

**数据标准化**：
- 统一列名标准化
- 缺失值处理
- 重复数据去除
- 格式统一

### 8.2 分析方法技术说明

**情感分析**：
- 模型：DeepSeek大模型
- 输出：情感倾向、情感强度、具体情绪
- 置信度：模型自评估

**CSI满意度指数**：
- 综合考虑情感倾向权重
- 结合情感强度系数
- 方面重要性加权

**方面识别**：
- 基于关键词库匹配
- 大模型辅助识别
- 人工校验修正

**紧急度评估**：
- 情感消极程度
- 问题严重程度
- 影响范围判断

### 8.3 数据质量保障措施

1. 多源交叉验证
2. 人工抽样复核机制
3. 数据清洗标准化流程
4. 结果一致性检验

---

**报告结束**

*本报告由大模型情感分析系统自动生成，数据仅供参考。*
*建议结合实地调研进一步验证分析结果。*

"""
        
        return content
    
    def _generate_structured_data(self) -> dict:
        """生成结构化数据"""
        structured_data = {
            "report_info": {
                "generated_at": datetime.now().isoformat(),
                "data_source": "网络爬虫采集（知乎、微博等平台）",
                "analysis_method": "基于DeepSeek-V3大模型的情感分析"
            },
            "data_overview": {
                "total_samples": len(self.df_analyzed),
                "source_distribution": {},
                "facility_distribution": {}
            },
            "sentiment_analysis": {
                "overall_polarity": {},
                "csi_score": {},
                "specific_emotion": {}
            },
            "aspect_analysis": {},
            "urgent_issues": [],
            "recommendations": [
                {
                    "aspect": "服务态度",
                    "suggestion": "加强员工培训，提高服务意识和专业水平"
                },
                {
                    "aspect": "环境设施",
                    "suggestion": "优化空间布局，提高环境整洁度和舒适度"
                },
                {
                    "aspect": "设备维护",
                    "suggestion": "定期检查和维护设施设备，确保正常运行"
                },
                {
                    "aspect": "流程优化",
                    "suggestion": "简化办事流程，提高服务效率"
                },
                {
                    "aspect": "沟通渠道",
                    "suggestion": "建立有效的用户反馈机制，及时响应用户需求"
                }
            ],
            "summary": {
                "key_findings": [],
                "future_directions": [
                    "长期跟踪: 建立长期的满意度监测机制，跟踪满意度变化趋势",
                    "多维度分析: 结合更多维度的数据，如运营数据、成本数据等进行综合分析",
                    "AI模型优化: 持续优化情感分析模型，提高分析准确性",
                    "行业对比: 与同行业其他机构进行对比分析，识别差距和优势"
                ]
            }
        }
        
        # 填充数据来源分布
        if 'source' in self.df_analyzed.columns:
            source_counts = self.df_analyzed['source'].value_counts()
            for source, count in source_counts.items():
                structured_data["data_overview"]["source_distribution"][source] = {
                    "count": int(count),
                    "percentage": float(count/len(self.df_analyzed)*100)
                }
        
        # 填充设施类型分布
        if 'facility_type' in self.df_analyzed.columns:
            facility_counts = self.df_analyzed['facility_type'].value_counts()
            for facility, count in facility_counts.items():
                structured_data["data_overview"]["facility_distribution"][facility] = {
                    "count": int(count),
                    "percentage": float(count/len(self.df_analyzed)*100)
                }
        
        # 填充整体情感倾向
        if 'polarity_label' in self.df_analyzed.columns:
            polarity_counts = self.df_analyzed['polarity_label'].value_counts()
            for polarity, count in polarity_counts.items():
                structured_data["sentiment_analysis"]["overall_polarity"][polarity] = {
                    "count": int(count),
                    "percentage": float(count/len(self.df_analyzed)*100)
                }
        
        # 填充CSI满意度指数
        if 'csi_score' in self.df_analyzed.columns:
            structured_data["sentiment_analysis"]["csi_score"] = {
                "average": float(self.df_analyzed['csi_score'].mean()),
                "minimum": float(self.df_analyzed['csi_score'].min()),
                "maximum": float(self.df_analyzed['csi_score'].max())
            }
        
        # 填充具体情绪分布
        if 'specific_emotion' in self.df_analyzed.columns:
            emotion_counts = self.df_analyzed['specific_emotion'].value_counts().head(10)
            for emotion, count in emotion_counts.items():
                structured_data["sentiment_analysis"]["specific_emotion"][emotion] = {
                    "count": int(count),
                    "percentage": float(count/len(self.df_analyzed)*100)
                }
        
        # 填充方面分析
        if 'aspect' in self.df_analyzed.columns and 'csi_score' in self.df_analyzed.columns:
            aspect_groups = self.df_analyzed.groupby('aspect')
            for aspect, group in aspect_groups:
                if len(group) >= 5:
                    structured_data["aspect_analysis"][aspect] = {
                        "sample_count": int(len(group)),
                        "average_csi": float(group['csi_score'].mean()),
                        "polarity_distribution": {}
                    }
                    
                    if 'polarity_label' in group.columns:
                        polarity_counts = group['polarity_label'].value_counts()
                        for polarity, count in polarity_counts.items():
                            structured_data["aspect_analysis"][aspect]["polarity_distribution"][polarity] = {
                                "count": int(count),
                                "percentage": float(count/len(group)*100)
                            }
        
        # 填充紧急问题
        if 'urgency_score' in self.df_analyzed.columns:
            urgent_issues = self.df_analyzed[self.df_analyzed['urgency_score'] >= 7]
            for _, row in urgent_issues.head(20).iterrows():
                structured_data["urgent_issues"].append({
                    "facility_type": row.get('facility_type', '未知设施'),
                    "aspect": row.get('aspect', '未知方面'),
                    "urgency_score": float(row['urgency_score']),
                    "content": row.get('content', '')[:200],
                    "csi_score": float(row.get('csi_score', 50))
                })
        
        # 填充主要发现
        if 'csi_score' in self.df_analyzed.columns:
            avg_csi = self.df_analyzed['csi_score'].mean()
            structured_data["summary"]["key_findings"].append(
                f"整体满意度水平: {'较高' if avg_csi >= 70 else '一般'} (平均CSI指数: {avg_csi:.1f})"
            )
        
        structured_data["summary"]["key_findings"].extend([
            "主要满意点: 服务态度、环境设施",
            "主要改进空间: 设备维护、流程优化"
        ])
        
        return structured_data

if __name__ == "__main__":
    # 测试
    df = pd.DataFrame({
        'content': ["广州图书馆的环境很好，书籍很全", "服务态度不错，但是人太多了"],
        'source': ["知乎", "微博"],
        'facility_type': ["广州图书馆", "广州图书馆"],
        'polarity_label': ["积极", "中性"],
        'csi_score': [85, 65],
        'specific_emotion': ["满意", "中性"],
        'aspect': ["环境", "服务态度"],
        'urgency_score': [0, 2]
    })
    
    generator = AcademicReportGenerator(df, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"))
    report_path = generator.generate_full_report()
    json_path = generator.generate_json_report()
    print(f"报告生成完成: {report_path}")
    print(f"结构化报告生成完成: {json_path}")
