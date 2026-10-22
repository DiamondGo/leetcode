"""第 11 章：护栏写在运行时里，而不是写在提示词里。
包含：预算、重复调用检测、风险分级、与参数绑定的审批。
"""
import hashlib
import json


class Blocked(Exception):
    pass


RISK = {"get_order": "read", "refund": "write_high"}


def args_hash(name, args):
    return hashlib.sha256(json.dumps([name, args], sort_keys=True).encode()).hexdigest()[:12]


class Guard:
    def __init__(self, max_steps=8, max_cost=1.0, max_repeat=2):
        self.max_steps, self.max_cost, self.max_repeat = max_steps, max_cost, max_repeat
        self.steps, self.cost, self.seen = 0, 0.0, {}
        self.approvals = set()                           # 存的是"被批准的具体调用"的哈希

    def approve(self, name, args):
        """人工审批：批准的是"这个工具 + 这组参数"，不是"以后随便用"。"""
        self.approvals.add(args_hash(name, args))

    def check(self, name, args, step_cost=0.05):
        self.steps += 1
        self.cost += step_cost
        if self.steps > self.max_steps:
            raise Blocked("超过步数上限")
        if self.cost > self.max_cost:
            raise Blocked("超过费用预算")
        h = args_hash(name, args)
        self.seen[h] = self.seen.get(h, 0) + 1
        if self.seen[h] > self.max_repeat:               # 同一个调用重复太多次 = 无进展
            raise Blocked(f"检测到重复调用 {name}{args}（第{self.seen[h]}次）")
        if RISK.get(name) == "write_high" and h not in self.approvals:
            raise Blocked(f"高风险操作 {name}{args} 需要人工审批")


if __name__ == "__main__":
    g = Guard()
    print("== 重复调用检测 ==")
    try:
        for i in range(5):
            g.check("get_order", {"order_id": 1001})
            print(f"  第{i+1}次 get_order 放行")
    except Blocked as e:
        print("  被拦截：", e)

    print("== 高风险操作 ==")
    g = Guard()
    try:
        g.check("refund", {"order_id": 1001, "amount": 300})
    except Blocked as e:
        print("  未审批：", e)
    g.approve("refund", {"order_id": 1001, "amount": 300})
    g.check("refund", {"order_id": 1001, "amount": 300})
    print("  审批后同一调用放行")
    try:
        g.check("refund", {"order_id": 1001, "amount": 30000})     # 模型想把金额改大
    except Blocked as e:
        print("  金额被改动，审批不适用：", e)

    print("== 预算 ==")
    g = Guard(max_cost=0.12)
    try:
        for i in range(10):
            g.check("get_order", {"order_id": i})
    except Blocked as e:
        print("  被拦截：", e, f"（已花费约 {g.cost:.2f}）")
