# 系统设计面试：设计一个 RAG 系统

> **这份材料的来源与可信度**
>
> - 我先搜索了“设计 RAG 系统”的面试备考内容和企业 RAG 权限过滤的做法：[DesignGurus：System Design for RAG](https://www.designgurus.io/blog/system-design-for-rag)、[PracHub：Designing RAG Architecture at Scale](https://prachub.com/resources/designing-rag-architecture-at-scale-an-ai-engineering-interview-guide)、[RAG System Walkthrough](https://calm-rocks.pages.dev/resources/prepare-interview/system-design/rag-system-walkthrough/)、[Design RAG Architecture](https://ailswan.github.io/poststwo/ai-a02-2026-05-25/)、[wavect：RAG 权限（SharePoint、Confluence、Drive）](https://wavect.io/blog/rag-permissions-sharepoint-confluence-drive/)、[DEV：你的 AI 助手可能泄露用户无权查看的文件](https://dev.to/lakhansamani/your-ai-assistant-can-leak-files-people-arent-allowed-to-see-heres-how-to-fix-it-51en)。**这些多是博客和备考站，不是公司官方的面试标准，也没有可核实的“某公司某年真题”**。我只用它们确认面试官通常期待的深度（切块、元数据、权限、混合检索、重排序、上下文预算、引用、降级、可观测性、评估），以及常见的追问方向。
> - **四个实验都在这个环境里真实运行过**（Python 3，hnswlib 与 faiss）。但要注意它们各自的性质：容量估算（实验 1）是公式计算，参数是我设的假设；ANN 与权限过滤（实验 2、3）用的是**合成向量**，不是真实文本嵌入，所以**绝对数字不能照搬，只看趋势**；尾延迟（实验 4）是模拟。
> - 工具和产品的具体行为（各向量数据库的功能、云服务限额、模型价格）会变，我只写通用的取舍，**没有写具体厂商的价格或基准**；需要时请对照官方文档。
> - 搜索结果里有某个博主给的评估阈值（例如 faithfulness 大于 0.9），那是**单个从业者的目标值，不是行业标准**，我没有把它当作标准引用。
> - 这份材料是**系统设计面试**角度的，重点是“怎么讲、怎么取舍”。RAG 的原理与手写实验（BM25、RRF、LoRA 显存等）在之前给你的《AI 应用工程六大主题》里，这里不重复。
> - 术语在每个小节第一次出现时附英文原名，附录有中英术语表。

## 零、先看这一页：面试官其实在看什么

"设计一个 RAG 系统"是个很开放的题目。大多数候选人的回答是：“文档切块（chunking）、做嵌入（embedding）、放进向量数据库（vector database）、检索（retrieval） top-k、塞给大模型”。**这是 RAG 的定义，不是设计。** 面试官（据备考站的共同说法）期待你谈到的是：

1. **先澄清需求**：数据规模、更新频率、用户量、延迟目标、是否要引用（citation）来源、有没有权限隔离、错了的代价有多大。
2. **把它当成两条管线**：离线的摄入（ingestion）管线和在线的查询（query）管线，加上贯穿的评估与监控。
3. **有质量意识**：怎么知道检索对不对？怎么知道答案没有编造？怎么发现退化？
4. **有权限意识**：企业数据有访问控制（access control），**检索阶段就要过滤**，不能等生成之后。
5. **会做取舍**：召回与延迟、精度与成本、新鲜度与一致性（consistency）、简单与可扩展。
6. **会讲失败**：检索不到时怎么办？下游超时怎么办？文档被删除后怎么办？

**一个好答案的节奏**（45 分钟的参考分配）：

| 阶段 | 时间 | 要做的事 |
|---|---|---|
| 澄清需求 | 5 分钟 | 问第一部分表里的问题，写下功能与非功能需求 |
| 估算 | 3–5 分钟 | 语料大小、块数、向量内存、QPS、LLM 成本（第二部分） |
| 高层架构 | 8–10 分钟 | 画出摄入与查询两条管线，说明每个组件职责 |
| 深入 2 到 3 个点 | 15–20 分钟 | 选面试官感兴趣的：切块、混合检索（hybrid search）与重排序（reranking）、权限、规模、评估 |
| 可靠性、安全、监控、成本 | 5 分钟 | 降级、权限、提示注入（prompt injection）、可观测性（observability） |
| 总结与风险 | 2 分钟 | 回顾设计、说明还有哪些风险与后续迭代 |

---

## 一、面试开场：要问的澄清问题（以及为什么问）

不要一上来就画图。先问下面这些问题，**每一个问题都会改变设计**：

| 问题 | 为什么问（会改变什么设计） |
|---|---|
| 这是给谁用的？员工内部、客户、公众？ | 决定权限模型、可用性要求、对错误的容忍度（tolerance） |
| 数据在哪里？格式是什么？（Confluence、Google Drive、PDF、工单（ticket）、代码、数据库、网页） | 决定连接器（connector）与解析的复杂度（PDF 表格、扫描件、图片最难） |
| 数据规模？（文档数、总 token、增长速度） | 决定向量索引形态：单机内存、分片（sharding）、磁盘索引、量化（quantization） |
| 更新频率与新鲜度要求？（分钟级、小时级、天级） | 决定增量同步（incremental sync）、流式（streaming）摄入（ingestion）还是批处理，以及索引更新策略 |
| 用户数与查询量？峰值 QPS？ | 通常 QPS 并不高，瓶颈在 LLM；这决定是否需要缓存（cache）与队列 |
| 延迟目标？（首个 token、完整答案） | 决定能否做查询改写（query rewriting）、重排序（reranking）、多轮检索；是否要流式输出 |
| 有没有访问控制（access control）？同一份内容不同人能看到不同部分吗？ | **权限过滤（permission filtering）是最容易被忽略也最致命的部分** |
| 答案必须带引用（citation）吗？错了会有什么后果？（法律、医疗 vs 内部闲聊） | 决定是否强制引用、拒答（refusal）阈值、人工复核 |
| 问题类型？（事实查找、总结、对比、多文档推理、对话式追问） | 决定是否需要多跳检索（multi-hop）、代理式 RAG（agentic RAG）、对话记忆（memory） |
| 语言？（单语言还是多语言） | 决定嵌入（embedding）模型与分词（tokenization）、是否需要翻译 |
| 多租户（multi-tenancy）吗？数据能否混放？ | 决定索引隔离方式、加密、成本分摊 |
| 有没有合规（compliance）要求？（数据驻留（data residency）、审计（audit）、PII、删除权） | 决定部署位置、日志、删除传播 |
| 成功怎么衡量？（解决率、采纳率、省下的人工时间） | 决定评估指标（metrics）与上线门槛 |
| 现有技术栈与团队规模？ | 决定选型：自建还是托管，是否用现有的数据库/搜索引擎 |

**写下需求的方法**：把问出来的内容整理成两栏——功能需求（Functional）与非功能需求（Non-functional：延迟、可用性、规模、新鲜度、安全、成本、质量）。后面的每个设计决定都回头对照这张表说明理由。

**如果面试官说“你自己定”**：说出你的假设并写下来，例如“我假设这是一个企业内部知识助手，500 万篇文档，5 万名员工，有访问控制，需要引用来源，首个 token 两秒内出现。如果实际不同请告诉我”。这样既推进了讨论，也展示了你的判断。

---

## 二、规模估算

### 2.1 为什么要估算

估算不是为了算对，而是为了**判断瓶颈在哪里**。RAG 系统的结论经常反直觉：**检索（retrieval）的 QPS 很低，真正的瓶颈是 LLM 的延迟与成本；而向量索引的内存占用决定了单机放不放得下。**

### 2.2 实验 1：把估算写成代码

下面的脚本把常用公式写出来，参数是我设的假设（企业知识助手：500 万篇文档，每篇约 3000 token，5 万名员工）。面试时你可以用这些公式现场计算，替换面试官给的数字。

```python
"""实验 1：RAG 系统的容量估算器（纯 Python）。
设计面试里要现场做数量级估算。这里把常用公式写成代码，参数全部是**假设**，请按面试官给的数字替换。
场景：企业内部知识助手（我设定的参考场景，不是真实公司的数据）。
"""
GB = 1e9

# ---- 假设（可改）----
docs = 5_000_000            # 文档数
tokens_per_doc = 3_000      # 平均每篇约 3000 token（约 6 页）
chunk_tokens = 512          # 切块大小
overlap_tokens = 64         # 相邻块重叠
dim = 1024                  # 嵌入维度
users = 50_000              # 员工总数
dau_ratio = 0.30            # 日活比例
queries_per_active_user = 8
peak_factor = 5             # 峰值 QPS = 平均 QPS × 峰值系数
top_k_retrieve = 100        # 向量/关键词各召回多少
top_k_rerank = 50           # 送去重排的数量
top_k_context = 6           # 最终放进提示词的块数
prompt_overhead_tokens = 600  # 系统提示 + 指令 + 历史摘要
answer_tokens = 400
hnsw_M = 16                 # HNSW 每个节点的出边数（近似）

# ---- 语料规模 ----
total_tokens = docs * tokens_per_doc
stride = chunk_tokens - overlap_tokens
chunks = int(total_tokens / stride)
print(f"语料：{docs/1e6:.0f}M 篇 × {tokens_per_doc} token = {total_tokens/1e9:.1f}B token")
print(f"切块：{chunk_tokens} token/块，重叠 {overlap_tokens} -> 步长 {stride} -> 约 {chunks/1e6:.1f}M 个块（重叠使块数增加 {(chunk_tokens/stride-1)*100:.0f}%）")

# ---- 存储 ----
def vec_bytes(bytes_per_dim): return chunks * dim * bytes_per_dim
graph_bytes = chunks * hnsw_M * 2 * 4      # 每节点约 2M 条出边（底层），每条 4 字节编号（粗略）
print("\n向量存储（只算向量本身）：")
for name, b in (("float32", 4), ("float16", 2), ("int8 标量量化", 1), ("乘积量化 PQ(约 64 字节/向量)", 64 / dim)):
    print(f"  {name:<24} {vec_bytes(b)/GB:8.1f} GB")
print(f"HNSW 图结构（粗估）        {graph_bytes/GB:8.1f} GB")
text_bytes = total_tokens * 4              # 约 4 字节/token 的原文
print(f"原文块文本（约 4 字节/token） {text_bytes/GB:8.1f} GB（放对象存储或文档库，不放内存）")
print(f"元数据（每块约 300 字节）     {chunks*300/GB:8.1f} GB")
mem_f32 = (vec_bytes(4) + graph_bytes) / GB
mem_i8 = (vec_bytes(1) + graph_bytes) / GB
print(f"\n全部放内存的热索引：float32 约 {mem_f32:.0f} GB；int8 约 {mem_i8:.0f} GB（再加副本数和 2 倍重建余量）")
print("  -> 单机放不下就分片；或用 磁盘型索引 + 内存里放量化向量；或按租户/部门拆索引。")

# ---- 摄入（嵌入）----
embed_tokens_per_sec = 200_000   # 假设：一台 GPU 嵌入服务的吞吐，实际差别很大，要实测
hours = total_tokens * (chunk_tokens / stride) / embed_tokens_per_sec / 3600
print(f"\n首次全量嵌入：{total_tokens*(chunk_tokens/stride)/1e9:.1f}B token（含重叠），按 {embed_tokens_per_sec:,} token/s/GPU 约 {hours:.0f} GPU 小时")
print(f"  用 8 张 GPU 并行约 {hours/8:.0f} 小时。换嵌入模型或改切块方式就要重做一次（所以这两个决定要慎重）。")
daily_change = 0.01
print(f"  每日变更 {daily_change*100:.0f}% 的文档 -> 每天重嵌约 {total_tokens*daily_change*(chunk_tokens/stride)/1e9:.2f}B token，增量完全跑得动")

# ---- 查询流量 ----
dau = users * dau_ratio
qpd = dau * queries_per_active_user
avg_qps = qpd / 86400
peak_qps = avg_qps * peak_factor
print(f"\n流量：日活 {dau:,.0f}，每天 {qpd:,.0f} 次提问 -> 平均 {avg_qps:.1f} QPS，峰值约 {peak_qps:.0f} QPS（峰值系数 {peak_factor}）")
print("  结论：对检索系统来说 QPS 很低；瓶颈在 LLM 生成（延迟高、成本高、并发受限），不是向量检索。")

# ---- LLM token ----
ctx_tokens = top_k_context * chunk_tokens
in_tokens = prompt_overhead_tokens + ctx_tokens
print(f"\n每次提问：输入 {in_tokens:,} token（提示 {prompt_overhead_tokens} + 上下文 {top_k_context}×{chunk_tokens}={ctx_tokens}），输出约 {answer_tokens} token")
print(f"  每天输入 {qpd*in_tokens/1e9:.2f}B token，输出 {qpd*answer_tokens/1e6:.0f}M token")
conc = peak_qps * 6
print(f"  峰值并发的生成请求数 ≈ 峰值 QPS × 平均生成时长（假设 6 秒）= {conc:.0f}")
print("  上下文只放 top-6 而不是 top-100：输入 token 是成本和延迟的主要来源，召回要宽、送模型要窄。")

# ---- 延迟预算 ----
print("\n延迟预算（目标：首个 token 在 2 秒内出现；这些数字是假设，要按实测调整）：")
budget = [("鉴权 + 查询改写（小模型/规则）", 150), ("向量检索 + 关键词检索（并行）", 80), ("融合 + 权限过滤", 10), ("重排序（对 50 个候选打分）", 250), ("构造提示词", 20), ("LLM 首个 token", 900)]
tot = 0
for name, ms in budget:
    tot += ms; print(f"  {name:<34} {ms:>5} ms   累计 {tot:>5} ms")
print(f"  之后流式输出：{answer_tokens} token 按 50 token/s 约 {answer_tokens/50:.0f} 秒；用流式让用户先看到前几个字。")

# ---- 重排序算力 ----
rerank_pairs_per_sec = peak_qps * top_k_rerank
print(f"\n重排序：峰值每秒 {rerank_pairs_per_sec:,.0f} 对（查询,块）要打分 -> 这是交叉编码器的主要算力需求；缩小候选数是最直接的降本手段")
```

运行结果：

```text
语料：5M 篇 × 3000 token = 15.0B token
切块：512 token/块，重叠 64 -> 步长 448 -> 约 33.5M 个块（重叠使块数增加 14%）

向量存储（只算向量本身）：
  float32                     137.1 GB
  float16                      68.6 GB
  int8 标量量化                    34.3 GB
  乘积量化 PQ(约 64 字节/向量)           2.1 GB
HNSW 图结构（粗估）             4.3 GB
原文块文本（约 4 字节/token）     60.0 GB（放对象存储或文档库，不放内存）
元数据（每块约 300 字节）         10.0 GB

全部放内存的热索引：float32 约 141 GB；int8 约 39 GB（再加副本数和 2 倍重建余量）
  -> 单机放不下就分片；或用 磁盘型索引 + 内存里放量化向量；或按租户/部门拆索引。

首次全量嵌入：17.1B token（含重叠），按 200,000 token/s/GPU 约 24 GPU 小时
  用 8 张 GPU 并行约 3 小时。换嵌入模型或改切块方式就要重做一次（所以这两个决定要慎重）。
  每日变更 1% 的文档 -> 每天重嵌约 0.17B token，增量完全跑得动

流量：日活 15,000，每天 120,000 次提问 -> 平均 1.4 QPS，峰值约 7 QPS（峰值系数 5）
  结论：对检索系统来说 QPS 很低；瓶颈在 LLM 生成（延迟高、成本高、并发受限），不是向量检索。

每次提问：输入 3,672 token（提示 600 + 上下文 6×512=3072），输出约 400 token
  每天输入 0.44B token，输出 48M token
  峰值并发的生成请求数 ≈ 峰值 QPS × 平均生成时长（假设 6 秒）= 42
  上下文只放 top-6 而不是 top-100：输入 token 是成本和延迟的主要来源，召回要宽、送模型要窄。

延迟预算（目标：首个 token 在 2 秒内出现；这些数字是假设，要按实测调整）：
  鉴权 + 查询改写（小模型/规则）                    150 ms   累计   150 ms
  向量检索 + 关键词检索（并行）                      80 ms   累计   230 ms
  融合 + 权限过滤                             10 ms   累计   240 ms
  重排序（对 50 个候选打分）                      250 ms   累计   490 ms
  构造提示词                                 20 ms   累计   510 ms
  LLM 首个 token                         900 ms   累计  1410 ms
  之后流式输出：400 token 按 50 token/s 约 8 秒；用流式让用户先看到前几个字。

重排序：峰值每秒 347 对（查询,块）要打分 -> 这是交叉编码器的主要算力需求；缩小候选数是最直接的降本手段
```

### 2.3 怎么读这些数字（面试里要说的结论）

1. **块数**：**150 亿 token → 约 3350 万个块**。重叠 64 token 让块数多了约 14%。
2. **向量内存**：1024 维 float32 约 137 GB；int8 标量量化（quantization）约 34 GB（4 倍压缩）；乘积量化可以压到几 GB。加上 HNSW 图结构的几 GB。**结论：这个规模单台大内存机器勉强放得下 int8 版本；float32 就要分片（sharding），或者用磁盘型索引。** 别忘了副本（replica）和重建索引的余量。
3. **原文放哪里**：块文本约 60 GB，不要放在内存里的向量索引中，放对象存储（object storage）或文档库，检索（retrieval）后按 ID 取回。
4. **摄入（ingestion）**：首次全量嵌入（embedding）约 170 亿 token。吞吐是我设的假设（每 GPU 每秒 20 万 token），**要实测**，但能得出量级：几十个 GPU 小时，8 张卡几小时。每天 1% 的文档变化，增量完全跑得动。**这也说明换嵌入模型或改切块（chunking）方式的代价是“整库重来”，所以要慎重。**
5. **流量**：1.4 QPS 平均，峰值约 7 QPS。对检索系统来说几乎是零。**不需要为了 QPS 去分片向量库**，分片是为了内存，不是为了吞吐。
6. **LLM 成本**：每次提问输入约 3700 token（上下文 6 块 × 512），输出约 400；每天约 4.4 亿输入 token。**召回要宽（top-100），送给模型要窄（top-6）**：输入 token 是成本和延迟的主要来源。
7. **延迟预算（budget）**：首个 token 2 秒内；查询改写（query rewriting）、检索、重排序（reranking）合计不到 0.5 秒，留给 LLM 首个 token 约 1 秒；之后靠流式（streaming）输出让用户尽早看到内容。**每增加一个阶段（改写、重排序、多轮检索），都要问它值不值得那几百毫秒。**
8. **重排序算力**：交叉编码器（cross-encoder）对每个（查询,块）对打分，峰值每秒几百对，不大；**候选数是最直接的降本手段**。

> **估算的小提示**：单位最容易出错（百万、十亿、字节、比特）。说数字时同时说单位，并用“每块 512 token、每向量 4 KB”这样的小数字倒推大数字，面试官能跟上你的推导。

---

## 三、总体架构

### 3.1 两条管线 + 一个评估闭环

```text
              ┌────────────────────────── 离线 / 近线：摄入管线 ──────────────────────────┐
 数据源       │                                                                            │
 Confluence ─►│ 连接器 ─► 解析 ─► 清洗/去重 ─► 切块 ─► 嵌入 ─► 写入索引 (向量 + 关键词)    │
 Drive      ─►│ (认证,增量,   (PDF/HTML/    (版本,哈希)  (结构感知,  (批量,    + 元数据存储     │
 Jira/工单  ─►│  变更通知,     表格/OCR)               父子块)    模型版本)   (来源,ACL,时间)  │
 代码仓库   ─►│  删除传播)                                                                  │
              └─────────────────────────────────┬──────────────────────────────────────────┘
                                                │ 索引
              ┌─────────────────────────────────▼──────────────────────────────────────────┐
              │                           在线：查询管线                                    │
 用户 ─► 网关 ─► 鉴权(身份+群组) ─► 查询理解 ─► 混合检索 ─► 融合 ─► 权限校验 ─► 重排序     │
        (限流)                      (改写,拆分,   (向量 +    (RRF)   (再确认)   (交叉编码器)  │
                                     路由)         关键词)                                  │
                  ─► 上下文构造 ─► LLM 生成 ─► 引用校验/护栏 ─► 流式返回 ─► 日志与反馈         │
                     (预算,去重,     (提示词,     (引用存在?     │                           │
                      排序)          拒答规则)     注入过滤)      │                           │
              └────────────────────────────────────────────────┼───────────────────────────┘
                                                               ▼
              ┌──────────────────────────── 评估与监控闭环 ─────────────────────────────────┐
              │ 离线评测集 (检索/生成) ─► 回归门禁 ─► 线上指标 (采纳率,引用点击,拒答率,延迟) │
              │ 失败样本回流 ─► 改进切块/检索/提示词 ─► 再评测                                │
              └──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 每个组件做什么（一句话版，面试时按这个顺序讲）

| 组件 | 职责 | 关键设计点 |
|---|---|---|
| 连接器（connector） | 从各数据源拉取内容与权限 | 认证（authentication）、增量同步（incremental sync）、变更通知（webhook）、限速、删除传播 |
| 解析器 | 把 PDF/HTML/Office/图片变成结构化文本 | 保留标题层级与表格；扫描件用 OCR；这是质量的第一道关 |
| 切块（chunking）器 | 把文档切成可检索（retrieval）单元 | 结构感知、块大小与重叠、父子块（parent-child chunks）、保留来源位置 |
| 嵌入（embedding）服务 | 把文本变成向量 | 模型选择、批处理、版本号（version number）、限流（rate limiting）与重试（retry） |
| 索引 | 向量索引 + 关键词索引 + 元数据（metadata） | ANN、混合检索（hybrid search）、过滤能力、更新与删除 |
| 元数据/权限存储 | 来源、时间、ACL | ACL 与内容分开同步，更新频率不同 |
| 查询理解 | 改写、拆分、路由（routing） | 结合对话历史、缩写展开、多问题拆分 |
| 检索与融合 | 召回候选 | 向量 + 关键词并行，RRF 融合 |
| 重排序（reranking）器 | 精排 | 交叉编码器（cross-encoder），控制候选数 |
| 上下文构造 | 决定哪些块进入提示词（prompt） | token 预算（budget）、去重（deduplication）、排序、附来源标记 |
| 生成 | 基于上下文回答 | 提示词约束、引用（citation）、拒答（refusal）、流式（streaming） |
| 护栏（guardrails） | 校验输出 | 引用有效性、敏感信息、注入防护 |
| 评估与监控 | 度量质量与健康 | 离线评测（offline evaluation）集、线上指标（metrics）、全链路追踪（trace） |

### 3.3 一个常用的口头开场（英文）

> “I’ll treat this as two pipelines plus an evaluation loop. An **ingestion pipeline** brings documents in, parses and chunks them, embeds them, and writes both vectors and metadata, including permissions, into an index. A **query pipeline** authenticates the user, rewrites the query, runs hybrid retrieval with permission filtering, reranks, builds a bounded context, and generates a cited answer. Around both, I’d build **evaluation and monitoring**, because retrieval quality is the thing that silently degrades. Before I go deeper, may I confirm the scale, freshness requirements, and whether we have access control?”

---

## 四、摄入管线：数据质量决定上限

### 4.1 为什么摄入最重要

RAG 有一句老话：“垃圾进，垃圾出。” 更准确地说：**检索（retrieval）只能找到你放进去的东西，而模型只能基于你给它的上下文回答。** 解析错了（表格被打乱）、切块（chunking）切断了关键信息、权限没带上，后面再好的模型都救不了。

### 4.2 连接器与解析

- **连接器（connector）**：每个数据源一个连接器，处理认证（OAuth、服务账号（ServiceAccount））、分页（pagination）、限速、增量同步（incremental sync，变更令牌、webhook、基于修改时间的轮询）。**同时同步内容和权限。**
- **解析**：HTML 去掉导航与广告；Office/Markdown 保留标题层级；PDF 最难——多栏、页眉页脚、表格、图表；扫描件需要 OCR。**表格要转成保留结构的文本（如 Markdown 表格或“行=记录”的描述），不要打平成一行字。** 图片和图表可用视觉模型生成描述（成本较高，按需）。
- **清洗与去重（deduplication）**：去掉重复内容（同一文档多个版本、转发邮件）；用内容哈希判断是否变化（没变化就不用重新嵌入（embedding））。
- **每个块保留的元数据（metadata）**：文档 ID、版本、来源链接、标题路径（章节层级）、页码或位置、更新时间、作者、语言、ACL。**引用（citation）、权限、过滤、删除、调试都靠这些元数据。**

### 4.3 切块（chunking）：最难回头的决定

**为什么难回头**：块大小和切法决定了向量的内容。改了之后整个语料要重新嵌入（embedding）（实验 1 估算是几十个 GPU 小时，再加上评估和灰度（canary release）切换）。所以要在小规模上先实验、先建评测集（evaluation set），再定。

**权衡**：
- **块太小**：检索精度高，但丢失上下文（“它”指什么？表头在哪？），一个答案分散在多个块里。
- **块太大**：包含更多上下文，但相关信息被稀释，向量变得“泛”，占用提示词（prompt）预算（budget）。

**常见策略（从简单到复杂）**：

1. **固定大小 + 重叠**：例如 512 token，重叠 10% 到 15%。最简单，作为基线。缺点：会切断句子、表格、代码块。
2. **递归/结构感知切块（chunking）**：优先按标题、段落、列表、代码块边界切，超长再按句子切。**多数场景的好起点。**
3. **语义切块**：按语义相似度的变化找边界。成本高，收益在不同数据集上证据不一，要用评测集验证。
4. **父子块（small-to-big / parent-child）**：用小块（如 128 到 256 token）做检索以提高精度，命中后返回它所在的大块（父块，如整个小节）给模型以保留上下文。**这是在精度与上下文之间折中的常用办法。**
5. **给每个块补上下文（contextual retrieval）**：嵌入前在块前面加一句“这个块来自哪个文档的哪一节，讲什么”（可由 LLM 生成）。Anthropic 提出过这类做法并报告能降低检索失败率；**具体百分比我没有核对**，面试时只说思路和代价（摄入（ingestion）时多一次 LLM 调用）。
6. **文档级摘要 + 块级索引（两级检索）**：先找文档，再在文档内找块；适合长文档或文档很多的场景。

**必须说出的细节**：
- 每个块带上**标题路径**，检索结果展示和引用（citation）时用。
- 表格、代码按整体切，不要从中间断开。
- 切块参数**版本化**（chunker 版本号（version number）写进元数据（metadata）），否则无法知道某个块是怎么产生的。
- **用评测集选参数**，不要凭感觉：同一评测集上比较 256/512/1024 和不同重叠，看 recall@k 和最终答案质量。

### 4.4 嵌入（embedding）

- **选模型看**：任务效果（在你自己的数据上评估，榜单只作参考）、维度（影响内存）、最大输入长度、多语言、速度与成本、能否自托管（数据驻留（data residency））。**维度越高不一定越好；有些模型支持截断到更低维度（Matryoshka 式），能省内存，效果需自己验证。**
- **查询和文档可能用不同前缀/指令**（部分模型要求）；用错会明显掉点。
- **模型版本写进元数据（metadata）**。**不同模型的向量空间互不兼容**：换模型必须全部重嵌；不能新旧向量混在一个索引里比较。
- **批处理与限流（rate limiting）**：嵌入（embedding）服务要有队列、批大小优化、重试（retry）与退避（backoff）、失败隔离（一个坏文档不能卡住整个批次）。
- **领域适配**：通用嵌入在专业术语多的领域可能不够；可以微调（fine-tuning）嵌入模型（需要成对的查询-文档数据），或加强关键词检索（retrieval）。先用混合检索（hybrid search） + 重排序（reranking）解决，别急着微调。

### 4.5 更新、删除与重建

- **增量更新**：文档变化时，用文档 ID + 内容哈希找出变化；**更新时替换该文档的所有块**（先写新版本，再删旧版本，避免出现“查不到”的空窗）。
- **删除传播**：源系统删除/撤销权限，索引必须及时反映。HNSW 类索引通常只能“标记删除”（墓碑（tombstone）），需要定期压缩/重建；要有“删除后多久不可再被检索（retrieval）到”的明确指标（SLA）。**合规（compliance）场景（删除权）这是硬要求。**
- **权限变化比内容变化更频繁**：把 ACL 作为独立的、可快速更新的元数据（metadata），而不要和内容一起重嵌（见第六部分）。
- **重建索引（换嵌入（embedding）模型、改切块（chunking））**：**蓝绿（blue-green）方式**：新建一份新索引在后台全量构建，评测（evaluation, or evals）通过后用别名（alias）原子切换，旧索引保留一段时间用于回滚（rollback）。构建期间的增量变更要双写或回放（replay）。
- **一致性（consistency）模型**：新增文档到可被检索的延迟（“摄入（ingestion）延迟”）要说清楚（分钟级？），以及用户是否能接受“刚更新的文档暂时搜不到”。

### 4.6 向量数据库选型

**不要先选产品，先说选择标准：**

| 标准 | 说明 |
|---|---|
| 规模 | 几百万块以内，许多通用数据库的向量扩展就够；上亿块要看分片（sharding）与磁盘索引能力 |
| 过滤能力 | **权限和元数据（metadata）过滤是否在检索（retrieval）过程中生效**（见实验 3）；过滤很严格时是否仍能返回足够结果 |
| 混合检索（hybrid search） | 是否同时支持关键词（BM25）和向量，是否能在一次查询里融合 |
| 更新与删除 | 增量写入、删除、重建的代价；一致性（consistency） |
| 运维 | 托管还是自建；团队是否熟悉；备份与高可用 |
| 现有栈 | 已经在用 PostgreSQL 或 OpenSearch/Elasticsearch，复用它们的向量功能能少一套系统 |
| 成本 | 内存占用（是否支持量化（quantization）、磁盘索引）、副本（replica）数 |
| 数据位置 | 合规（compliance）与驻留 |

**常见选择路径（我的判断，不是权威结论）**：
- 规模不大（百万级块）、已有 PostgreSQL → 用向量扩展（如 pgvector）**最省事**，事务（transaction）与权限和业务数据放一起，运维简单。
- 需要强大的关键词 + 向量混合检索与过滤，已有搜索基础设施 → OpenSearch/Elasticsearch 一类。
- 规模大、要求低延迟、希望少运维 → 专用向量数据库（vector database，托管或自建），选型时重点验证过滤性能与成本。
- 无论选哪个：**把向量库当作可替换的组件**——数据（块、元数据）以你自己的存储为准，索引可以随时重建。这是降低风险的关键。



---

## 五、检索：召回、融合与重排序

### 5.1 检索的目标

检索（retrieval）阶段的目标是：**让真正相关的块出现在送给模型的那 5 到 10 个块里。** 它是整个系统的天花板：检索没找到，生成再强也只能编造或拒答（refusal）。所以通常采用**两阶段**：先“宽召回”（高召回率（recall），便宜），再“精排”（高精度，贵）。

### 5.2 为什么只用向量检索不够：混合检索

- **向量（dense）检索（retrieval）**擅长语义相似：“如何报销差旅” 能匹配 “出差费用申报流程”。弱点：对**精确标识符、型号、缩写、人名、错误码**不敏感（嵌入（embedding）把它们当成普通词，容易找到“语义相近但不是它”的内容）。
- **关键词（BM25 等 sparse）检索**擅长精确匹配和稀有词。弱点：不懂同义改写。
- **混合检索（hybrid search）**：两路并行召回，再融合。最常用的融合方法是 **RRF（reciprocal rank fusion，倒数排名融合）**：每个结果的得分是各路排名的 `1/(k+rank)` 之和（k 常取 60）。优点：不需要把两种不同量纲的分数归一化，简单稳健。
- 之前给你的《AI 应用工程六大主题》里有一个可运行的玩具实验（`rag_hybrid_toy.py`）：标识符/稀有词查询上 BM25 完胜，同义改写查询上稠密检索（dense retrieval）完胜，RRF 融合两者都好。这里就不重复了。

### 5.3 近似最近邻（ANN）索引：召回、速度与内存的三角

向量检索（vector search）在大规模下不能暴力比较所有向量（复杂度 O(N·D)），要用 ANN 索引。常见的三类：

| 索引 | 原理 | 优点 | 缺点 |
|---|---|---|---|
| **HNSW** | 多层近邻图，从上层贪心下降到底层 | 召回高、查询快、实现成熟 | **内存大**（向量 + 图）；删除通常是标记删除；构建慢；严格过滤时变慢（见实验 3） |
| **IVF**（倒排文件） | 先聚类成 nlist 个簇，查询时只扫最近的 nprobe 个簇 | 内存比 HNSW 小，构建快，易分片（sharding） | 召回依赖 nprobe；簇边界附近的点会漏 |
| **PQ**（乘积量化（quantization））及标量量化 | 把向量压缩成少量字节 | **内存极省** | 有损；通常配合“用原始向量精排” |

另外：**磁盘型索引**（如 DiskANN 一类的思路）把大部分数据放在 SSD，内存只放压缩向量和图的一部分，适合十亿级。

### 5.4 实验 2：召回、延迟、内存的取舍（合成数据）

下面的实验在 20 万个 128 维合成向量上，对比精确搜索、HNSW、int8 标量量化（quantization）和 IVF-PQ。**再次强调：数据是合成的聚簇高斯分布，不是真实文本嵌入（embedding），绝对数字不能照搬，只看趋势。**

```python
"""实验 2：近似最近邻（ANN）的召回率、速度与内存取舍。
数据是**合成的**：20 万个 128 维向量，由 400 个高斯簇生成（模拟“主题聚集”）。真实的文本嵌入分布不同，
结果的绝对数字不能照搬，但“召回率随搜索宽度上升、量化省内存但损失精度”这些趋势是通用的。
对比：精确搜索（暴力）、HNSW（hnswlib，不同 ef）、标量量化（int8）、IVF-PQ（faiss，不同 nprobe）。
"""
import time
import numpy as np
import hnswlib
import faiss

rng = np.random.default_rng(0)
N, D, NQ, K = 200_000, 128, 1000, 10
centers = rng.normal(size=(400, D)).astype("float32") * 3
assign = rng.integers(0, 400, size=N)
X = (centers[assign] + rng.normal(size=(N, D)).astype("float32")).astype("float32")
qa = rng.integers(0, 400, size=NQ)
Q = (centers[qa] + rng.normal(size=(NQ, D)).astype("float32")).astype("float32")

def normalize(a): return a / np.linalg.norm(a, axis=1, keepdims=True)
X, Q = normalize(X), normalize(Q)

# ---- 精确搜索（内积，已归一化 = 余弦）----
t = time.perf_counter()
gt = np.empty((NQ, K), dtype=np.int64)
for i in range(0, NQ, 100):
    s = Q[i:i + 100] @ X.T
    idx = np.argpartition(-s, K, axis=1)[:, :K]
    order = np.take_along_axis(s, idx, 1).argsort(1)[:, ::-1]
    gt[i:i + 100] = np.take_along_axis(idx, order, 1)
exact_ms = (time.perf_counter() - t) / NQ * 1000
print(f"数据：{N:,} 个 {D} 维向量，float32 共 {X.nbytes/1e6:.0f} MB；{NQ} 个查询，召回@{K}")
print(f"精确搜索（numpy 矩阵乘法，批量 100，BLAS 多线程）：{exact_ms:.2f} ms/查询 —— 复杂度 O(N·D)，N 增大就线性变慢")
print("（下面 HNSW 是单线程，精确搜索是多线程批量，“相对精确搜索”只看量级，不是严格公平比较。）\n")

def recall(pred): return np.mean([len(set(p) & set(g)) / K for p, g in zip(pred, gt)])

# ---- HNSW ----
for M, efc in ((16, 200),):
    idx = hnswlib.Index(space="ip", dim=D)
    t = time.perf_counter()
    idx.init_index(max_elements=N, ef_construction=efc, M=M)
    idx.set_num_threads(4)
    idx.add_items(X, np.arange(N))
    build = time.perf_counter() - t
    print(f"HNSW M={M} efConstruction={efc}：构建 {build:.0f} 秒（4 线程）")
    idx.set_num_threads(1)
    print(f"  {'ef(搜索宽度)':<14}{'召回@10':>10}{'延迟 ms/查询(单线程)':>24}{'相对精确搜索':>14}")
    for ef in (10, 20, 40, 80, 160, 320):
        idx.set_ef(ef)
        t = time.perf_counter()
        labels, _ = idx.knn_query(Q, k=K)
        ms = (time.perf_counter() - t) / NQ * 1000
        print(f"  {ef:<14}{recall(labels):>10.3f}{ms:>24.3f}{exact_ms/ms:>13.0f}x")

# ---- 标量量化（int8）：把每个维度线性映射到 [-127,127]，用于粗排或节省内存 ----
lo, hi = X.min(), X.max()
scale = 127.0 / max(abs(lo), abs(hi))
X8 = np.round(X * scale).astype(np.int8)
Q8 = np.round(Q * scale).astype(np.int8)
t = time.perf_counter()
pred8 = np.empty((NQ, K), dtype=np.int64)
X8f = X8.astype(np.float32)
for i in range(0, NQ, 100):
    s = Q8[i:i + 100].astype(np.float32) @ X8f.T
    idx_ = np.argpartition(-s, K, axis=1)[:, :K]
    order = np.take_along_axis(s, idx_, 1).argsort(1)[:, ::-1]
    pred8[i:i + 100] = np.take_along_axis(idx_, order, 1)
print(f"\nint8 标量量化：向量内存 {X.nbytes/1e6:.0f} MB -> {X8.nbytes/1e6:.0f} MB（4 倍），精确搜索的召回@10 = {recall(pred8):.3f}")

# ---- IVF-PQ：倒排索引 + 乘积量化，内存最小；再加“用原始向量精排”的 refine ----
nlist = 1024
faiss.omp_set_num_threads(1)
train = X[rng.choice(N, 60_000, replace=False)]
print(f"\nIVF-PQ：nlist={nlist}；PQ 是有损压缩，把每个向量压成 m 个字节")
for m in (16, 64):
    quant = faiss.IndexFlatIP(D)
    ivfpq = faiss.IndexIVFPQ(quant, D, nlist, m, 8, faiss.METRIC_INNER_PRODUCT)
    ivfpq.train(train); ivfpq.add(X)
    refined = faiss.IndexRefineFlat(ivfpq, faiss.swig_ptr(X))   # 候选用原始 float32 向量重新打分
    print(f"  m={m}：每向量 {m} 字节（原来 {D*4} 字节，压缩 {D*4//m} 倍）")
    print(f"    {'nprobe':<8}{'纯 PQ 召回':>12}{'PQ+精排(取20×k候选)召回':>26}{'精排延迟 ms':>14}")
    for nprobe in (4, 16, 64):
        ivfpq.nprobe = nprobe
        _, lab = ivfpq.search(Q, K)
        refined.k_factor = 20
        t = time.perf_counter()
        _, lab2 = refined.search(Q, K)
        ms = (time.perf_counter() - t) / NQ * 1000
        print(f"    {nprobe:<8}{recall(lab):>12.3f}{recall(lab2):>26.3f}{ms:>14.3f}")
print("\n结论：纯 PQ 在这份合成数据上召回很低（簇内点的距离差异本来就很小，量化误差盖过了差异）；")
print("但“PQ 做粗召回 + 用原始向量精排”可以把召回拉回来，内存只多放一份原始向量（可放磁盘/内存映射）。")
print("我没有在真实文本嵌入上测过：这里的绝对数字取决于这份合成数据，只看“趋势”和“粗召回+精排”这个做法。")
```

运行结果：

```text
数据：200,000 个 128 维向量，float32 共 102 MB；1000 个查询，召回@10
精确搜索（numpy 矩阵乘法，批量 100，BLAS 多线程）：2.20 ms/查询 —— 复杂度 O(N·D)，N 增大就线性变慢
（下面 HNSW 是单线程，精确搜索是多线程批量，“相对精确搜索”只看量级，不是严格公平比较。）

HNSW M=16 efConstruction=200：构建 10 秒（4 线程）
  ef(搜索宽度)           召回@10           延迟 ms/查询(单线程)        相对精确搜索
  10                 0.775                   0.026           86x
  20                 0.914                   0.036           61x
  40                 0.984                   0.058           38x
  80                 0.998                   0.095           23x
  160                1.000                   0.143           15x
  320                1.000                   0.216           10x

int8 标量量化：向量内存 102 MB -> 26 MB（4 倍），精确搜索的召回@10 = 0.878

IVF-PQ：nlist=1024；PQ 是有损压缩，把每个向量压成 m 个字节
  m=16：每向量 16 字节（原来 512 字节，压缩 32 倍）
    nprobe       纯 PQ 召回          PQ+精排(取20×k候选)召回       精排延迟 ms
    4              0.134                     0.814         0.090
    16             0.134                     0.814         0.095
    64             0.134                     0.814         0.238
  m=64：每向量 64 字节（原来 512 字节，压缩 8 倍）
    nprobe       纯 PQ 召回          PQ+精排(取20×k候选)召回       精排延迟 ms
    4              0.744                     0.996         0.106
    16             0.745                     1.000         0.172
    64             0.745                     1.000         0.402

结论：纯 PQ 在这份合成数据上召回很低（簇内点的距离差异本来就很小，量化误差盖过了差异）；
但“PQ 做粗召回 + 用原始向量精排”可以把召回拉回来，内存只多放一份原始向量（可放磁盘/内存映射）。
我没有在真实文本嵌入上测过：这里的绝对数字取决于这份合成数据，只看“趋势”和“粗召回+精排”这个做法。
```

**怎么读（面试里能说的话）**：

1. **HNSW 的 `ef`（搜索宽度）是召回与延迟的旋钮**：ef=10 时召回约 0.78，ef=40 约 0.98，ef=80 以后接近 1.0，延迟随 ef 近似线性增长（0.03 ms 到 0.2 ms）。生产上通常选一个让召回达到目标（如 0.95 到 0.99）的最小 ef，再用评测集（evaluation set）确认**端到端**效果，因为 ANN 的召回 ≠ 最终答案质量。
2. **相对精确搜索快一到两个数量级**，而且精确搜索的代价随 N 线性增长，ANN 增长慢得多。（这里精确搜索用了多线程批量，HNSW 是单线程，比值只看量级。）
3. **int8 标量量化**：内存降到 1/4，在这份合成数据上精确搜索的召回降到约 0.88。量化会损失精度。
4. **IVF-PQ**：每向量 16 字节（压缩 32 倍）时，纯 PQ 召回很低（约 0.13）；每向量 64 字节时约 0.75。**但“PQ 做粗召回，再用原始向量对候选精排”可以把召回拉回到 0.8 到 1.0**（取 20 倍候选）。这是大规模下常见的两段式做法：压缩向量常驻内存，原始向量放磁盘或内存映射，只对少量候选读取。
5. **内存与召回的取舍**要和估算（实验 1）结合：3350 万个块 float32 要 137 GB；int8 要 34 GB；PQ 只要几 GB。**所以“选哪种索引”是由“放不放得下内存”和“召回目标”共同决定的。**
6. **提醒**：构建参数（HNSW 的 M、efConstruction）也影响召回、内存和构建时间；M 越大图越稠密，内存越大、召回越好；这里固定 M=16。

### 5.5 查询理解（query understanding）

用户的原始查询往往不适合直接检索（retrieval）。可选的步骤（**每一步都增加延迟与成本，要用评测集（evaluation set）证明值得**）：

- **对话式改写**：多轮对话里“那它的价格呢？”要结合历史改写成独立的问题。小模型即可。
- **缩写与术语展开**：用企业词典/同义词（synonym）表。
- **查询拆分**：“对比 A 和 B 的退款政策” 拆成两个子查询分别检索。
- **假设性文档嵌入（HyDE）**：先让模型写一个假想的答案，用它的嵌入去检索。有时能提升召回，但增加延迟，且可能引入偏差。
- **路由（routing）**：判断该查哪个数据源/索引（政策文档、代码、工单（ticket）），或者判断**是否需要检索**（闲聊、简单计算不需要）。
- **澄清问题**：查询太模糊时，反问用户，而不是猜。

### 5.6 重排序（reranking）

- **为什么**：向量检索（vector search）是“双塔（bi-encoder）”——查询和文档分别编码，只比较向量，快但粗。**交叉编码器（cross-encoder）** 把（查询,文档）一起输入，能捕捉细粒度交互，更准，但要对每个候选单独打分，贵。
- **典型用法**：召回 top-50 到 top-100，重排序（reranking）后取 top-5 到 top-10 送模型。
- **取舍**：精度提升明显，代价是延迟（实验 1 的预算（budget）里给了 250 ms）和算力（候选数 × QPS）。控制成本的办法：减少候选数、缓存（cache）、用小模型、对高置信的查询跳过重排序。
- **延迟交互模型（如 ColBERT 式的多向量）**：折中方案，存储更大。
- **也可以用 LLM 做重排序**（listwise），更灵活但更慢更贵，一般只在对质量要求极高的场景。

### 5.7 多跳与“代理式 RAG”（agentic RAG）

- 有些问题需要**多步检索（retrieval）**：“去年 A 部门的预算（budget）比 B 部门高多少？” 要先查两个数字再计算。
- **代理式（agentic） RAG**：让模型决定“要不要检索、检索什么、检索结果够不够、是否继续检索”。灵活，但**延迟和成本不可控，行为更难评估**。设计建议：先把单次检索做好；对确实需要的场景再加迭代，并设置**步数上限、总 token 预算和超时**。

---

## 六、权限与多租户：企业 RAG 最容易出大事的地方

### 6.1 为什么单独拿出来讲

企业数据有访问控制（access control）：同一个知识库（knowledge base）里，HR 文档只有 HR 能看，某个项目的设计文档只有项目成员能看。如果 RAG 把用户无权看的内容检索（retrieval）出来，哪怕模型只是“总结”了一下，也算数据泄露。据备考站和实践经验，这是企业 RAG 面试里**区分有生产经验和没有生产经验**的话题。

### 6.2 基本原则

1. **在检索（retrieval）阶段就按用户权限过滤（permission filtering），不是生成之后**。不能指望提示词（prompt）里写“不要透露用户无权查看的内容”——模型看到的上下文里就不该有。
2. **给每个块打上权限元数据（metadata）**：允许访问的主体（用户、群组、角色）的标识。拒绝（deny）优先于允许（grant）。
3. **权限同步和内容同步分开**：权限变化更频繁，需要更快的传播（分钟级甚至更快）；权限元数据可以单独更新，不必重嵌。
4. **查询时解析用户的身份和所属群组**，作为过滤条件传给检索。
5. **纵深防御（defense in depth）**：检索过滤之外，在**进入提示词之前**再向权威系统（源系统或权限服务）确认一次用户对这些块的访问权；记录每一次授权（authorization）决定用于审计（audit）。这样即使索引里的权限元数据过期或检索后端有 bug，也不会泄露。
6. **缓存（cache）要带权限维度**：任何查询缓存、语义缓存（semantic cache）的键都必须包含权限范围，否则 A 用户的结果可能被 B 用户命中。
7. **删除与撤销权限要有明确的传播时延指标（metrics）**，并监控。
8. **来源有额外限制时要尊重**：例如某些文档有敏感度标签，是在访问控制（access control）之外的第二道门槛；为了抓取全量权限，通常需要应用级身份而不是某个用户的令牌。（这些是备考站提到的实践细节，具体要看各数据源的 API。）

### 6.3 过滤发生在哪里：post-filter 与 pre-filter

**post-filter（先检索，再过滤）**：先取 top-k'，再丢掉用户无权的块。简单，但：**如果用户能看到的块很少，top-k' 里可能一个都没有**，结果凑不够；更糟的是，权限和内容相关时（团队的文档往往集中在少数主题），更难命中。

**pre-filter / 过滤检索（filtered search）**：在 ANN 遍历过程中就跳过无权限的节点，只返回有权限的。不会凑不够，但**在过滤非常严格时，图遍历要走很远才能找到可见节点，变得很慢**；不同的向量库实现差异很大（有的在遍历中过滤，有的先过滤再暴力，有的有迭代扫描）。

**精确搜索可见子集**：当用户可见的集合很小（如几千个块）时，直接在这个集合里暴力搜索，又快又准。

### 6.4 实验 3：三种过滤方式的真实表现（合成数据）

场景：20 万个块，用户可见一部分，要返回用户可见块中的 top-10。**真值**是“只在可见块里精确搜索”的结果。可见集有两种分布：随机（与内容无关），和与内容相关（可见的块集中在少数主题簇里，更像“某个团队的文档”）。

```python
"""实验 3：权限过滤——先检索再过滤（post-filter） vs 检索时过滤（pre-filter / filtered search）。
场景：20 万个块，每个块有访问控制（ACL）。用户只能看到一部分块（可见比例 p）。要返回该用户可见的 top-10。
真值 = 在“用户可见的块”里精确搜索得到的 top-10。
对比：
  A. post-filter：先 ANN 取 top-k'，再丢掉不可见的，剩多少算多少；
  B. 提高 k'（取 top-100/1000 再过滤）；
  C. HNSW 内置过滤（hnswlib 的 filter 回调，在遍历图的过程中跳过不可见节点）；
  D. 精确搜索可见子集（可见集很小时最简单、最准）。
可见集有两种分布：随机（与内容无关）、与内容相关（可见的块集中在少数主题簇里，更像真实的“某个团队的文档”）。
数据是合成的（同实验 2），只看趋势。
"""
import time
import numpy as np
import hnswlib

rng = np.random.default_rng(1)
N, D, NQ, K = 200_000, 128, 300, 10
C = 400
centers = rng.normal(size=(C, D)).astype("float32") * 3
assign = rng.integers(0, C, size=N)
X = centers[assign] + rng.normal(size=(N, D)).astype("float32")
X /= np.linalg.norm(X, axis=1, keepdims=True)
qa = rng.integers(0, C, size=NQ)
Q = centers[qa] + rng.normal(size=(NQ, D)).astype("float32")
Q /= np.linalg.norm(Q, axis=1, keepdims=True)

idx = hnswlib.Index(space="ip", dim=D)
idx.init_index(max_elements=N, ef_construction=200, M=16)
idx.set_num_threads(4); idx.add_items(X, np.arange(N)); idx.set_num_threads(1)
idx.set_ef(100)

def exact_topk(allowed_ids, q_idx_subset):
    A = X[allowed_ids]
    res = []
    for q in Q:
        s = A @ q
        top = np.argpartition(-s, min(K, len(s) - 1))[:K]
        res.append(allowed_ids[top[np.argsort(-s[top])]])
    return res

def run(visible_mask, qs):
    allowed = np.flatnonzero(visible_mask)
    t = time.perf_counter(); gt = exact_topk(allowed, None); t_exact = (time.perf_counter() - t) / NQ * 1000
    out = {}
    def rec(preds):
        r = [len(set(p) & set(g)) / K for p, g in zip(preds, gt)]
        return float(np.mean(r))
    def filled(preds):
        return float(np.mean([min(len(p), K) / K for p in preds]))
    for kp in (10, 100, 1000):
        idx.set_ef(max(100, kp))
        t = time.perf_counter(); lab, _ = idx.knn_query(Q, k=kp); ms = (time.perf_counter() - t) / NQ * 1000
        preds = [[i for i in row if visible_mask[i]][:K] for row in lab]
        out[f"A post-filter, 先取 top-{kp}"] = (rec(preds), filled(preds), ms)
    idx.set_ef(100)
    t = time.perf_counter()
    preds = []
    for q in Q:
        try:
            lab, _ = idx.knn_query(q[None, :], k=K, filter=lambda i: bool(visible_mask[i]))
            preds.append(list(lab[0]))
        except RuntimeError:
            preds.append([])
    ms = (time.perf_counter() - t) / NQ * 1000
    out["C HNSW 内置过滤 (ef=100)"] = (rec(preds), filled(preds), ms)
    out["D 精确搜索可见子集"] = (1.0, 1.0, t_exact)
    return out, len(allowed)

def show(title, mask):
    out, n = run(mask, None)
    print(f"\n{title}：用户可见 {n:,} 个块（{n/N*100:.2f}%）")
    print(f"  {'方案':<28}{'召回@10':>9}{'凑够 10 条的比例':>18}{'ms/查询':>10}")
    for k, (r, f, ms) in out.items():
        print(f"  {k:<28}{r:>9.3f}{f:>18.3f}{ms:>10.3f}")

for p in (0.5, 0.05, 0.005):
    show(f"[随机可见] p={p}", rng.random(N) < p)

for ncl, label in ((200, "可见 200 个主题簇"), (20, "可见 20 个主题簇"), (2, "可见 2 个主题簇")):
    chosen = rng.choice(C, ncl, replace=False)
    show(f"[内容相关] {label}", np.isin(assign, chosen))
```

运行结果：

```text
[随机可见] p=0.5：用户可见 100,117 个块（50.06%）
  方案                              召回@10        凑够 10 条的比例     ms/查询
  A post-filter, 先取 top-10        0.496             0.496     0.143
  A post-filter, 先取 top-100       0.999             1.000     0.114
  A post-filter, 先取 top-1000      1.000             1.000     1.001
  C HNSW 内置过滤 (ef=100)            1.000             1.000     0.411
  D 精确搜索可见子集                      1.000             1.000     1.287

[随机可见] p=0.05：用户可见 10,036 个块（5.02%）
  方案                              召回@10        凑够 10 条的比例     ms/查询
  A post-filter, 先取 top-10        0.049             0.049     0.168
  A post-filter, 先取 top-100       0.499             0.499     0.163
  A post-filter, 先取 top-1000      1.000             1.000     1.257
  C HNSW 内置过滤 (ef=100)            1.000             1.000     2.560
  D 精确搜索可见子集                      1.000             1.000     0.115

[随机可见] p=0.005：用户可见 1,020 个块（0.51%）
  方案                              召回@10        凑够 10 条的比例     ms/查询
  A post-filter, 先取 top-10        0.005             0.005     0.106
  A post-filter, 先取 top-100       0.051             0.051     0.102
  A post-filter, 先取 top-1000      0.507             0.507     0.881
  C HNSW 内置过滤 (ef=100)            1.000             1.000    28.847
  D 精确搜索可见子集                      1.000             1.000     0.020

[内容相关] 可见 200 个主题簇：用户可见 100,407 个块（50.20%）
  方案                              召回@10        凑够 10 条的比例     ms/查询
  A post-filter, 先取 top-10        0.503             0.503     0.159
  A post-filter, 先取 top-100       0.503             0.503     0.158
  A post-filter, 先取 top-1000      0.925             0.957     0.906
  C HNSW 内置过滤 (ef=100)            0.953             1.000     0.781
  D 精确搜索可见子集                      1.000             1.000     1.491

[内容相关] 可见 20 个主题簇：用户可见 9,953 个块（4.98%）
  方案                              召回@10        凑够 10 条的比例     ms/查询
  A post-filter, 先取 top-10        0.033             0.033     0.173
  A post-filter, 先取 top-100       0.033             0.033     0.174
  A post-filter, 先取 top-1000      0.237             0.266     1.087
  C HNSW 内置过滤 (ef=100)            0.928             1.000     9.547
  D 精确搜索可见子集                      1.000             1.000     0.154

[内容相关] 可见 2 个主题簇：用户可见 954 个块（0.48%）
  方案                              召回@10        凑够 10 条的比例     ms/查询
  A post-filter, 先取 top-10        0.003             0.003     0.130
  A post-filter, 先取 top-100       0.003             0.003     0.141
  A post-filter, 先取 top-1000      0.029             0.031     1.002
  C HNSW 内置过滤 (ef=100)            0.975             1.000    62.698
  D 精确搜索可见子集                      1.000             1.000     0.019
```

**逐条解读**：

1. **随机可见，50%**：post-filter 先取 top-10，召回只有约 0.5（因为大约一半被丢了，凑不够 10 条）；先取 top-100 就够了。
2. **随机可见，5%**：先取 top-100 召回只有约 0.5，**要取 top-1000 才到 1.0**。可见比例越低，要“多取”的倍数越大（大约是 1/p 倍）。
3. **随机可见，0.5%**：连 top-1000 也只有约 0.5；post-filter 基本失效。HNSW 内置过滤能达到 1.0，但延迟升到约 30 ms（遍历要走很远）；而**直接精确搜索这 1000 个可见块只要约 0.02 ms**。
4. **内容相关的可见集**（更贴近真实）：post-filter **更差**。可见 20 个主题簇（5% 的块）时，top-1000 之后召回仅约 0.24，凑够 10 条的只有 27%——因为用户的查询落在不可见的主题附近，top-1000 全是不可见的内容。HNSW 内置过滤召回约 0.93，凑够 10 条是 100%。
5. **HNSW 内置过滤在严格过滤下变慢**：可见 2 个主题簇（0.5%）时延迟约 60 ms，是普通查询的上千倍。
6. **精确搜索可见子集**在可见集小时最快最准：O(可见集大小)。

**结论（面试里这样讲）**：
- **post-filter 只在“用户能看到绝大多数内容”时可用**，企业场景里不能作为主要方案。
- **过滤检索（in-index filtering）** 是通用方案，但要在你的向量库上**实测严格过滤时的延迟与召回**。
- **按可见集大小选策略**：很小 → 暴力扫可见子集；很大 → 内置过滤；中间 → 看实测。很多系统按租户（tenant）/部门**拆分索引**或分区（partition），让大多数查询的可见集就等于一个分区。
- **提醒**：这是合成数据上的趋势，具体向量库的过滤实现（预过滤、迭代扫描等）差别很大，生产选型一定要用自己的 ACL 分布压测。

### 6.5 权限模型细节

- **群组爆炸**：一个用户可能属于几百个群组。把“用户的所有群组”展开成大 OR 条件会很慢（备考站提到过长的等值 OR 链在某些后端很慢）。办法：用“集合包含”类的过滤运算；预先把用户展开成一个更紧凑的“有效主体集合”并缓存（cache，带版本）；或把常见权限模式映射成少量“权限标签”。
- **继承与嵌套**：文件夹继承、群组嵌套——在摄入（ingestion）时把有效权限“展平”，或在查询时展开。权衡：摄入时展平读得快但更新代价大。
- **多租户隔离（tenant isolation）**：每个租户（tenant）一个索引/命名空间（namespace，强隔离，成本高，租户多了管理难）；共享索引 + 租户 ID 过滤（便宜，但过滤性能和“吵闹邻居（noisy neighbor）”要管）；混合：大租户独立、小租户共享。**加密密钥按租户分开**可增加隔离。
- **审计（audit）**：记录谁在什么时候检索（retrieval）了哪些文档、模型看到了哪些块。

---

## 七、生成：上下文、引用与拒答

### 7.1 上下文构造（context assembly）

- **预算（budget）**：提示词（prompt）总 token 有上限，也决定延迟与成本。分配：系统提示（system prompt） + 对话历史摘要 + 检索（retrieval）块 + 预留给答案。实验 1 里是约 600 + 6×512 + 400 输出。
- **选哪些块**：重排序（reranking）后取前几个；**去重（deduplication）**（相同或近似的块、同一文档多个版本）；限制同一文档的块数量，增加来源多样性；父子块（parent-child chunks）情况下合并同一父块。
- **顺序**：模型对长上下文中间部分的利用往往较差（所谓 “lost in the middle” 现象，有研究报告过），所以把最相关的放在开头或结尾，上下文不要无谓地变长。**短而相关胜过长而全。**
- **标注**：每个块带上来源 ID（如 `[doc12#3]`），方便模型引用（citation），也方便后处理校验。
- **时间与版本**：块要带更新时间；同一问题有新旧两个版本的文档时，提示模型以较新的为准，或在检索阶段按有效期过滤。

### 7.2 提示词与行为约束

- 明确指令：**只依据提供的上下文回答**；找不到就说不知道；给出引用（citation）；回答格式；语气。
- **把检索（retrieval）内容当数据，不当指令**（见第九部分提示注入（prompt injection））。
- 示例（few-shot）：展示怎么引用、怎么拒答（refusal）。
- **输出结构化**（JSON：答案 + 引用列表 + 置信度）便于后处理。

### 7.3 引用（citation）与可验证性

- **为什么**：用户能核实，是降低“幻觉（hallucination）”影响的最有效方式；对合规（compliance）场景是必须。
- **做法**：模型输出引用的块 ID；**后处理校验**引用的 ID 确实在送入的上下文里；更严格的，检查引文（quote）确实是原文子串；展示来源链接和标题。
- **注意**：引用存在不代表答案被引用内容支持——还需要评估“引用正确性”（citation correctness）。

### 7.4 拒答与置信度

- 检索（retrieval）阶段的信号：top 结果的相关性分数过低、各路检索结果几乎不重叠、重排序（reranking）分数低 → 说明“可能没有答案”。
- 生成阶段的信号：模型自己的判断、答案与上下文的一致性（consistency）检查。
- 策略：**宁可说“没有找到相关信息，您可以向 X 咨询”，也不要编造。** 对高风险场景设置更严格的阈值，并把“低置信”情况转人工。
- **阈值要用评测集（evaluation set）校准（calibration）**，同时看“该答没答”（过度拒答（refusal））和“不该答却答了”两类错误。

### 7.5 幻觉的来源与缓解

| 来源 | 缓解 |
|---|---|
| 检索（retrieval）没找到 → 模型凭记忆（memory）编 | 拒答（refusal）规则、置信度、提示词（prompt）约束 |
| 检索到了但被噪声淹没 | 重排序（reranking）、减少块数、去重（deduplication） |
| 上下文里有冲突信息 | 按时间/权威度排序，提示模型指出冲突 |
| 模型曲解或过度推断 | 要求逐条引用（citation）、引文校验、更保守的模型/温度 |
| 切块（chunking）切断关键信息 | 父子块（parent-child chunks）、上下文补充 |

### 7.6 缓存与成本控制

- **嵌入（embedding）缓存（cache）**：相同文本不重复嵌入（内容哈希）。
- **查询结果缓存**：规范化后的查询 + **权限范围** 作为键；设置较短 TTL 并在相关文档更新时失效。**语义缓存（semantic cache）**（相似问题复用答案）风险：把“相似”当成“相同”会返回错的答案，也有跨权限泄漏风险；若用，只用于低风险场景，并把权限范围放进键。
- **提示缓存（prompt caching，模型服务商的特性）**：系统提示（system prompt）和固定前缀可复用，降低成本和延迟，具体支持情况以服务商文档为准。
- **模型路由（model routing）**：简单问题用小模型，复杂问题用大模型；用评测（evaluation, or evals）证明质量没有下降。
- **减少输入 token**：更少更准的块、压缩上下文。
- **流式（streaming）输出**：不降低成本，但显著改善感知延迟。

---

## 八、规模、延迟与可靠性

### 8.1 先问：瓶颈真的是检索吗？

回到实验 1：QPS 很低，瓶颈通常是 **LLM 的延迟、并发（concurrency）与成本**，以及**索引的内存**。所以扩展的次序是：先扩 LLM 调用（并发限制、排队、重试（retry）、降级），再考虑索引分片（sharding，为了内存），最后才考虑检索（retrieval）吞吐。

### 8.2 索引分片与尾延迟

当索引大到单机放不下，就分片（sharding）：**按文档/块的哈希**（负载均衡，但每个查询要问所有分片，即 scatter-gather），或**按租户（tenant）/部门/时间**（查询只问相关分片，但可能不均衡）。

**scatter-gather 的问题是尾延迟（tail latency）放大**：一次查询要等所有分片返回，延迟取最大值。分片越多，“至少有一个分片很慢”的概率越高。

### 8.3 实验 4：尾延迟放大与缓解（模拟）

```python
"""实验 4：分片扇出（scatter-gather）的尾延迟放大，以及对冲请求（hedged request）的缓解。纯模拟（numpy）。
一次查询要等 S 个分片全部返回，所以查询延迟 = 各分片延迟的最大值。
单分片延迟用对数正态分布模拟：中位数 10 ms，p99 约 40 ms（假设值；真实系统要实测）。
"""
import numpy as np

rng = np.random.default_rng(0)
N = 200_000
MU, SIGMA = np.log(10.0), 0.6      # 中位数 10 ms；sigma=0.6 时 p99 ≈ 10·e^{0.6·2.326} ≈ 40 ms
def shard_latency(size): return rng.lognormal(MU, SIGMA, size)

single = shard_latency(N)
print(f"单个分片：p50={np.percentile(single,50):.1f} ms  p95={np.percentile(single,95):.1f} ms  p99={np.percentile(single,99):.1f} ms\n")

print("等待全部 S 个分片（取最大值）：")
print(f"  {'分片数 S':<10}{'p50':>8}{'p95':>8}{'p99':>8}{'p99 / 单分片 p99':>20}")
base99 = np.percentile(single, 99)
for S in (1, 4, 16, 64, 256):
    mx = shard_latency((N, S)).max(axis=1)
    print(f"  {S:<10}{np.percentile(mx,50):>8.1f}{np.percentile(mx,95):>8.1f}{np.percentile(mx,99):>8.1f}{np.percentile(mx,99)/base99:>19.2f}x")
print("  理论：单分片超过自己 p99 的概率是 1%；S=64 时“至少一个分片慢”的概率 = 1-0.99^64 =", f"{(1-0.99**64)*100:.0f}%")

print("\n缓解 1：对冲请求。每个分片先发一次；如果 H 毫秒内没返回，就向该分片的另一个副本再发一次，取先到的。")
S = 64
print(f"  S={S}：{'H(ms)':<8}{'p50':>8}{'p99':>8}{'额外请求比例':>14}")
for H in (None, 40, 25, 15):
    a = shard_latency((N, S))
    if H is None:
        mx = a.max(axis=1); extra = 0.0
        label = "不对冲"
    else:
        b = H + shard_latency((N, S))                  # 第二次请求在 H 之后发出
        t = np.where(a > H, np.minimum(a, b), a)
        mx = t.max(axis=1); extra = float((a > H).mean())
        label = f"H={H}"
    print(f"       {label:<9}{np.percentile(mx,50):>8.1f}{np.percentile(mx,99):>8.1f}{extra*100:>13.1f}%")

print("\n缓解 2：部分结果（deadline）。在时限 T 到达时，用已返回的分片结果作答，丢弃慢分片，并标注“结果可能不完整”。")
S = 64
print(f"  S={S}：{'时限 T(ms)':<12}{'平均丢失分片数':>16}{'有分片被丢的查询占比':>22}")
a = shard_latency((N, S))
for T in (30, 40, 60, 100):
    lost = (a > T).sum(axis=1)
    print(f"       {T:<12}{lost.mean():>16.2f}{(lost>0).mean()*100:>21.1f}%")
print("  取舍：延迟有上限，但召回会有损失；对 RAG 来说，少一个分片的结果通常好过整个请求超时。")
```

运行结果：

```text
单个分片：p50=10.0 ms  p95=26.8 ms  p99=40.5 ms

等待全部 S 个分片（取最大值）：
  分片数 S          p50     p95     p99       p99 / 单分片 p99
  1             10.0    26.8    40.3               1.00x
  4             18.2    38.4    54.0               1.33x
  16            28.1    51.4    69.0               1.70x
  64            39.7    66.5    87.0               2.15x
  256           53.1    83.7   107.0               2.64x
  理论：单分片超过自己 p99 的概率是 1%；S=64 时“至少一个分片慢”的概率 = 1-0.99^64 = 47%

缓解 1：对冲请求。每个分片先发一次；如果 H 毫秒内没返回，就向该分片的另一个副本再发一次，取先到的。
  S=64：H(ms)        p50     p99        额外请求比例
       不对冲          39.7    86.9          0.0%
       H=40         39.7    60.5          1.0%
       H=25         34.4    51.6          6.3%
       H=15         29.1    46.1         25.0%

缓解 2：部分结果（deadline）。在时限 T 到达时，用已返回的分片结果作答，丢弃慢分片，并标注“结果可能不完整”。
  S=64：时限 T(ms)             平均丢失分片数            有分片被丢的查询占比
       30                      2.15                 88.7%
       40                      0.67                 49.1%
       60                      0.09                  8.8%
       100                     0.00                  0.4%
  取舍：延迟有上限，但召回会有损失；对 RAG 来说，少一个分片的结果通常好过整个请求超时。
```

**解读**：
1. 单分片（sharding） p99 约 40 ms；查询要等 64 个分片时，p99 变成约 87 ms（2.2 倍），p50 也从 10 ms 变成约 40 ms——因为“64 个分片里至少一个慢”的概率有 47%。
2. **对冲请求（hedged requests）**：某分片超过 H 毫秒没返回，就向另一个副本（replica）再发一次，取先到的。H=40 ms 时只多发 1% 的请求，p99 从 87 降到约 60 ms；H 越小效果越好但额外请求越多（H=15 ms 时多发 25%）。**需要每个分片有至少两个副本。**
3. **时限 + 部分结果**：到时限就用已返回的分片结果作答。T=60 ms 时只有 9% 的查询丢了分片，平均丢 0.09 个。**对 RAG 来说，缺一个分片的结果通常好过整个请求超时。** 要把“结果可能不完整”记录下来用于监控。
4. 其他办法：减少分片数（用更大内存的机器或量化（quantization））、分层索引（热数据在内存，冷数据在 SSD）、按路由（routing）键只查相关分片、副本之间的负载均衡与慢节点剔除。

### 8.4 可用性与降级（graceful degradation）

RAG 流水线中各依赖都可能失败，要预先设计“退一步”的行为：

| 故障 | 降级策略 |
|---|---|
| 重排序（reranking）服务慢/挂 | 跳过重排序，直接用融合结果（质量略降） |
| 向量检索（vector search）超时 | 只用关键词检索（retrieval）结果；或返回缓存（cache） |
| 查询改写（query rewriting）失败 | 用原始查询 |
| 某个分片（sharding）超时 | 用部分结果作答，并标注 |
| LLM 提供商限流（rate limiting）/故障 | 退避（backoff）重试（retry） → 切换备用模型/区域 → 返回“仅展示相关文档片段，不生成答案” |
| 嵌入（embedding）服务故障 | 查询时：关键词检索兜底；摄入（ingestion）时：队列堆积，恢复后追赶 |
| 权限服务不可用 | **失败关闭**（fail closed）：拒绝返回结果，而不是跳过权限检查 |

要点：**大多数阶段失败时“质量下降但可用”，唯独权限相关必须失败关闭。** 还有：超时预算（budget）要分摊到各阶段、重试要带退避与抖动（jitter）并限制总重试、对下游设置并发（concurrency）上限（舱壁）、队列与背压（backpressure）。

### 8.5 摄入管线的可靠性

- 消息队列（message queue）解耦连接器（connector）、解析、嵌入（embedding）、写入；各阶段幂等（idempotency）（用文档 ID + 内容哈希作为幂等键（idempotency key））。
- 死信队列（dead-letter queue）收集总是失败的文档；告警（alerting）；可重放（replay）。
- 大文件/大批量的限流（rate limiting），防止摄入（ingestion）压垮嵌入服务或影响在线查询（隔离资源）。
- 对账（reconciliation）：定期比较源系统的文档列表与索引里的列表，发现漏同步和孤儿数据。

### 8.6 成本模型

主要成本项：**LLM 生成（通常最大）** > 嵌入（embedding，一次性 + 增量）> 重排序（reranking）算力 > 向量库内存/存储 > 解析（OCR/视觉）。优化的顺序：减少 LLM 输入 token（更精的上下文）、模型路由（model routing）、缓存（cache）、量化（quantization）索引、增量摄入（ingestion）、跳过无用的阶段。**每个优化都要用评测集（evaluation set）证明质量没有明显下降。**



---

## 九、评估与监控：怎么知道它是好的

### 9.1 为什么一定要讲评估

RAG 的质量问题往往是**悄悄发生**的：文档变了、嵌入（embedding）模型换了、切块（chunking）改了、提示词（prompt）调了，系统仍然“能回答”，但答案变差了。没有评估，你只能靠用户投诉发现。面试里**主动讲评估**是区分高级候选人的信号（备考站的共同看法）。

### 9.2 把评估拆成两层

**检索（retrieval）层**（独立评估，因为它是天花板）：
- 需要一个**评测集（evaluation set）**：真实或合成的查询 + 标注“哪些文档/块是相关的”。
- 指标（metrics）：**recall@k**（相关块有没有出现在前 k 个里，最重要）、**precision@k**、**MRR**（第一个相关结果的排名倒数）、**nDCG**（考虑排序和分级相关）。
- 分别评估：召回阶段的 recall@100 和重排序（reranking）后的 recall@5/10。

**生成层**（端到端）：
- **忠实度（faithfulness / groundedness）**：答案中的论断是否都被上下文支持。
- **答案相关性与正确性**：答案是否回答了问题、是否与参考答案一致。
- **引用（citation）正确性**：引用的块是否真的支持对应论断。
- **拒答（refusal）质量**：该拒答时拒答了吗？不该拒答时答了吗？
- **其他**：格式、语气、长度、安全。

### 9.3 评测集怎么来

1. **从真实日志里挑**：用户真实提的问题（脱敏（data masking）），覆盖常见和长尾，**包括困难的**（多跳（multi-hop）、含缩写、含数字、无答案）。
2. **让领域专家标注**相关文档和参考答案——贵，但最可靠。从 100 到 300 个高质量样本起步，比几千个粗糙样本更有价值。
3. **用 LLM 合成**：从文档生成问题—答案对，快速扩充；**风险**：合成问题往往比真实问题“更容易”，措辞与文档过于相似，高估检索（retrieval）效果。要混合真实样本，并抽检。
4. **按切片（slice）评估**：按来源、文档类型、语言、查询类型分别看，平均值会掩盖某类问题的严重退化。
5. **评测集（evaluation set）要版本化**，并保持“冻结的回归集（regression set）”与“持续更新的新集”。

### 9.4 用 LLM 当评审（LLM-as-judge）

- 优点：便宜、可扩展。缺点：有偏差（偏爱长答案、偏爱自家模型、位置偏差（position bias）），要**用人工标注（human annotation）的样本校准（calibration）**（测它与人判断的一致率），评审提示词（prompt）也要版本化。
- 关键场景（高风险）仍需要人工抽检。
- 不要只看一个总分；看**失败样本**——读失败案例是改进最有效的方法。
- （搜索到的某备考资料给了一组 RAGAS 风格的阈值，例如忠实度（faithfulness）大于 0.9。**那是单个从业者的目标，不是行业标准**，应当用自己业务的人工评审数据来定门槛。）

### 9.5 回归门禁与上线流程

- 任何变更（切块（chunking）、嵌入（embedding）模型、检索（retrieval）参数、提示词（prompt）、模型版本）都先过**离线评测（offline evaluation）**，指标（metrics）不降才能进入灰度（canary release）。
- **灰度/影子（shadow）**：新旧管线对同一批线上查询并行运行，只展示旧的，比较新旧输出。
- **A/B 测试（A/B testing）**看线上指标，注意样本量和周期。
- 留好回滚（rollback）方案（索引别名切换、提示词版本）。

### 9.6 线上监控

| 类别 | 指标（metrics） |
|---|---|
| 质量代理指标 | 用户点赞/点踩、引用（citation）点击率、复制率、追问/重复提问率（可能说明没答好）、转人工率、拒答（refusal）率 |
| 检索（retrieval）健康 | 检索结果数为零的比例、top 分数分布、重排序（reranking）前后重合度、各路检索的贡献比例 |
| 系统 | 各阶段延迟（p50/p95/p99）、错误率、超时、降级触发次数、队列深度 |
| 摄入（ingestion） | 摄入延迟（从源变更到可检索）、失败率、死信数量、与源系统的对账（reconciliation）差异 |
| 权限 | 被权限过滤（permission filtering）掉的结果比例、授权（authorization）校验失败次数、删除传播延迟 |
| 成本 | 每次提问的 token、各阶段成本、缓存（cache）命中率 |
| 漂移 | 查询分布变化、新出现的高频无答案问题（说明知识库（knowledge base）缺内容） |

- **全链路追踪（trace）**：每次请求有一个 ID，记录改写后的查询、检索结果（块 ID 与分数）、权限过滤结果、最终进入提示词（prompt）的块、模型版本、答案、引用。出问题时能回放（replay）。**注意日志里的隐私**：脱敏（data masking）、访问控制（access control）、保留期。
- **知识库缺口**：统计“无答案/低置信”的高频问题，反馈给内容负责人补充文档，这是 RAG 系统带来的额外价值。

---

## 十、安全与合规

### 10.1 提示注入（prompt injection），特别是间接注入

- **直接注入**：用户在输入里写“忽略之前的指令”。
- **间接注入**：恶意指令藏在**被检索（retrieval）到的文档**里（网页、邮件、共享文档）。模型读到后可能照做（泄露其他内容、调用工具）。
- **缓解**：把检索内容明确标成“数据而非指令”（分隔符 + 提示词（prompt）声明）；**最小权限（least privilege）**——生成阶段的模型不应有执行危险操作的工具；若有工具，对敏感操作要求用户确认；输出过滤；监控异常；对不可信来源（外部网页）单独标注并降低信任；**不依赖单一防线**。
- **致命三要素（lethal trifecta）**（据业界常见说法）：同时具备“能读私有数据”“能接触不可信内容”“能向外发送数据”时风险最大。RAG 本身满足前两条，所以不要再轻易给它第三条（例如任意外发请求、渲染外部图片链接）。

### 10.2 数据泄漏

- 权限过滤（permission filtering）失败（第六部分）。
- 日志、缓存（cache）、评测集（evaluation set）里的敏感内容；第三方模型服务的数据保留与训练政策（合同与配置）。
- 引用（citation）中暴露用户无权看的文档标题或链接。
- 模型“记住”并在其他租户（tenant）的回答中泄露——通过不在共享的微调（fine-tuning）数据里混入租户数据来避免。
- **PII**：摄入（ingestion）时识别并脱敏（data masking）或打标；输出时过滤。

### 10.3 合规

- 数据驻留（data residency）（嵌入（embedding）和 LLM 调用发生在哪个区域）；删除权（删除传播到索引、缓存（cache）、日志、备份）；审计（audit，谁看了什么）；保留期；供应商评估。
- **可解释性**：引用（citation）来源 + 检索（retrieval）日志让答案可追溯。

---

## 十一、常见变体题（面试官换个场景时怎么调整）

**每个变体的思路**：先说和基础设计相同的部分，再说**这个场景改变了哪些假设**。

### 变体 1：企业内部知识助手（基础题）
本文主体。重点：多数据源连接器（connector）、权限、新鲜度、引用（citation）。

### 变体 2：客户支持机器人（面向外部客户）
- 数据：帮助中心文章、产品文档、历史工单（ticket）、政策。
- 变化：**错误的代价是客户体验和合规（compliance）**；要有明确的**升级到人工**路径；知识要有**版本与适用范围**（产品版本、地区、套餐）；**个性化**（读取该客户的账户信息，要权限和隐私控制）；高并发（concurrency）和公开暴露，要**防滥用和提示注入（prompt injection）**；**度量**：自助解决率（deflection）、转人工率、满意度。
- 设计：检索（retrieval）时按产品版本/地区过滤；结构化的订单/账户查询走工具（API）而不是向量检索（vector search）；回答必须引用（citation）；对政策类问题使用更严格的拒答（refusal）阈值。

### 变体 3：代码库问答/代码搜索
- 切块（chunking）：按语法结构（函数、类）而不是固定 token；保留文件路径、符号名、调用关系。
- 检索（retrieval）：**标识符精确匹配很重要**（函数名、报错码），所以关键词/符号索引权重更大；可结合代码图（调用关系、定义-引用（citation））；有时直接用代码搜索工具（grep、语言服务）作为检索器。
- 新鲜度：代码持续提交，增量按提交更新；分支与版本。
- 权限：仓库级权限；私有代码的合规（compliance）。
- 评估：能否定位到正确的文件与函数。

### 变体 4：法律/医疗等高精度场景
- 错误代价极高：**强制引用（citation） + 引文校验**，更低的幻觉（hallucination）容忍度（tolerance）；拒答（refusal）阈值更严；**人工复核**；完整**审计（audit）**与可追溯；文档版本与生效日期；不使用语义缓存（semantic cache）。
- 可能采用更保守的生成（抽取式回答、只复述原文）。

### 变体 5：新闻/行情等高频更新数据
- 新鲜度是第一要求：流式（streaming）摄入（ingestion）（消息队列（message queue）→嵌入（embedding）→写入）、秒到分钟级可检索（retrieval）；**时间衰减**（排序时加入时间权重）；索引分层（近期热数据小索引 + 历史大索引）；去重（deduplication）和事件聚合；过期数据下线。

### 变体 6：多模态/复杂文档（PDF 表格、图表、幻灯片）
- 解析是重点：版面分析、表格结构化、图表描述（视觉模型生成文字）；可对页面图像做多模态嵌入（embedding）或让视觉模型直接读页面（成本高，按需）；引用（citation）要能定位到页面区域。

### 变体 7：对话式 RAG（多轮、有记忆）
- 查询改写（query rewriting）结合历史；对话状态与摘要；区分“这一轮需要检索（retrieval）吗”；长对话的上下文预算（budget）；会话级缓存（cache）；用户偏好记忆（memory）要有隐私与删除机制。

### 变体 8：十亿级语料
- 分片（sharding）与分层索引；量化（quantization） + 磁盘索引 + 原始向量精排；两段式检索（retrieval，先粗召回再精排）；预计算与分区路由（routing）（按租户（tenant）、时间、主题）；成本成为首要问题（实验 1 的公式）；尾延迟（tail latency，实验 4）。

### 变体 9：多语言
- 多语言嵌入（embedding）模型；查询语言检测；是否翻译查询/文档；各语言的关键词分词（tokenization）和分析器；评测集（evaluation set）要覆盖各语言；跨语言检索（retrieval）的效果要专门评估。

---

## 十二、追问题库与参考答案

> 每题给出面试官想听到的要点。你的回答要结合自己的经验和场景假设，不要背诵。

### A. 总体设计与取舍

**Q1. 什么情况下不应该用 RAG？**
- 数据很小，能直接放进模型上下文（长上下文 + 提示缓存（prompt caching）可能更简单、更准）；
- 需要的是模型**行为/风格**的改变而不是知识（用微调（fine-tuning）或提示词（prompt））；
- 问题可以用结构化查询回答（SQL/API），RAG 反而不精确；
- 数据变化极快且需要精确计算（用工具）；
- 要求 100% 的确定性（deterministic）（用规则或检索（retrieval）而不生成）。
RAG 的价值在于：数据量大于上下文、需要最新或私有数据、需要引用（citation）、需要权限控制。

**Q2. RAG、微调、长上下文怎么选？**
- **RAG**：知识会变、需要引用与权限、数据量大。
- **微调**：改变行为、格式、风格、专用任务的稳定能力；不适合注入经常变化的事实，也不能做权限隔离。
- **长上下文**：数据少、问题需要全局理解；成本和延迟随长度增长，且长上下文中间部分利用率下降。
- 实际常**组合**使用：微调（或提示）定行为 + RAG 供知识 + 长上下文放更多检索结果。

**Q3. 如果只能做三件事来提高 RAG 质量，你选什么？**
1）建评测集（evaluation set）并读失败案例（没有度量就没有改进）；2）混合检索（hybrid search） + 重排序（reranking）；3）改进解析与切块（chunking，结构、表格、标题路径）。再加：拒答（refusal）与引用。

**Q4. 为什么说“检索是天花板”？怎么验证瓶颈在检索还是生成？**
把检索与生成分开评估：如果相关块没有进入上下文（recall@k 低），问题在检索；如果相关块在上下文里但答案仍错，问题在生成/提示。做法：用“带标准答案块的上下文”（oracle context）喂给模型，看答案质量——这给出生成层的上限。

**Q5. 你怎么决定 top-k？**
分两个 k：召回 k（如 50 到 100，追求高召回，用评测集的 recall@k 曲线找拐点）和送模型的 k（如 5 到 10，由 token 预算（budget）与精度决定，用端到端评测（evaluation, or evals）找最佳点）。k 越大，噪声与成本越高，且中间部分的利用率可能下降。

**Q6. 同一个问题在知识库（knowledge base）里有多个冲突答案（新旧版本）怎么办？**
入库时保留版本和生效日期；检索时按有效期过滤或提升新版本；上下文里标注日期并在提示中规定以新的为准；答案里明示冲突与来源；定期清理过期文档。

### B. 摄入与切块

**Q7. 怎么选块大小？**
没有普适答案：先用 256 到 512 token 加 10% 到 15% 重叠作基线，用评测集（evaluation set）比较不同大小与结构感知切块（chunking）；考虑父子块（parent-child chunks）；看文档类型（FAQ 适合小块，长报告适合结构切块）。强调“用评测集决定，参数版本化，改了要整库重嵌”。

**Q8. PDF 里的表格怎么处理？**
用版面分析/表格识别提取结构；转成保留行列关系的文本（Markdown 表或“列名: 值”的行描述）；表格整体作为一个块或每行一个带表头的块；复杂图表可用视觉模型生成描述；评测集里专门加表格类问题。

**Q9. 文档更新或删除后，怎么保证检索（retrieval）不会返回旧内容？**
增量同步（incremental sync）用变更事件 + 内容哈希；更新=原子替换该文档所有块（先写新后删旧，或用文档版本号（version number）过滤）；删除=在索引里标记删除并最终压缩；设一个传播时延指标（metrics）并监控；用定期对账（reconciliation）发现漏同步。

**Q10. 换了嵌入（embedding）模型怎么办？**
新模型的向量和旧向量不兼容。蓝绿（blue-green）重建：后台用新模型全量构建新索引，评测（evaluation, or evals）通过（recall、端到端）后别名切换，保留旧索引回滚（rollback）；构建期间的变更双写；成本用实验 1 的公式估。可以先在子集上评估新模型是否值得换。

**Q11. 怎么处理重复内容？**
内容哈希去重（deduplication）完全相同的；近似重复用 SimHash/MinHash 或嵌入相似度聚类；检索后按文档/聚类去重，避免上下文被同一内容占满；多版本文档保留最新并标注。

**Q12. 如何设计连接器（connector）的增量同步？**
优先用源系统的变更事件/变更令牌；退化为按修改时间轮询；处理分页（pagination）、限速、重试（retry）；保存游标；崩溃后可恢复；定期全量对账；权限与内容分开同步；对删除用墓碑（tombstone）事件或对账发现。

### C. 检索与排序

**Q13. 为什么混合检索（hybrid search）比纯向量好？什么时候纯向量够？**
见 5.2：标识符、缩写、稀有词需要关键词；同义改写需要向量。纯向量够用的情况：查询基本是自然语言描述、术语不多、有高质量的领域嵌入（embedding）；但混合检索成本很低，通常值得作为默认。要用评测集（evaluation set）验证两者的贡献。

**Q14. RRF 是怎么工作的？为什么不直接加权分数？**
得分 = 对每一路的 1/(k+排名) 求和。不同检索（retrieval）器的分数量纲和分布不同，直接加权要先归一化且不稳定；RRF 只用排名，稳健、无需调参（k 常取 60）。如果有足够数据，也可以训练一个学习排序模型来融合。

**Q15. 重排序（reranking）为什么更准？代价是什么？**
交叉编码器（cross-encoder）把查询与文档一起编码，能捕捉词级别的交互；双塔（bi-encoder）模型只比较各自的向量。代价：每个候选单独推理，延迟和算力随候选数线性增长。控制：候选数、批处理、小模型、缓存（cache）、条件触发。

**Q16. 查询改写（query rewriting）什么时候有用？**
对话式追问、指代、缩写；复杂问题拆分；口语化查询。风险：改写错误会放大偏差，增加延迟。要用评测集比较“有无改写”，并保留原始查询作为一路。

**Q17. ANN 索引怎么选？**
见 5.3 与实验 2：放得下内存且要高召回 → HNSW；内存紧 → IVF-PQ/量化（quantization） + 原始向量精排；超大规模 → 磁盘型索引。决定因素：块数×维度的内存（实验 1）、召回目标、更新频率、过滤需求。

**Q18. 向量检索（vector search）召回很高，但最终答案仍然不对，可能是什么原因？**
ANN 召回高只说明近似搜索接近精确搜索，不代表“嵌入找到了相关的块”（嵌入本身可能不好）；相关块在 top-k 但重排序没排上来；块切断了关键信息；上下文构造丢掉了；提示词（prompt）/模型问题；评测（evaluation, or evals）标注问题。逐层定位（Q4 的方法）。

**Q19. 怎么处理需要聚合多个文档的问题（总结、对比）？**
多查询拆分后各自检索；map-reduce 式总结（先分块总结再汇总）；提高上下文预算（budget）或用长上下文模型；对“全局问题”预先构建摘要层/知识图谱；明确告知用户范围限制。

### D. 权限与多租户

**Q20. 怎么保证用户看不到无权访问的文档？**
见第六部分：块级 ACL 元数据（metadata）；检索（retrieval）时过滤（in-index filter 或按可见集大小选策略）；进入提示词（prompt）前再校验；缓存（cache）键含权限；失败关闭（fail closed）；审计（audit）；权限同步延迟指标（metrics）。

**Q21. ACL 在源系统里改了，多久能生效？怎么做到？**
权限同步独立于内容，走变更事件（webhook/变更令牌）加定期全量对账（reconciliation）；ACL 元数据单独更新（不重嵌）；对高敏感内容可在查询时向源系统/权限服务实时校验；定义 SLA（例如分钟级）并监控；撤销权限的优先级高于授予。

**Q22. 用户属于几百个群组，过滤条件很长怎么办？**
用集合包含类过滤运算，而非长 OR 链；缓存用户的“有效主体集合”（带版本）；把常见权限组合映射成少量标签；或按权限分区索引；实测过滤性能（实验 3 提示严格过滤下可能很慢）。

**Q23. 多租户（multi-tenancy）：共享索引还是每租户（tenant）一个索引？**
共享索引：成本低、运维简单，但需要可靠的租户过滤、会有吵闹邻居（noisy neighbor）、一次过滤失误=跨租户泄漏；独立索引：强隔离、可按租户加密/删除/迁移，但成本高、租户多了难管。常用混合：大客户独立、小客户共享；无论哪种都做纵深防御（defense in depth）和审计。

**Q24. post-filter 为什么不行？**
实验 3：可见比例低或权限与内容相关时，top-k 里可能没有任何可见块（可见 20 个主题簇，先取 top-1000 再过滤，召回只有约 0.24）；要么凑不够，要么只能取很大的 k（延迟和成本上升）。

### E. 生成与质量

**Q25. 怎么减少幻觉（hallucination）？**
见 7.5：提高检索（retrieval）质量；提示词（prompt）约束只依据上下文；拒答（refusal）规则；引用（citation）并校验；更少更精的上下文；评测（evaluation, or evals）忠实度（faithfulness）并作为发布门槛；高风险场景人工复核。强调没有一种办法能完全消除，要多层。

**Q26. 引用是怎么实现并校验的？**
块带稳定 ID；提示词要求每个论断后标注块 ID；后处理检查 ID 都在送入的上下文里；严格场景检查引文是原文子串；展示来源链接；评估引用正确性（引用是否真的支持论断）。

**Q27. 什么时候拒答？阈值怎么定？**
检索分数低、各路结果不一致、模型判断上下文不足、问题超出范围、权限不足。阈值用评测集（evaluation set）校准（calibration），在“过度拒答”与“错误回答”之间权衡；高风险场景偏向拒答，并转人工。

**Q28. 上下文太长怎么办？**
减少块数（更强的重排序（reranking））；压缩（对每块做摘要或抽取相关句子，代价是多一次调用和信息损失）；父子块（parent-child chunks）只取需要的部分；去重（deduplication）；把重要信息放在开头和结尾；评估长度对质量的影响。

**Q29. 如何支持流式（streaming）输出，同时做引用校验和护栏（guardrails）？**
流式先输出正文，引用在结尾统一校验；或在句子级别缓冲后校验再输出；对高风险内容采用“非流式 + 完整校验”。取舍：感知延迟 vs 校验完整性。

**Q30. 评估时怎么避免“自己出题自己考”？**
评测集包含真实日志；合成样本要抽检并混入真实样本；评审模型（judge model）与被评估模型不同源并用人工样本校准；保留一个不用于调参的测试集（test set）；按切片（slice）看结果。

### F. 规模、性能与可靠性

**Q31. 查询延迟 5 秒，怎么排查？**
先看各阶段延迟分布（追踪（trace））：通常 LLM 首 token 与生成长度占大头 → 流式（streaming）、缩短输入、更快模型、缓存（cache）；其次是重排序（reranking）和查询改写（query rewriting） → 减少候选/跳过；检索（retrieval）慢 → 索引参数、过滤、分片（sharding）尾延迟（tail latency，实验 4）；网络与冷启动（cold start）。不要凭猜测，先有数据。

**Q32. 怎么处理 LLM 提供商限流（rate limiting）/故障？**
队列与限流（令牌桶（token bucket））、重试（retry）加退避（backoff）与抖动（jitter）、断路器、备用模型/区域、降级（只返回相关片段）、缓存、给不同优先级的请求预留配额（quota）、监控 429 和超时比例。

**Q33. 索引内存放不下怎么办？**
量化（int8、PQ）、降低维度（支持的模型）、分片、磁盘型索引、分层（热/冷）、按租户（tenant）/时间分区、去掉低价值内容、减少块数（更大的块或去重（deduplication））。实验 1 的公式先算清楚。

**Q34. 如何做到零停机重建索引？**
蓝绿（blue-green）索引 + 别名切换；构建期间的增量写入双写或回放（replay）日志；切换前评测（evaluation, or evals）；保留旧索引一段时间以便回滚（rollback）；容量上准备两份索引的余量。

**Q35. 怎么发现检索质量在退化？**
每日对固定评测集（evaluation set）跑回归（regression，含检索 recall）；线上监控零结果率、top 分数分布、点踩与重复提问率；摄入（ingestion）对账（reconciliation）；新增文档与嵌入（embedding）模型的变更纳入变更管理；对失败样本做告警（alerting）与回流。

**Q36. 热点查询很多（很多人问同样的问题）怎么优化？**
带权限范围的结果缓存；对常见问题预计算答案（并随文档更新失效）；提示缓存（prompt caching）；批量合并相同查询（请求合并 single-flight）；限流。

### G. 安全

**Q37. 文档里藏了恶意指令怎么办？**
把检索（retrieval）内容当数据：分隔符与提示约束；生成阶段不给危险工具，或敏感操作需人工确认；输出过滤和异常监控；对不可信来源标注；红队（red teaming）测试；不依赖单一防线。

**Q38. 用户让模型“把所有文档给我”或越权探测怎么办？**
权限在检索层强制，不依赖提示词（prompt）；限制单次返回的内容量和速率；对异常访问模式告警（alerting）；审计（audit）日志；对高敏感文档需要显式授权（authorization）。

**Q39. 用户要求删除自己的数据（删除权）怎么做？**
定位该用户的数据在哪些地方（源数据、块、向量、缓存（cache）、日志、备份、评测集（evaluation set））；传播删除到索引（标记删除并压缩）与缓存；日志里去标识；备份按保留周期过期；记录删除凭证（credentials）。

### H. 评估

**Q40. 你会怎么建评测集（evaluation set）？需要多少样本？**
从真实日志挑 + 专家标注 + 合成补充；先 100 到 300 个高质量样本；覆盖常见与长尾、含无答案；按切片（slice）统计；版本化；定期更新。样本量取决于要检测的差异大小：差异越小需要越多样本，指标（metrics）要报告置信区间或至少看波动。

**Q41. 离线指标好，线上用户不满意，为什么？**
评测集与真实分布不一致；评测（evaluation, or evals）没覆盖某些类型；延迟/格式/语气等非准确性因素；权限导致线上可见内容更少；知识库（knowledge base）缺内容；用户期望不同；指标定义（如忠实度（faithfulness））与用户价值不一致。需要线上指标和失败分析闭环。

**Q42. 怎么衡量一次改动是否真的有效？**
同一评测集前后对比并看显著性；按切片；线上 A/B 或影子（shadow mode）对比；注意“大模型评审”的噪声，多次运行；看失败样本变化而不只是平均分。

### I. 开放题

**Q43. 如果让你从零做 MVP，第一周做什么？**
选一个窄场景和一个数据源；简单管线（结构切块（chunking） + 混合检索（hybrid search） + 一个好模型 + 引用（citation））；先把评测集（evaluation set）和日志搭起来（20 到 50 个真实问题）；做出可用的 Demo 给真实用户看，收集失败案例；权限从第一天就设计进去，而不是后补。

**Q44. 如果用户反馈“有时答得很好，有时很糟”，你怎么办？**
分类失败案例（检索（retrieval）没找到、找到了没用上、文档本身缺失/过期、模型误解、权限）；统计占比，先解决占比最大的；读几十个具体案例；建立回归集（regression set）防止修好一个坏另一个。

**Q45. 你觉得 RAG 的未来是什么？（开放）**
可以谈：更长的上下文与提示缓存（prompt caching）改变“要不要检索”的边界；代理式（agentic）检索与工具使用（tool use）结合；更好的解析与多模态；评测（evaluation, or evals）自动化；更强的权限与治理（governance）；但**检索质量、权限与评估**这些工程基本功不会过时。（表达自己的判断即可，不必追求“正确答案”。）

---

## 十三、常见的红旗（面试官不想听到的）

1. 没有澄清问题，直接画“文档→向量库→LLM”。
2. 不谈权限，或认为“在提示词（prompt）里告诉模型不要泄露”就够了。
3. 只有向量检索（vector search），没有关键词和重排序（reranking）的讨论。
4. 没有评估：说“看看效果”，但没有评测集（evaluation set）和指标（metrics）。
5. 把向量库当整个系统；不谈摄入（ingestion）、更新、删除、重建。
6. 不做估算，或估算单位错误；看不出瓶颈（以为 QPS 是难点）。
7. 把所有技术堆上去（代理、知识图谱、微调（fine-tuning）、多路召回……），却没有说明为什么需要、代价是什么。
8. 不谈失败：没有降级、没有超时预算（budget）、没有拒答（refusal）。
9. 相信“幻觉（hallucination）可以消除”。
10. 不谈成本和延迟的取舍。
11. 回答里全是名词，没有取舍和数字。
12. 把检索（retrieval）内容当可信指令，不考虑提示注入（prompt injection）。

---

## 十四、一个 45 分钟的参考回答范本（口述提纲）

> 这是一份**提纲**，用来练习节奏；请替换成你自己的假设和经历。括号里是大致用时。

**1. 澄清（5 分钟）**
“我想先确认几件事：用户是谁、数据在哪里、规模多大、更新多快、有没有访问控制（access control）、延迟目标、是否要引用（citation）、错了的后果。（问第一部分表中的问题。）我先假设：企业内部助手，500 万篇文档，5 万名员工，有访问控制，需要引用，首个 token 两秒内。”

**2. 估算（4 分钟）**
“500 万篇、每篇约 3000 token，约 150 亿 token；512 token 一块、重叠 64，约 3350 万块。1024 维 float32 向量约 137 GB，int8 量化（quantization）约 34 GB，所以需要量化或分片（sharding）。QPS 峰值约 7，很低——瓶颈在 LLM 与内存，不在检索（retrieval）吞吐。”

**3. 架构（8 分钟）**
画两条管线 + 评估闭环（3.1 的图）；逐个组件一句话说职责与关键点。

**4. 深入（20 分钟，选三个）**
- 权限：块级 ACL、检索时过滤、进入提示词（prompt）前再校验、缓存（cache）键含权限、失败关闭（fail closed）；讲 post-filter 的问题（实验 3）。
- 检索质量：混合检索（hybrid search） + RRF、重排序（reranking，召回 50 到 100，取 5 到 10）、父子块（parent-child chunks）；ANN 选型与召回/内存取舍（实验 2）。
- 评估：检索与生成分开评估、评测集（evaluation set）来源、LLM 评审要校准（calibration）、回归门禁（regression gate）、线上指标（metrics）。
（或根据面试官兴趣：摄入（ingestion）与重建、规模与尾延迟（tail latency）、成本。）

**5. 可靠性、安全、成本（5 分钟）**
降级表（重排序/分片/LLM 失败时怎么办）；提示注入（prompt injection）；删除传播；成本主要是 LLM 输入 token，优化顺序。

**6. 总结与风险（3 分钟）**
“这个设计的核心取舍是……，主要风险是文档解析（document parsing）质量和权限同步延迟；我会先上线窄场景、搭评测集，再逐步加重排序、查询改写（query rewriting）等，每一步用评测（evaluation, or evals）证明价值。”

---

## 十五、一页纸速记与自测

**四个必须说出口（egress）的词**：**权限过滤（permission filtering）**、**混合检索（hybrid search） + 重排序（reranking）**、**评测集（evaluation set）**、**降级**。

**六个数字意识**：块数（总 token ÷ 步长）；向量内存（块数 × 维度 × 字节数）；峰值 QPS；每次提问的输入 token；延迟预算（budget）；重建一次要多久。

**自测表**（能用 2 分钟讲清的打勾）

| 主题 | 你应该能讲清 |
|---|---|
| 澄清与估算 | 问哪些问题；块数、内存、QPS、token 怎么算 |
| 摄入（ingestion） | 解析、切块（chunking）取舍、父子块（parent-child chunks）、元数据（metadata）、增量/删除/重建 |
| 检索（retrieval） | 混合检索、RRF、ANN 三角、重排序取舍、查询改写（query rewriting） |
| 权限 | 块级 ACL、pre/post-filter、缓存（cache）键、纵深防御（defense in depth）、失败关闭（fail closed） |
| 生成 | 上下文预算、引用（citation）与校验、拒答（refusal）、幻觉（hallucination）来源 |
| 规模与可靠性 | 分片（sharding）与尾延迟（tail latency）、对冲请求（hedged request）、降级、蓝绿（blue-green）重建 |
| 评估 | 检索与生成分层、评测集来源、LLM 评审校准（calibration）、回归门禁（regression gate） |
| 安全 | 间接提示注入（indirect prompt injection）、数据泄漏（data leakage）、删除权、审计（audit） |
| 变体 | 客服、代码、高精度、高频更新、多模态、多语言 |

---

## 附录 A：来源与说明

**我搜索并参考的页面**（博客和备考站，非官方标准）：

- RAG 系统设计面试：[DesignGurus：System Design for RAG](https://www.designgurus.io/blog/system-design-for-rag)、[PracHub：Designing RAG Architecture at Scale](https://prachub.com/resources/designing-rag-architecture-at-scale-an-ai-engineering-interview-guide)、[RAG System Walkthrough](https://calm-rocks.pages.dev/resources/prepare-interview/system-design/rag-system-walkthrough/)、[Design RAG Architecture](https://ailswan.github.io/poststwo/ai-a02-2026-05-25/)、[PracHub：RAG Systems And LLM Retrieval](https://prachub.com/concepts/rag-systems-and-llm-retrieval)
- 企业 RAG 权限过滤：[wavect：RAG 权限（SharePoint、Confluence、Drive）](https://wavect.io/blog/rag-permissions-sharepoint-confluence-drive/)、[DEV：你的 AI 助手可能泄露用户无权查看的文件](https://dev.to/lakhansamani/your-ai-assistant-can-leak-files-people-arent-allowed-to-see-heres-how-to-fix-it-51en)

**已验证（真实运行）**：实验 1 到 4，代码与样例输出在 `rag-system-design/code/` 和 `sample_output/`。实验 1 是公式计算，参数是假设；实验 2、3 用合成向量（hnswlib、faiss），**不是真实文本嵌入（embedding）**；实验 4 是模拟。

**未验证或需要自行核对**：
- 各向量数据库（vector database）/搜索引擎的具体功能、过滤实现、限额、价格，以及各模型服务商的提示缓存（prompt caching）、上下文长度、价格：我没有写具体数字，请对照官方文档。
- “lost in the middle”、contextual retrieval 的效果与具体数字：我只描述了思路，没有核对论文或博客里的数值。
- 备考站里的评估阈值是个人目标，不是标准。
- 这份材料里没有真实的、带日期的某公司 RAG 系统设计面经。

## 附录 B：术语表（中英对照）

按在文中第一次出现的顺序排列。

- 切块：chunking
- 嵌入：embedding
- 向量数据库：vector database
- 检索：retrieval
- 引用：citation
- 摄入：ingestion
- 访问控制：access control
- 一致性：consistency
- 混合检索：hybrid search
- 重排序：reranking
- 提示注入：prompt injection
- 可观测性：observability
- 容忍度：tolerance
- 工单：ticket
- 连接器：connector
- 分片：sharding
- 量化：quantization
- 增量同步：incremental sync
- 流式：streaming
- 缓存：cache
- 查询改写：query rewriting
- 权限过滤：permission filtering
- 拒答：refusal
- 记忆：memory
- 分词：tokenization
- 多租户：multi-tenancy
- 租户：tenant
- 合规：compliance
- 数据驻留：data residency
- 审计：audit
- 指标：metrics
- 副本：replica
- 对象存储：object storage
- 预算：budget
- 交叉编码器：cross-encoder
- 认证：authentication
- 父子块：parent-child chunks
- 版本号：version number
- 限流：rate limiting
- 重试：retry
- 元数据：metadata
- 路由：routing
- 提示词：prompt
- 去重：deduplication
- 护栏：guardrails
- 离线评测：offline evaluation
- 评测：evaluation, or evals
- 追踪：trace
- 服务账号：ServiceAccount
- 分页：pagination
- 灰度：canary release
- 评测集：evaluation set
- 退避：backoff
- 微调：fine-tuning
- 墓碑：tombstone
- 蓝绿：blue-green
- 回滚：rollback
- 事务：transaction
- 召回率：recall
- 稠密检索：dense retrieval
- 近似最近邻：ANN, approximate nearest neighbor
- 向量检索：vector search
- 同义词：synonym
- 双塔：bi-encoder
- 代理式：agentic
- 知识库：knowledge base
- 纵深防御：defense in depth
- 授权：authorization
- 语义缓存：semantic cache
- 租户隔离：tenant isolation
- 命名空间：namespace
- 吵闹邻居：noisy neighbor
- 系统提示：system prompt
- 幻觉：hallucination
- 校准：calibration
- 提示缓存：prompt caching
- 模型路由：model routing
- 并发：concurrency
- 尾延迟：tail latency
- 扇出：fan-out
- 对冲请求：hedged request
- 抖动：jitter
- 背压：backpressure
- 消息队列：message queue
- 幂等：idempotency
- 幂等键：idempotency key
- 死信队列：dead-letter queue
- 告警：alerting
- 重放：replay
- 对账：reconciliation
- 忠实度：faithfulness
- 脱敏：data masking
- 多跳：multi-hop
- 切片：slice
- 回归集：regression set
- 位置偏差：position bias
- 人工标注：human annotation
- 影子：shadow mode
- A/B 测试：A/B testing
- 最小权限：least privilege
- 致命三要素：lethal trifecta
- 确定性：deterministic
- 失败关闭：fail closed
- 评审模型：judge model
- 测试集：test set
- 冷启动：cold start
- 令牌桶：token bucket
- 配额：quota
- 回归：regression
- 红队：red teaming
- 凭证：credentials
- 工具使用：tool use
- 治理：governance
- 回归门禁：regression gate
- 文档解析：document parsing
- 出口：egress
- 间接提示注入：indirect prompt injection
- 数据泄漏：data leakage
