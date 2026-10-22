"""第 1 章：最小的智能体循环。
用脚本化的"假模型"代替真实 LLM，所以不需要 API key，结果完全可复现。
真实系统里，fake_model 这一处换成一次 LLM 调用，其余结构不变。
"""
import json


class MaxStepsExceeded(Exception):
    pass


# ---- 假模型：根据对话内容决定下一步（真实系统里这里是 LLM 调用）----
def fake_model(messages):
    last = messages[-1]
    if last["role"] == "user":                      # 刚收到问题 -> 先去查订单
        return {"role": "assistant",
                "tool_call": {"id": "c1", "name": "get_order", "args": {"order_id": 1001}}}
    if last["role"] == "tool":                      # 拿到工具结果 -> 给出最终回答
        order = json.loads(last["content"])
        return {"role": "assistant", "content": f"订单 {order['id']} 的状态是：{order['status']}。"}
    raise ValueError("unexpected message")


def broken_model(messages):
    """永远不收手的模型：用来演示为什么必须有步数上限。"""
    return {"role": "assistant",
            "tool_call": {"id": "c", "name": "get_order", "args": {"order_id": 1001}}}


# ---- 工具 ----
ORDERS = {1001: {"id": 1001, "status": "已发货"}}


def get_order(order_id):
    return ORDERS[order_id]


TOOLS = {"get_order": get_order}


# ---- 循环本身：整个"智能体"其实就这几行 ----
def run_agent(task, model, tools, max_steps=5):
    messages = [{"role": "user", "content": task}]
    for step in range(1, max_steps + 1):
        reply = model(messages)                      # 1) 让模型决定下一步
        messages.append(reply)
        call = reply.get("tool_call")
        if not call:                                 # 2) 没有工具调用 = 模型认为做完了
            return reply["content"], step
        result = tools[call["name"]](**call["args"])  # 3) 由"运行时"（不是模型）执行工具
        messages.append({"role": "tool", "id": call["id"],
                         "content": json.dumps(result, ensure_ascii=False)})  # 4) 结果喂回去
    raise MaxStepsExceeded(f"超过 {max_steps} 步仍未结束")


if __name__ == "__main__":
    answer, steps = run_agent("订单 1001 到哪了？", fake_model, TOOLS)
    print(f"[正常] {answer}（用了 {steps} 步）")
    try:
        run_agent("订单 1001 到哪了？", broken_model, TOOLS)
    except MaxStepsExceeded as e:
        print(f"[失控] 被步数上限拦住：{e}")
