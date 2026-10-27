"""实验 9：HPA 扩缩容公式、滚动更新的 maxSurge/maxUnavailable、CrashLoopBackOff 的退避时间。
纯 Python 模拟，按 Kubernetes 文档描述的公式实现（教学模型，不连集群）：
  HPA：desired = ceil(current × 当前指标 / 目标指标)；比值在 1±0.1 内不动（tolerance）；
       缩容取过去 5 分钟（stabilization window）内算出的最大值，防止抖动；每 15 秒同步一次。
  滚动更新：maxSurge 向上取整，maxUnavailable 向下取整；默认都是 25%。
  CrashLoopBackOff：重启延迟 10s、20s、40s…… 翻倍，上限 5 分钟。
"""
import math


def hpa(current, metric, target, tol=0.1):
    ratio = metric / target
    if abs(ratio - 1) <= tol:
        return current
    return math.ceil(current * ratio)


print("=== A. HPA：目标 CPU 利用率 60%，当前 4 个副本 ===")
for m in (50, 63, 66, 90, 120, 30):
    print(f"  当前平均利用率 {m:>3}% -> 期望副本 {hpa(4, m, 60)}")
print("  （63% 比值 1.05，落在容忍范围内不动；50% 算出 ceil(3.33)=4，向上取整所以还是 4；利用率是相对 **requests** 算的，没设 requests 就没法用）")

print("\n=== B. 缩容稳定窗口：流量尖峰过去后，副本不会立刻缩回去 ===")
load = [90] * 4 + [30] * 28   # 每步 15 秒；先高负载 1 分钟，然后骤降
replicas, history, window = 4, [], 20     # 窗口按 20 步（5 分钟）
trace = []
for t, m in enumerate(load):
    total_load = m * 4          # 总负载固定；平均利用率 = 总负载 / 副本数
    util = total_load / replicas
    raw = hpa(replicas, util, 60)
    history.append(raw)
    if raw < replicas:
        replicas = max(history[-window:])      # 缩容取窗口内最大值
    else:
        replicas = raw
    trace.append(replicas)
print("  每 15 秒一步，副本数:", trace)
print(f"  负载骤降后第 {next(i for i, r in enumerate(trace) if i >= 4 and r < max(trace)) * 15 - 60} 秒才开始缩容（稳定窗口约 300 秒）")


def surge_unavail(replicas, surge="25%", unavail="25%"):
    f = lambda x, up: (math.ceil if up else math.floor)(replicas * float(x[:-1]) / 100) if str(x).endswith("%") else int(x)
    s, u = f(surge, True), f(unavail, False)
    return s, u


print("\n=== C. 滚动更新 ===")
for n, sg, un in ((10, "25%", "25%"), (3, "25%", "25%"), (4, "25%", "25%"), (10, "0", "1"), (10, "100%", "0")):
    s, u = surge_unavail(n, sg, un)
    if s == 0 and u == 0:
        print(f"  replicas={n}: 不合法，两者不能同时为 0")
        continue
    print(f"  replicas={n:<2} maxSurge={sg:<4} maxUnavailable={un:<4} -> 最多同时 {n + s} 个，至少 {n - u} 个可用")
print("  （只有 readiness 通过的新 Pod 才算“可用”：readiness 写错会让滚动更新卡住；"
      "maxUnavailable=0 + 一个永远不 Ready 的新版本 = 旧版本继续服务，更新停在中间，这是好事。）")

print("\n=== D. CrashLoopBackOff 重启间隔 ===")
d, t, seq = 10, 0, []
for i in range(8):
    seq.append(d); t += d; d = min(d * 2, 300)
print("  第 1~8 次重启前等待（秒）:", seq, f"累计 {t}s")
print("  （容器稳定运行一段时间后退避会重置。CrashLoopBackOff 只是“反复崩溃”的状态，不是原因；"
      "先看 kubectl describe pod 的 Last State 和 exit code，再看 kubectl logs --previous。）")
