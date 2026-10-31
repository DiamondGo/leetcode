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
