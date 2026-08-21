import asyncio
import json
import time
from typing import List, Dict
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

# ==========================================
# 1. 基础配置与 Pydantic 结构化数据定义
# ==========================================
VLLM_API_BASE = "http://localhost:8090/v1"  # 你的 vLLM 推理服务地址
VLLM_API_KEY = "my_secret_token_123"  # vLLM 默认无需 key
MODEL_NAME = "Qwen2.5-7B-Instruct"  # 替换为你部署的模型名称

client = AsyncOpenAI(base_url=VLLM_API_BASE, api_key=VLLM_API_KEY)


class SectionPlan(BaseModel):
    section_id: int = Field(description="章节序号")
    title: str = Field(description="章节标题")
    subsections: List[str] = Field(description="该章节包含的子要点列表")
    target_focus: str = Field(description="该章节的深度分析侧重点与目标")
    relevant_keywords: List[str] = Field(
        description="用于从原始长文本中筛选相关切片的关键词"
    )
    target_token_budget: int = Field(
        description="预估生成字数Token预算, 如1000-1500", default=1200
    )


class ReportOutline(BaseModel):
    report_title: str = Field(description="整篇报告的总标题")
    executive_summary_goal: str = Field(description="执行摘要的核心主旨")
    sections: List[SectionPlan] = Field(description="分章节规划列表")


# ==========================================
# 2. 模拟长文档与切片检索机制 (Context Slicing)
# ==========================================
# 在实际场景中, 这可以是 50 页 PDF 切分后的 List[DocumentChunk] 或向量库
MOCK_50_PAGE_CHUNKS = [
    {
        "chunk_id": 1,
        "text": "[第一部分: 宏观财务分析]公司2025年Q4营收增长28%, 净利润达4.2亿美元. 研发投入占比上升至18.5%, 主要集中在AI算力集群建设. 现金流稳健, 但应收账款周转天数拉长至65天...",
        "tags": ["财务", "营收", "利润", "现金流"],
    },
    {
        "chunk_id": 2,
        "text": "[第二部分: 核心业务线运营]智能云业务同比增长45%, 客户续约率92%. 边缘计算节点覆盖提升至120个城市. 硬件供应链受制于先进封装产能, 交付周期延长至16周...",
        "tags": ["业务", "智能云", "供应链", "交付"],
    },
    {
        "chunk_id": 3,
        "text": "[第三部分: 技术研发与战略架构]完成了下一代自研异构计算架构的流片, 能效比提升40%. 开源生态社区开发者突破50万人. 面临的技术风险主要是多模态算法的收敛稳定性...",
        "tags": ["技术", "研发", "算力架构", "算法"],
    },
    {
        "chunk_id": 4,
        "text": "[第四部分: 组织变革与风险管控]公司推进扁平化组织调整, 中台架构重组为三个独立业务单元. 合规与数据安全投入增加30%, 以满足全球各区域最新的数据出境法规要求...",
        "tags": ["组织", "合规", "数据安全", "风险"],
    },
]


def retrieve_relevant_context(keywords: List[str], chunks: List[Dict]) -> str:
    """根据关键词筛选相关上下文切片(在生产中可替换为 BM25 / Vector Rerank)"""
    matched_texts = []
    for chunk in chunks:
        # 只要包含任意关键词或标签命中即视为相关切片
        if any(
            kw.lower() in chunk["text"].lower() or kw in chunk["tags"]
            for kw in keywords
        ):
            matched_texts.append(chunk["text"])

    if not matched_texts:
        # 如果未严格命中, 回退到兜底前两个 chunk
        matched_texts = [c["text"] for c in chunks[:2]]
    return "\n\n".join(matched_texts)


# ==========================================
# 3. Stage 1: 规划阶段 (Generate Outline)
# ==========================================
async def stage1_generate_outline(
    full_document_summary: str, user_requirement: str
) -> ReportOutline:
    """
    第一阶段: 输入全局长文本/核心全貌, 生成结构化大纲
    消耗 tokens: 输入大, 输出极小 (~500 tokens)
    """
    print("\n🚀 [Stage 1] 正在启动全局规划 (Planning) , 生成深度报告大纲...")

    prompt = f"""你是一位顶尖的商业战略与技术分析专家.
请根据以下提供的文档全貌与用户要求, 制定一份深度分析报告的详细章节大纲.

[用户需求]: {user_requirement}
[文档全局全貌/摘要]:
{full_document_summary}

[输出要求]:
必须严格按照 JSON 格式输出, 不要包含 markdown 格式标记外的冗余内容.
格式参考结构:
{{
  "report_title": "...",
  "executive_summary_goal": "...",
  "sections": [
    {{
      "section_id": 1,
      "title": "...",
      "subsections": ["要点1", "要点2"],
      "target_focus": "深入分析...",
      "relevant_keywords": ["关键词1", "关键词2"],
      "target_token_budget": 1200
    }}
  ]
}}
"""
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a professional research director. Output pure JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},  # vLLM 支持 JSON Mode
    )

    raw_json = response.choices[0].message.content
    outline_data = json.loads(raw_json)
    outline = ReportOutline(outline_data)
    print(f"✅ [Stage 1] 大纲规划完成! 共规划 {len(outline.sections)} 个深度剖析章节.")
    return outline


# ==========================================
# 4. Stage 2: 执行阶段 (Parallel Section Execution)
# ==========================================
async def stage2_generate_single_section(
    outline: ReportOutline, section: SectionPlan, context_slice: str
) -> Dict[str, str]:
    """
    第二阶段子任务: 根据专属上下文切片, 详尽扩写单个章节
    消耗 tokens: 输入小 (~1.5K tokens), 输出极大 (~1.5K tokens)
    """
    print(f"  ✍️ [Stage 2] 开始并发撰写章节 [{section.section_id}]: {section.title}...")

    prompt = f"""你是一位顶级行业分析专家. 现在正在联合撰写一份题为《{outline.report_title}》的深度研究报告.
请你专门负责深入撰写第 {section.section_id} 章节.

[本章节标题]: {section.title}
[必须涵盖的子要点]: {', '.join(section.subsections)}
[写作深度要求与主旨]: {section.target_focus}
[预估字数/深度]: 请尽可能详尽、透彻展开论述, 结合数据与事实, 生成长篇深度分析(不少于 800 字).

[本章节专属参考资料]:
{context_slice}

[写作规则]:
1. 直接输出本章节正文(Markdown 格式, 使用二级标题 `##` 起始), 禁止输出前后客套话.
2. 论据必须严格基于所给资料, 论述逻辑严密.
"""
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are an exhaustive research report writer.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=section.target_token_budget,
    )

    section_content = response.choices[0].message.content
    print(
        f"  ✅ [Stage 2] 章节 [{section.section_id}]: {section.title} 撰写完成 (字数: {len(section_content)} 字)."
    )
    return {
        "section_id": section.section_id,
        "title": section.title,
        "content": section_content,
    }


# ==========================================
# 5. Stage 3: 聚合阶段 (Aggregation & Assembly)
# ==========================================
def stage3_aggregate_report(
    outline: ReportOutline, sections_results: List[Dict[str, str]]
) -> str:
    """
    第三阶段: 按大纲逻辑时序组装各独立章节
    """
    print("\n📦 [Stage 3] 正在组装完整深度报告...")

    # 按照 section_id 排序确保顺序正确
    sorted_sections = sorted(sections_results, key=lambda x: x["section_id"])

    final_report = []
    final_report.append(f"# {outline.report_title}\n")
    final_report.append(f"核心主旨: {outline.executive_summary_goal}\n")
    final_report.append("## 目录\n")
    for s in sorted_sections:
        final_report.append(
            f"- [{s['title']}](#{s['title'].replace(' ', '-').lower()})"
        )
    final_report.append("\n---\n")

    for s in sorted_sections:
        final_report.append(s["content"])
        final_report.append("\n\n")

    return "\n".join(final_report)


# ==========================================
# 6. 主执行管道 (Pipeline Coordinator)
# ==========================================
async def main():
    start_time = time.time()

    # 1. 模拟输入准备
    user_requirement = "请对这份 50 页年报进行全面深度的穿透性解读, 重点关注财务健康度、技术架构突破以及潜在风险, 输出一份详尽的长篇深度分析报告."
    # 模拟把全量文档拼接出的超长 Prompt(Stage 1 仅用它做整体规划)
    full_document_text = "\n".join([c["text"] for c in MOCK_50_PAGE_CHUNKS])

    # 2. 执行 Stage 1: 生成大纲规划
    outline = await stage1_generate_outline(
        full_document_summary=full_document_text, user_requirement=user_requirement
    )

    # 3. 执行 Stage 2: 并发调用 LLM 撰写各个章节 (独立上下文空间)
    print("\n⚡ [Stage 2] 启动多协程并发执行章节撰写...")
    tasks = []
    for section in outline.sections:
        # 为每个章节匹配专属上下文切片
        context_slice = retrieve_relevant_context(
            section.relevant_keywords, MOCK_50_PAGE_CHUNKS
        )
        # 创建并发任务
        task = stage2_generate_single_section(outline, section, context_slice)
        tasks.append(task)

    # 等待所有章节并发生成完毕
    sections_results = await asyncio.gather(*tasks)

    # 4. 执行 Stage 3: 聚合组装
    full_report = stage3_aggregate_report(outline, sections_results)

    # 5. 输出与统计
    elapsed = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"🎉 最终深度报告生成完成! 总耗时: {elapsed:.2f} 秒")
    print(f"📊 报告总字数: {len(full_report)} 字符")
    print("=" * 50 + "\n")
    print(full_report[:1200] + "\n\n...[后文省略]...")


if __name__ == "__main__":
    asyncio.run(main())


"""
$ python plan_and_execute_demo.py

🚀 [Stage 1] 正在启动全局规划 (Planning) , 生成深度报告大纲...
✅ [Stage 1] 大纲规划完成! 共规划 4 个深度剖析章节.

⚡ [Stage 2] 启动多协程并发执行章节撰写...
  ✍️ [Stage 2] 开始并发撰写章节 [1]: 宏观财务分析...
  ✍️ [Stage 2] 开始并发撰写章节 [2]: 核心业务线运营...
  ✍️ [Stage 2] 开始并发撰写章节 [3]: 技术研发与战略架构...
  ✍️ [Stage 2] 开始并发撰写章节 [4]: 组织变革与风险管控...
  ✅ [Stage 2] 章节 [1]: 宏观财务分析 撰写完成 (字数: 880 字).
  ✅ [Stage 2] 章节 [2]: 核心业务线运营 撰写完成 (字数: 1043 字).
  ✅ [Stage 2] 章节 [4]: 组织变革与风险管控 撰写完成 (字数: 1152 字).
  ✅ [Stage 2] 章节 [3]: 技术研发与战略架构 撰写完成 (字数: 1562 字).

📦 [Stage 3] 正在组装完整深度报告...

==================================================
🎉 最终深度报告生成完成! 总耗时: 39.91 秒
📊 报告总字数: 4824 字符
==================================================

# 2025年度公司年报深度分析报告

核心主旨: 全面解读公司2025年度年报, 重点分析财务健康度、技术架构突破及潜在风险.

## 目录

- [宏观财务分析](#宏观财务分析)
- [核心业务线运营](#核心业务线运营)
- [技术研发与战略架构](#技术研发与战略架构)
- [组织变革与风险管控](#组织变革与风险管控)

---

## 营收与净利润增长

根据最新财务数据, 公司在2025年第四季度实现了显著的增长. 具体来看, 公司的营收同比增长了28%, 这表明市场需求持续增长, 同时公司的市场份额也在扩大. 这一增长趋势延续了过去几个季度的表现, 显示了公司在市场中的强劲竞争力和良好的业务扩展能力.

净利润方面, 公司取得了4.2亿美元的成绩, 显示出公司在盈利方面的稳健表现. 净利润的增长速度略低于营收增长速度, 这可能反映了公司在扩大业务规模的同时, 也在积极进行成本控制和优化运营效率. 从整体上看, 公司的净利润率保持在一个相对稳定的水平, 表明公司在盈利方面具有较强的可持续性.

## 研发投入与资本支出

研发投入是衡量公司创新能力的重要指标. 2025年, 公司研发投入占总营收的比例达到了18.5%, 较上一年度有所提升. 这一增长主要体现在对公司AI算力集群建设的投资上. 随着人工智能技术的快速发展及其在各行业的广泛应用, 加大对AI领域的投资已成为众多科技企业的共识. 公司在这方面的高投入不仅有助于巩固其在技术前沿的地位, 还能促进产品和服务的创新, 从而进一步增强市场竞争力.

资本支出方面, 公司继续增加对研发设施和技术升级的投资. 这些支出不仅支持了现有产品的改进和完善, 也为未来新产品和新技术的研发奠定了基础. 合理的资本支出规划有助于确保公司在未来的市场竞争中保持领先地位.

## 现金流状况

公司在现金流管理方面表现出色. 尽管整体现金流保持稳健, 但在应收账款周转天数方面出现了变化. 数据显示, 应收账款周转天数延长至65天, 相比以往有所增加. 这一现象可能反映了公司在扩大销售规模的过程中, 需要更长的时间来回收客户欠款. 虽然短期内可能会影响公司的现金流状况, 但从长期来看, 通过优化信用政策和加强客户管理, 可以有效改善这一情况. 此外, 公司应加强对逾期账款的监控和催收力度, 以减少坏账风险, 确保现金流的安全性和稳定性.

综上所述, 公司在2025年的财务表现显示出强劲的增长势头和良好的盈利能力. 通过合理分配资源, 加大研发投入, 并持续优化现金流管理策略, 公司有望在未来继续保持健康的发展态势.



## 智能云业务表现

智能云业务作为公司的核心业务之一, 在2024年实现了显著的增长. 根据最新的财务数据显示, 该业务线同比增长了45%, 这不仅反映了市场需求的增长, 也体现了公司在技术和服务方面的持续优化. 这一增长速度远超行业平均水平, 显示出了公司在智能云领域的强劲竞争力.

从客户层面

...[后文省略]...
$
"""
