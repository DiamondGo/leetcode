"""RAG 实验：为什么需要"混合检索"（hybrid search）？
对比三种检索：BM25（关键词）、玩具"语义"向量、两者用 RRF 融合。

重要说明：这里的"语义向量"是**故意简化的玩具**——只认识一张固定的同义词表里的词，不认识表外的词。
真实的嵌入模型是学出来的，能处理更广的同义和改写，但同样**不擅长稀有标识符**（错误码、人名、产品型号），
这个弱点是真实存在的，所以玩具模型抓住了这一点。结论（两种信号互补）在真实系统里同样成立。
"""
import math
import re
from collections import Counter

DOCS = {
    "d1": "Refund policy: customers can request reimbursement within 30 days of purchase by contacting support.",
    "d2": "Troubleshooting ERR-4012: the payment gateway timed out. Retry after 60 seconds or switch the card.",
    "d3": "Troubleshooting ERR-5003: database connection pool exhausted. Increase pool size in settings.",
    "d4": "Employee onboarding: new hires receive a laptop and account access on their first day.",
    "d5": "Vacation policy: employees accrue 1.5 days of paid leave per month.",
    "d6": "Expense reports must be submitted within 14 days with receipts attached.",
    "d7": "Password reset: use the self-service portal; credentials expire every 90 days.",
    "d8": "Release process: deployments happen on Tuesdays after the change advisory board approves.",
    "d9": "Incident response: page the on-call engineer and open a postmortem within 5 days.",
    "d10": "Customer data retention: records are deleted 7 years after account closure.",
    "d11": "API rate limits: 100 requests per minute per key; contact sales for higher quotas.",
    "d12": "Travel booking: book flights through the corporate portal; economy class for trips under 6 hours.",
}

# (查询, 正确答案, 类型)
QUERIES = [
    ("ERR-4012", "d2", "精确标识符"),
    ("ERR-5003 fix", "d3", "精确标识符"),
    ("change advisory board", "d8", "稀有术语"),
    ("postmortem", "d9", "稀有术语"),
    ("how do I get my money back", "d1", "同义改写"),
    ("time off allowance", "d5", "同义改写"),
    ("forgot my login secret", "d7", "同义改写"),
    ("how many calls per minute can I make", "d11", "同义改写"),
]

TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def tokens(text):
    return TOKEN.findall(text.lower())


# ---------- 1. BM25：词法检索 ----------
class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.tf = {i: Counter(tokens(t)) for i, t in docs.items()}
        self.len = {i: sum(c.values()) for i, c in self.tf.items()}
        self.avg = sum(self.len.values()) / len(docs)
        df = Counter(w for c in self.tf.values() for w in c)
        n = len(docs)
        self.idf = {w: math.log(1 + (n - d + 0.5) / (d + 0.5)) for w, d in df.items()}

    def score(self, query, doc_id):
        s = 0.0
        for w in tokens(query):
            f = self.tf[doc_id].get(w, 0)
            if f:
                s += self.idf[w] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[doc_id] / self.avg))
        return s

    def rank(self, query):
        scored = [(self.score(query, i), i) for i in self.tf]
        return [i for s, i in sorted(scored, key=lambda x: (-x[0], x[1])) if s > 0]


# ---------- 2. 玩具"语义"向量：只认识同义词表里的词 ----------
CONCEPTS = {
    "MONEY": {"refund", "reimbursement", "money", "back"},
    "LEAVE": {"vacation", "leave", "off", "allowance", "pto", "paid"},
    "PASSWORD": {"password", "credentials", "login", "secret", "passcode"},
    "REQUEST": {"requests", "request", "calls", "call"},
    "LIMIT": {"limits", "limit", "quotas", "quota"},
    "MINUTE": {"minute", "minutes"},
    "LAPTOP": {"laptop", "computer"}, "TRAVEL": {"travel", "flights", "trips"},
    "EXPENSE": {"expense", "receipts", "reports"}, "RETENTION": {"retention", "deleted", "records"},
}
LEXICON = {w: c for c, ws in CONCEPTS.items() for w in ws}


def dense_vec(text):
    return Counter(LEXICON[w] for w in tokens(text) if w in LEXICON)   # 表外的词（如 ERR-4012）直接忽略


def cosine(a, b):
    dot = sum(a[k] * b[k] for k in a)
    na, nb = math.sqrt(sum(v * v for v in a.values())), math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def dense_rank(query):
    q = dense_vec(query)
    scored = [(cosine(q, dense_vec(t)), i) for i, t in DOCS.items()]
    return [i for s, i in sorted(scored, key=lambda x: (-x[0], x[1])) if s > 0]


# ---------- 3. RRF（Reciprocal Rank Fusion）：只用名次融合，不需要对齐两种分数的尺度 ----------
def rrf(rankings, k=60):
    score = Counter()
    for r in rankings:
        for pos, d in enumerate(r, 1):
            score[d] += 1 / (k + pos)
    return [d for d, _ in sorted(score.items(), key=lambda x: (-x[1], x[0]))]


def evaluate(rank_fn):
    res = {}
    for q, gold, kind in QUERIES:
        r = rank_fn(q)
        pos = r.index(gold) + 1 if gold in r else None
        res.setdefault(kind, []).append(pos)
        res.setdefault("全部", []).append(pos)
    out = {}
    for kind, poss in res.items():
        n = len(poss)
        out[kind] = (sum(1 for p in poss if p == 1) / n,
                     sum(1 for p in poss if p and p <= 3) / n,
                     sum(1 / p for p in poss if p) / n)
    return out


if __name__ == "__main__":
    bm25 = BM25(DOCS)
    systems = {
        "BM25（关键词）": bm25.rank,
        "玩具语义向量": dense_rank,
        "混合（RRF 融合）": lambda q: rrf([bm25.rank(q), dense_rank(q)]),
    }
    print("每种查询类型的 Recall@1 / Recall@3 / MRR")
    for kind in ("精确标识符", "稀有术语", "同义改写", "全部"):
        print(f"\n[{kind}]")
        for name, fn in systems.items():
            r1, r3, mrr = evaluate(fn)[kind]
            print(f"  {name:<16} R@1={r1:.2f}  R@3={r3:.2f}  MRR={mrr:.2f}")
    print("\n单个查询的名次（前 3 名）：")
    for q, gold, kind in QUERIES[:1] + QUERIES[4:5]:
        print(f"  查询 {q!r}（答案 {gold}）")
        for name, fn in systems.items():
            print(f"    {name:<16} -> {fn(q)[:3]}")
