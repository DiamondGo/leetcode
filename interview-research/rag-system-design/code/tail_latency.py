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
