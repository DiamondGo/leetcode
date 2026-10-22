"""第 8 章：长时间等待与人工审批。工作流挂起时不占用任何进程；几天后收到审批信号，再从日志恢复继续。"""
import os
import tempfile

from durable import Journal, Runner


class Refunds:
    def __init__(self):
        self.drafted, self.executed = 0, 0

    def draft(self, order, idem_key=None):
        self.drafted += 1
        return {"order": order, "amount": 300}

    def execute(self, order, idem_key=None):
        self.executed += 1
        return f"已对 {order} 退款"


def refund_workflow(ctx, svc, order):
    draft = ctx.activity("draft_refund", svc.draft, order)      # 先由智能体起草（含一次模型调用）
    decision = ctx.wait_signal("approval")                      # 没有信号就挂起，不占进程
    if not decision["approved"]:
        return "审批被拒绝，流程结束"
    ctx.activity("execute_refund", svc.execute, order)
    return f"退款 {draft['amount']} 元已完成"


if __name__ == "__main__":
    path = os.path.join(tempfile.mkdtemp(), "journal.db")
    svc = Refunds()

    status, result, ctx = Runner(Journal(path)).run(refund_workflow, "run-9", svc, "A1001")
    print(f"第1次运行：{status}，实际执行的步骤：{ctx.executed}")
    print("……（进程退出，几天过去，没有任何进程在等待）……")

    r = Runner(Journal(path))                                    # 全新的进程
    status, _, _ = r.run(refund_workflow, "run-9", svc, "A1001")
    print(f"审批前再次运行：{status}（仍在等待，起草步骤没有被重复执行：drafted={svc.drafted}）")

    r.signal("run-9", "approval", {"approved": True, "by": "alice"})
    status, result, ctx = r.run(refund_workflow, "run-9", svc, "A1001")
    print(f"收到审批后：{status}，结果：{result}")
    print(f"本次进程实际执行的步骤：{ctx.executed} | 起草 {svc.drafted} 次，退款 {svc.executed} 次")
