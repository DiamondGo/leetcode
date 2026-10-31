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
