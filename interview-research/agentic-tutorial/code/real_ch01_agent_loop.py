"""第 1 章（真实模型版）：用 Anthropic SDK 写一个能真正调用 Claude 的智能体循环。

运行前：pip install anthropic，并设置环境变量 ANTHROPIC_API_KEY。
注意：这个文件会真实调用 API，会产生费用，所以故意不叫 ch*.py，run_all.py 不会运行它。
"""
import json

import anthropic

client = anthropic.Anthropic()                 # 自动从环境变量 ANTHROPIC_API_KEY 读取密钥
MODEL = "claude-opus-5-5"                      # 想省钱可以换成别的模型 ID

# ---- 1. 工具：一个真正的 Python 函数 + 一份告诉模型"怎么用它"的说明 ----
ORDERS = {1001: {"status": "已发货", "carrier": "顺丰"}, 1002: {"status": "待付款", "carrier": None}}


def get_order(order_id):
    return ORDERS[order_id]                    # 订单不存在会抛 KeyError——正好演示"错误作为结果返回"


TOOL_FUNCS = {"get_order": get_order}
TOOLS = [{
    "name": "get_order",
    "description": "按订单编号查询订单状态和承运商。订单编号必须是整数。",
    "input_schema": {"type": "object",
                     "properties": {"order_id": {"type": "integer", "description": "订单编号，例如 1001"}},
                     "required": ["order_id"]},
}]


# ---- 2. 循环：调用模型 -> 执行它要的工具 -> 把结果喂回去 -> 直到它不再调用工具 ----
def run_agent(task, max_steps=8):
    messages = [{"role": "user", "content": task}]
    for _ in range(max_steps):                                   # 步数上限：第 1 章讲过为什么必须有
        resp = client.messages.create(model=MODEL, max_tokens=16000, tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})   # 原样追加，不要只取文字
        if resp.stop_reason == "refusal":                        # 先检查：模型可能拒绝回答
            return "（模型拒绝了这个请求）"
        if resp.stop_reason != "tool_use":                       # 没有要调用的工具 = 模型认为做完了
            return "".join(b.text for b in resp.content if b.type == "text")
        results = []
        for block in resp.content:                               # 一轮里可能有多个工具调用
            if block.type != "tool_use":
                continue
            try:                                                 # 由我们的代码执行，不是模型
                out, is_error = json.dumps(TOOL_FUNCS[block.name](**block.input), ensure_ascii=False), False
            except Exception as e:                               # 出错也变成结果，让模型有机会处理
                out, is_error = f"{type(e).__name__}: {e}", True
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": out, "is_error": is_error})
        messages.append({"role": "user", "content": results})    # 所有结果放在同一条 user 消息里
    raise RuntimeError(f"超过 {max_steps} 步仍未结束")


if __name__ == "__main__":
    print(run_agent("订单 1001 和 1003 现在分别是什么状态？"))
