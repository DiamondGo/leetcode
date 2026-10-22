"""第 3 章：上下文是稀缺资源。演示三个手段：清理旧的工具结果、结构化笔记、按预算裁剪。"""
import json


def tokens(messages):
    """粗略估计 token：中文约 1 字 ≈ 1~2 token，这里取字符数/1.5，仅用于演示。"""
    return int(sum(len(m["content"]) for m in messages) / 1.5)


class Notes:
    """外部结构化笔记：关键事实写在上下文之外，需要时再读回。比"自然语言摘要"更不容易丢信息。"""
    def __init__(self):
        self.facts = {}

    def remember(self, key, value):
        self.facts[key] = value

    def render(self):
        return "已确认的事实：" + json.dumps(self.facts, ensure_ascii=False)


def clear_old_tool_results(messages, keep_last=1):
    """只保留最近 keep_last 个工具结果的原文，更早的替换成占位符（原文已提炼进笔记）。"""
    idx = [i for i, m in enumerate(messages) if m["role"] == "tool"]
    out = list(messages)
    for i in idx[:-keep_last] if keep_last else idx:
        out[i] = {**out[i], "content": f"[已清理，原长度 {len(messages[i]['content'])} 字符]"}
    return out


if __name__ == "__main__":
    big_log = "ERROR line\n" * 400                     # 一个体积很大的工具输出
    messages = [
        {"role": "system", "content": "你是运维助手。"},
        {"role": "user", "content": "排查 order-service 的故障"},
        {"role": "tool", "content": big_log},          # 第1次查日志
        {"role": "assistant", "content": "日志里大量 ERROR，我再看看指标。"},
        {"role": "tool", "content": "cpu=93% mem=40%"},
        {"role": "assistant", "content": "CPU 很高。"},
        {"role": "tool", "content": big_log},          # 第2次又查了日志
    ]
    notes = Notes()
    notes.remember("日志", "存在大量 ERROR，约 400 行")   # 读完日志就把关键事实记下来
    notes.remember("指标", "cpu=93% mem=40%")

    print("原始上下文估计 token：", tokens(messages))
    slim = clear_old_tool_results(messages, keep_last=1)
    slim.insert(1, {"role": "system", "content": notes.render()})
    print("清理旧结果并加入笔记后：", tokens(slim))
    print("笔记内容：", notes.render())
