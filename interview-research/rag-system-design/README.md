# 系统设计面试：设计一个 RAG 系统

- `rag-system-design-interview.md`：正文（澄清问题、规模估算、总体架构、摄入、检索、权限、生成、规模与可靠性、评估、安全、9 个变体题、45 道追问题与参考答案、红旗清单、45 分钟答题范本）
- `code/`：4 个实验
  - `capacity.py`：容量估算（公式，参数为假设）
  - `ann_tradeoffs.py`：HNSW / int8 量化 / IVF-PQ 的召回、延迟、内存取舍（合成向量）。依赖：`pip install numpy hnswlib faiss-cpu`
  - `acl_filtering.py`：权限过滤：post-filter 与 in-index filter 与精确搜索可见子集（合成向量）。依赖同上
  - `tail_latency.py`：分片扇出的尾延迟放大与缓解（模拟，只需 numpy）
- `sample_output/`：我运行时的输出（耗时每次不同；召回等由固定随机种子决定）

说明：实验 2、3 用合成向量，不是真实文本嵌入，只看趋势；各向量库与模型服务的具体功能、限额、价格没有写，需对照官方文档。详见正文附录 A。
