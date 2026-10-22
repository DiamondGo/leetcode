"""第 2 章：工具——模型只"提议"，运行时负责校验和执行；错误作为结果返回，让模型有机会自我纠正。"""
import json

ORDERS = {1001: {"id": 1001, "status": "已发货"}}


def get_order(order_id):
    if order_id not in ORDERS:
        raise LookupError(f"订单 {order_id} 不存在")
    return ORDERS[order_id]


# 工具规格：名称、参数类型、描述（给模型看）。真实系统里通常是 JSON Schema。
SPEC = {
    "get_order": {"params": {"order_id": int}, "fn": get_order,
                  "doc": "按订单编号查询订单状态。order_id 必须是整数。"},
}


def validate(name, args):
    """执行前校验：不信任模型给的参数。"""
    if name not in SPEC:
        return [f"未知工具 {name}，可用工具：{list(SPEC)}"]
    errors, params = [], SPEC[name]["params"]
    for p, typ in params.items():
        if p not in args:
            errors.append(f"缺少参数 {p}")
        elif not isinstance(args[p], typ):
            errors.append(f"参数 {p} 应为 {typ.__name__}，收到 {type(args[p]).__name__}")
    errors += [f"多余参数 {k}" for k in args if k not in params]
    return errors


def execute(name, args):
    """永远返回结构化结果，不向上抛异常：错误信息本身就是给模型的反馈。"""
    errors = validate(name, args)
    if errors:
        return {"ok": False, "error": "；".join(errors)}
    try:
        return {"ok": True, "data": SPEC[name]["fn"](**args)}
    except Exception as e:                        # 工具内部失败也变成可读的结果
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


# ---- 假模型：第一次给错参数类型，看到错误信息后修正 ----
def fake_model(messages):
    tool_msgs = [m for m in messages if m["role"] == "tool"]
    if not tool_msgs:
        return {"role": "assistant", "tool_call": {"id": "c1", "name": "get_order",
                                                    "args": {"order_id": "1001"}}}   # 故意写成字符串
    last = json.loads(tool_msgs[-1]["content"])
    if not last["ok"]:
        return {"role": "assistant", "tool_call": {"id": "c2", "name": "get_order",
                                                    "args": {"order_id": 1001}}}     # 读懂错误后修正
    return {"role": "assistant", "content": f"订单状态：{last['data']['status']}"}


def run_agent(task, model, max_steps=6, max_consecutive_errors=2):
    messages, errors_in_row = [{"role": "user", "content": task}], 0
    for step in range(1, max_steps + 1):
        reply = model(messages)
        messages.append(reply)
        call = reply.get("tool_call")
        if not call:
            return reply["content"]
        result = execute(call["name"], call["args"])
        print(f"  第{step}步 调用 {call['name']}({call['args']}) -> {result}")
        errors_in_row = 0 if result["ok"] else errors_in_row + 1
        if errors_in_row > max_consecutive_errors:      # 自纠错必须有上限，否则就是死循环
            return "多次失败，转人工处理"
        messages.append({"role": "tool", "id": call["id"],
                         "content": json.dumps(result, ensure_ascii=False)})
    return "超出步数上限"


if __name__ == "__main__":
    print(run_agent("订单 1001 到哪了？", fake_model))
    print("-- 不存在的订单 --")
    print(execute("get_order", {"order_id": 9999}))
