"""第 10 章：评测。把"感觉不错"变成统计证据。
包含：多次运行的 pass@k / pass^k、置信区间、LLM 评审员的校准（准确率与 Cohen's kappa）、回归对比。
这里用"假智能体"和"假评审员"，目的是理解指标本身，不依赖任何模型。
"""
import math
import random


def wilson(successes, n, z=1.96):
    """比例的 Wilson 置信区间：样本小时比"均值±误差"可靠。"""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(centre - half, 3), round(centre + half, 3))


def run_trials(task_success_prob, k, seed):
    """每个任务独立跑 k 次，返回每个任务的成功次数。"""
    rng = random.Random(seed)
    return [sum(rng.random() < p for _ in range(k)) for p in task_success_prob]


def metrics(successes_per_task, k):
    n = len(successes_per_task)
    return {
        "单次成功率": round(sum(successes_per_task) / (n * k), 3),
        f"pass@{k}（至少一次成功）": round(sum(s >= 1 for s in successes_per_task) / n, 3),
        f"pass^{k}（全部成功）": round(sum(s == k for s in successes_per_task) / n, 3),
    }


def cohen_kappa(a, b):
    """评审员与人工标签的一致性，扣除"碰巧一致"的部分。"""
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return round((po - pe) / (1 - pe), 3) if pe != 1 else 1.0


if __name__ == "__main__":
    # 30 个任务：大多数较容易，少数较难
    probs = [0.95] * 18 + [0.8] * 8 + [0.4] * 4
    k = 8

    print("== 1) 单次成功率高，不代表可靠 ==")
    for name, pr in (("版本 A", probs), ("版本 B（改了提示词）", [min(1, p + 0.03) for p in probs])):
        s = run_trials(pr, k, seed=7)
        print(name, metrics(s, k), "单次成功率 95% 区间", wilson(sum(s), len(s) * k))

    print("\n== 2) 样本量与置信区间：同样 90% 的成功率 ==")
    for n in (10, 100, 1000):
        print(f"n={n:<5} 成功 {int(0.9 * n):>3} 次 -> 95% 区间 {wilson(int(0.9 * n), n)}")

    print("\n== 3) 评审员要先校准：它和人工一致吗？有没有偏好长回答？ ==")
    rng = random.Random(3)
    items = []                                           # (回答长度, 人工是否认为合格)
    for _ in range(200):
        length = rng.choice([50, 400])
        good = rng.random() < 0.5                         # 质量与长度无关
        items.append((length, good))

    jrng = random.Random(9)

    def judge(length, good):                              # 假评审员：有噪声，而且偏爱长回答
        score = (0.75 if good else 0.25) + (0.25 if length > 200 else -0.25) + jrng.gauss(0, 0.2)
        return score > 0.5

    human = [g for _, g in items]
    llm = [judge(l, g) for l, g in items]
    acc = sum(h == j for h, j in zip(human, llm)) / len(items)
    print(f"准确率 {acc:.2f}，kappa {cohen_kappa(human, llm)}")
    for name, cond in (("短回答", lambda l: l < 200), ("长回答", lambda l: l >= 200)):
        sub = [(h, j) for (l, _), h, j in zip(items, human, llm) if cond(l)]
        print(f"  {name}: 准确率 {sum(h == j for h, j in sub) / len(sub):.2f}，"
              f"评审员判\"合格\"的比例 {sum(j for _, j in sub) / len(sub):.2f}（人工 {sum(h for h, _ in sub) / len(sub):.2f}）")

    print("\n== 4) 回归门禁：新版本是否真的更差？（配对比较同一批任务）==")
    base = run_trials(probs, k, seed=11)
    cand = run_trials([max(0, p - 0.05) for p in probs], k, seed=12)     # 新版本其实略差
    diffs = [(c - b) / k for b, c in zip(base, cand)]
    rng = random.Random(5)
    boots = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(2000))
    lo, hi = boots[50], boots[1949]
    print(f"平均变化 {sum(diffs) / len(diffs):+.3f}，95% 区间 [{lo:+.3f}, {hi:+.3f}]")
    print("结论：", "区间包含 0，差异不显著，不能据此下结论" if lo <= 0 <= hi else "差异显著")
