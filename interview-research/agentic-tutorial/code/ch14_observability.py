"""第 14 章：可观测性。一次运行 = 一条 trace，每次模型/工具调用 = 一个 span，并统计 token 与费用。
最后用 trace 自动发现"疑似循环"。时间用假时钟，输出可复现。
"""
import contextvars
import json

PRICE_PER_1K = {"input": 0.003, "output": 0.015}          # 假定价格（美元 / 1000 token），仅演示
_current = contextvars.ContextVar("current_span", default=None)
SPANS, CLOCK = [], {"t": 0.0}


class span:
    """上下文管理器：自动记录开始/结束时间、父子关系和属性。"""
    def __init__(self, name, **attrs):
        self.rec = {"id": len(SPANS) + 1, "parent": None, "name": name, "attrs": attrs}

    def __enter__(self):
        self.rec["parent"] = (_current.get() or {}).get("id")
        self.rec["start"] = CLOCK["t"]
        SPANS.append(self.rec)
        self.token = _current.set(self.rec)
        return self.rec

    def __exit__(self, *exc):
        self.rec["end"] = CLOCK["t"]
        _current.reset(self.token)


def llm_call(step, tokens_in, tokens_out, secs):
    with span("llm", step=step, tokens_in=tokens_in, tokens_out=tokens_out) as s:
        CLOCK["t"] += secs
        s["attrs"]["cost"] = round(tokens_in / 1000 * PRICE_PER_1K["input"] + tokens_out / 1000 * PRICE_PER_1K["output"], 5)


def tool_call(name, args, secs):
    with span("tool", tool=name, args=json.dumps(args, sort_keys=True)):
        CLOCK["t"] += secs


def simulated_run():
    """一次"有问题"的运行：智能体反复用同一个参数查订单，陷入循环。"""
    with span("run", run_id="r-42", tenant="acme"):
        for step in range(1, 6):
            llm_call(step, tokens_in=1200 + step * 600, tokens_out=60, secs=1.1)
            tool_call("get_order", {"order_id": 1001}, 0.3)


def analyse(spans):
    print("== 调用树 ==")
    depth = {}
    for s in spans:
        depth[s["id"]] = 0 if s["parent"] is None else depth[s["parent"]] + 1
        dur = s["end"] - s["start"]
        a = s["attrs"]
        extra = f"cost=${a['cost']}" if "cost" in a else (f"{a['tool']} {a['args']}" if "tool" in a else "")
        print(f"{'  ' * depth[s['id']]}{s['name']:<4} {dur:>4.1f}s {extra}")
    total_cost = sum(s["attrs"].get("cost", 0) for s in spans)
    total_in = sum(s["attrs"].get("tokens_in", 0) for s in spans)
    wall = max(s["end"] for s in spans) - min(s["start"] for s in spans)
    print(f"== 汇总 == 耗时 {wall:.1f}s | 输入 token {total_in} | 费用 ${total_cost:.4f}")
    llm_t = sum(s["end"] - s["start"] for s in spans if s["name"] == "llm")
    print(f"   延迟构成：模型 {llm_t:.1f}s / 工具 {wall - llm_t:.1f}s")
    calls = {}
    for s in spans:
        if s["name"] == "tool":
            key = (s["attrs"]["tool"], s["attrs"]["args"])
            calls[key] = calls.get(key, 0) + 1
    for (tool, args), n in calls.items():
        if n >= 3:
            print(f"   [告警] 疑似循环：{tool} {args} 被重复调用 {n} 次，输入 token 随步数增长")


if __name__ == "__main__":
    simulated_run()
    analyse(SPANS)
