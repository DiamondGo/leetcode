"""第 6 章：有副作用的操作为什么需要幂等键。
场景：智能体调用支付接口扣款，扣款成功了，但在保存结果之前进程崩溃，重启后重试。
"""
import uuid


class PaymentProvider:
    """模拟外部支付系统。支持幂等键：同一个键只会真正扣一次款。"""
    def __init__(self):
        self.charges, self.seen = [], {}

    def charge(self, amount, idem_key=None):
        if idem_key is not None and idem_key in self.seen:
            return self.seen[idem_key]                 # 重复请求：直接返回第一次的结果
        self.charges.append(amount)
        result = {"charge_id": f"ch_{len(self.charges)}", "amount": amount}
        if idem_key is not None:
            self.seen[idem_key] = result
        return result


class Crash(Exception):
    pass


def agent_step(provider, amount, key_fn, crash_first_time, attempt):
    """一步：扣款 -> （崩溃点）-> 保存结果。崩溃发生在"已扣款但未保存"之间。"""
    result = provider.charge(amount, idem_key=key_fn(attempt))
    if crash_first_time and attempt == 1:
        raise Crash("进程在保存结果前崩溃")
    return result


def run_with_retry(provider, key_fn):
    for attempt in (1, 2):
        try:
            return agent_step(provider, 100, key_fn, crash_first_time=True, attempt=attempt)
        except Crash:
            continue


if __name__ == "__main__":
    # A. 不用幂等键：崩溃后重试 -> 重复扣款
    p = PaymentProvider()
    run_with_retry(p, key_fn=lambda attempt: None)
    print(f"A 无幂等键          : 实际扣款 {len(p.charges)} 次 {p.charges}")

    # B. 每次尝试都生成新的随机键：等于没有（常见的错误做法）
    p = PaymentProvider()
    run_with_retry(p, key_fn=lambda attempt: str(uuid.uuid4()))
    print(f"B 每次重试换新随机键: 实际扣款 {len(p.charges)} 次 {p.charges}")

    # C. 键由业务意图决定，且在重试之间保持不变
    p = PaymentProvider()
    run_with_retry(p, key_fn=lambda attempt: "order-1001:charge")
    print(f"C 稳定的幂等键      : 实际扣款 {len(p.charges)} 次 {p.charges}")
