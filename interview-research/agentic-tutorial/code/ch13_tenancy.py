"""第 13 章：多租户隔离。向量检索只看语义相似度，不看权限——所以隔离必须在检索层强制，而不是写进提示词。"""
import math
from collections import Counter

DOCS = [
    {"id": 1, "tenant": "acme",   "text": "acme 公司 2026 年 Q3 财报 营收 增长 并购 计划"},
    {"id": 2, "tenant": "acme",   "text": "acme 员工 手册 请假 流程"},
    {"id": 3, "tenant": "globex", "text": "globex 公司 2026 年 Q3 财报 营收 下滑 裁员 计划"},
    {"id": 4, "tenant": "globex", "text": "globex 内部 安全 事故 复盘"},
]


def embed(text):
    return Counter(text.split())                         # 玩具"嵌入"：词袋


def cosine(a, b):
    dot = sum(a[w] * b[w] for w in a)
    na, nb = math.sqrt(sum(v * v for v in a.values())), math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def search_unsafe(query, k=2):
    """错误做法：全局取 top-k，再指望提示词/模型"忽略别的租户的内容"。"""
    q = embed(query)
    return sorted(DOCS, key=lambda d: -cosine(q, embed(d["text"])))[:k]


def search_safe(auth_tenant, query, k=2):
    """正确做法：租户来自服务端的认证上下文（不是模型传的参数），在排序前先过滤。"""
    q = embed(query)
    allowed = [d for d in DOCS if d["tenant"] == auth_tenant]
    return sorted(allowed, key=lambda d: -cosine(q, embed(d["text"])))[:k]


# ---- 缓存同样会泄漏 ----
class Cache:
    def __init__(self, per_tenant):
        self.per_tenant, self.store = per_tenant, {}

    def key(self, tenant, query):
        return (tenant, query) if self.per_tenant else query

    def get_or_compute(self, tenant, query, compute):
        k = self.key(tenant, query)
        if k not in self.store:
            self.store[k] = compute(tenant, query)
        return self.store[k]


def answer(tenant, query):
    top = search_safe(tenant, query, k=1)[0]
    return f"[{tenant}] {top['text']}"


if __name__ == "__main__":
    q = "2026 年 Q3 财报 营收 计划"
    print("== 检索 ==")
    print("不安全（acme 用户的查询，全局取 top-2）：")
    for d in search_unsafe(q):
        flag = "  <-- 别的租户的数据进入了上下文！" if d["tenant"] != "acme" else ""
        print(f"  [{d['tenant']}] {d['text']}{flag}")
    print("安全（服务端按认证身份先过滤）：")
    for d in search_safe("acme", q):
        print(f"  [{d['tenant']}] {d['text']}")

    print("== 缓存 ==")
    for per_tenant in (False, True):
        c = Cache(per_tenant)
        c.get_or_compute("acme", q, answer)               # acme 先问
        r = c.get_or_compute("globex", q, answer)         # globex 再问同一句
        who = "泄漏了 acme 的内容" if r.startswith("[acme]") else "正确，得到的是自己的数据"
        print(f"缓存键{'包含' if per_tenant else '不含'}租户 -> globex 看到：{r[:28]}…  ({who})")
