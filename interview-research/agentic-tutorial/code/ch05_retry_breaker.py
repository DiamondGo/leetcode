"""第 5 章：失败是常态。退避与抖动（为什么"立刻重试"会让事故变大）、超时预算、熔断器。
全部用"假时钟"模拟，不需要真的等待，结果可复现。
"""
import random


# ---------- 1. 指数退避 + 抖动 ----------
def delays(attempts, base=0.1, cap=5.0, jitter=True, rng=None):
    """第 n 次重试前等待多久。jitter=True 用"完全抖动"：在 [0, 上限] 内随机取值。"""
    out = []
    for n in range(attempts):
        upper = min(cap, base * (2 ** n))
        out.append(rng.uniform(0, upper) if jitter else upper)
    return out


def peak_load(n_clients, attempts, jitter, bucket=0.1, seed=1):
    """服务在 t=0 故障，1000 个客户端同时失败后各自重试；统计任意 100ms 时间桶里的最大请求数。"""
    rng = random.Random(seed)
    buckets = {}
    for _ in range(n_clients):
        t = 0.0
        for d in delays(attempts, base=0.5, jitter=jitter, rng=rng):
            t += d
            buckets[int(t / bucket)] = buckets.get(int(t / bucket), 0) + 1
    return max(buckets.values())


# ---------- 2. 带截止时间的重试：只重试"可重试"的错误 ----------
class Retryable(Exception):
    pass


def call_with_retry(fn, max_attempts=4, deadline=2.0, rng=None):
    """deadline 是整个调用的总预算（假时钟下用累计的等待时间代替），超了就别再试了。"""
    rng = rng or random.Random(0)
    waited, last = 0.0, None
    for n in range(max_attempts):
        try:
            return fn(), n + 1, round(waited, 2)
        except Retryable as e:                     # 只有可重试错误才重试；参数错误等不该重试
            last = e
            wait = delays(n + 1, jitter=True, rng=rng)[-1]
            if waited + wait > deadline:
                break
            waited += wait
    raise last


# ---------- 3. 熔断器 ----------
class CircuitBreaker:
    """CLOSED(正常) -> 连续失败达到阈值 -> OPEN(快速失败) -> 冷却后 HALF_OPEN(放一个探测请求) -> 成功则 CLOSED。"""
    def __init__(self, threshold=3, reset_after=10.0, clock=lambda: 0.0):
        self.threshold, self.reset_after, self.clock = threshold, reset_after, clock
        self.state, self.fails, self.opened_at = "CLOSED", 0, 0.0

    def call(self, fn):
        if self.state == "OPEN":
            if self.clock() - self.opened_at >= self.reset_after:
                self.state = "HALF_OPEN"
            else:
                raise RuntimeError("熔断中：快速失败，不去打已经不健康的下游")
        try:
            result = fn()
        except Exception:
            self.fails += 1
            if self.state == "HALF_OPEN" or self.fails >= self.threshold:
                self.state, self.opened_at = "OPEN", self.clock()
            raise
        self.state, self.fails = "CLOSED", 0
        return result


if __name__ == "__main__":
    print("== 1) 1000 个客户端同时重试，任意 100ms 内的最大请求数 ==")
    print("无抖动：", peak_load(1000, 5, jitter=False))
    print("有抖动：", peak_load(1000, 5, jitter=True))

    print("== 2) 带预算的重试 ==")
    state = {"n": 0}

    def flaky():
        state["n"] += 1
        if state["n"] < 3:
            raise Retryable("503")
        return "ok"
    print("结果(返回值, 尝试次数, 累计等待秒)：", call_with_retry(flaky))

    print("== 3) 熔断器 ==")
    now = {"t": 0.0}
    cb = CircuitBreaker(threshold=3, reset_after=10.0, clock=lambda: now["t"])

    def down():
        raise ConnectionError("下游挂了")
    for i in range(5):
        try:
            cb.call(down)
        except Exception as e:
            print(f"  请求{i+1}: 状态={cb.state} 错误={type(e).__name__}: {e}")
    now["t"] = 11.0
    print("  冷却 11 秒后探测一次（下游已恢复）：", cb.call(lambda: "恢复"), "-> 状态", cb.state)
