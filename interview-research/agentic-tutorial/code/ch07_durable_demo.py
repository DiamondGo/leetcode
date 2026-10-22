"""第 7 章：崩溃恢复演示。用 durable.py 跑一个"订单智能体"工作流，在最危险的位置制造崩溃。"""
import os
import tempfile

from durable import Crash, Journal, Runner


class Service:
    """模拟一个外部系统。calls 统计"真正生效"的次数；dedupe=True 表示它支持幂等键。"""
    def __init__(self, name, dedupe=True):
        self.name, self.dedupe, self.calls, self.seen = name, dedupe, 0, {}

    def do(self, payload, idem_key=None):
        if self.dedupe and idem_key in self.seen:
            return self.seen[idem_key]
        self.calls += 1
        self.seen[idem_key] = f"{self.name} 完成（第{self.calls}次真正执行）"
        return self.seen[idem_key]


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def plan(self, order, idem_key=None):
        self.calls += 1                      # 统计真实的模型调用次数（钱和延迟都花在这里）
        return {"steps": ["reserve", "charge", "email"]}


def order_workflow(ctx, svc, order):
    ctx.activity("llm_plan", svc["llm"].plan, order)         # 模型输出被记录进日志，回放时不会重新调用
    ctx.activity("reserve", svc["inventory"].do, f"reserve {order}")
    ctx.activity("charge", svc["payment"].do, f"charge {order}")     # seq=2
    ctx.activity("email", svc["mail"].do, f"email {order}")
    return "订单处理完成"


def scenario(title, payment_supports_idempotency):
    print(f"\n=== {title} ===")
    path = os.path.join(tempfile.mkdtemp(), "journal.db")
    svc = {"llm": FakeLLM(), "inventory": Service("库存"),
           "payment": Service("支付", dedupe=payment_supports_idempotency), "mail": Service("邮件")}

    # 第一次运行：在 charge 已经执行、但结果还没写入日志时崩溃
    try:
        Runner(Journal(path), crash_points={(2, "after")}).run(order_workflow, "run-1", svc, "A1001")
    except Crash as e:
        print("第一次运行：", e)

    # "进程重启"：新的 Journal 连接、新的 Runner，用同一个 run_id 继续
    status, result, ctx = Runner(Journal(path)).run(order_workflow, "run-1", svc, "A1001")
    print("第二次运行：", status, "|", result, "| 本次进程实际执行的步骤：", ctx.executed)
    print(f"模型调用 {svc['llm'].calls} 次 | 库存 {svc['inventory'].calls} 次 | "
          f"支付 {svc['payment'].calls} 次 | 邮件 {svc['mail'].calls} 次")


if __name__ == "__main__":
    scenario("场景 A：支付系统支持幂等键", payment_supports_idempotency=True)
    scenario("场景 B：支付系统不支持幂等键", payment_supports_idempotency=False)
