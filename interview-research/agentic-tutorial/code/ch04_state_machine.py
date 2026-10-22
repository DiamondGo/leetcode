"""第 4 章：把流程写成显式状态机。LLM 只负责"理解"，状态转移由代码裁决：非法转移会被拒绝，重复事件不会重复推进。"""

# 允许的转移表：(当前状态, 事件) -> 下一个状态
TRANSITIONS = {
    ("RECEIVED", "verified"): "VERIFIED",
    ("VERIFIED", "needs_approval"): "AWAITING_APPROVAL",
    ("VERIFIED", "auto_approved"): "REFUNDING",
    ("AWAITING_APPROVAL", "approved"): "REFUNDING",
    ("AWAITING_APPROVAL", "rejected"): "FAILED",
    ("REFUNDING", "refunded"): "DONE",
    ("REFUNDING", "refund_failed"): "FAILED",
}
TERMINAL = {"DONE", "FAILED"}


class InvalidTransition(Exception):
    pass


class RefundRun:
    def __init__(self, amount):
        self.state, self.amount = "RECEIVED", amount
        self.history, self.seen_events = [], set()

    def advance(self, event_id, event):
        """event_id 用来保证幂等：同一个事件被重复投递，只生效一次。"""
        if event_id in self.seen_events:
            return self.state
        key = (self.state, event)
        if key not in TRANSITIONS:
            raise InvalidTransition(f"状态 {self.state} 不允许事件 {event}")
        self.seen_events.add(event_id)
        self.history.append((self.state, event, TRANSITIONS[key]))
        self.state = TRANSITIONS[key]
        return self.state


def decide_after_verify(run, limit=100):
    """守卫条件（guard）：金额不超过阈值自动批准，否则必须人工审批。"""
    return "auto_approved" if run.amount <= limit else "needs_approval"


if __name__ == "__main__":
    run = RefundRun(amount=300)
    run.advance("e1", "verified")
    run.advance("e2", decide_after_verify(run))
    print("金额 300 -> 当前状态：", run.state)

    run.advance("e3", "approved")
    run.advance("e3", "approved")           # 消息被重复投递：不会重复推进
    print("重复投递 approved 后：", run.state)

    try:
        run.advance("e4", "verified")       # 非法转移：REFUNDING 状态下不能再 verified
    except InvalidTransition as e:
        print("拒绝非法转移：", e)

    run.advance("e5", "refunded")
    print("最终状态：", run.state, "| 历史：")
    for h in run.history:
        print("  ", h)
