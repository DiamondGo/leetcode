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
