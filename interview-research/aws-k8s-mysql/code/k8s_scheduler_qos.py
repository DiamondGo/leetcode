"""实验 8：Kubernetes 调度（filter + score）、QoS 类别、Pending 原因。纯 Python 模拟，不连集群。
按文档描述的流程实现：先过滤（资源是否放得下、污点是否被容忍、nodeSelector 是否匹配），
再给剩下的节点打分（这里用“最少已分配”策略），选分数最高的。调度只看 **requests**，不看 limits，也不看实际用量。
这是教学模型：真实调度器还有亲和性、拓扑分布、优先级抢占、volume 绑定等大量插件。
"""
from dataclasses import dataclass, field


@dataclass
class Node:
    name: str
    cpu: int            # allocatable，单位 m（毫核）
    mem: int            # MiB
    labels: dict = field(default_factory=dict)
    taints: list = field(default_factory=list)   # 形如 "gpu=true:NoSchedule"
    used_cpu: int = 0
    used_mem: int = 0


@dataclass
class Pod:
    name: str
    req_cpu: int = 0
    req_mem: int = 0
    lim_cpu: int = None
    lim_mem: int = None
    node_selector: dict = field(default_factory=dict)
    tolerations: list = field(default_factory=list)


def qos(p):
    """Guaranteed：每种资源 requests == limits（且都设置了）；BestEffort：什么都没设；其余 Burstable。"""
    if not (p.req_cpu or p.req_mem or p.lim_cpu or p.lim_mem):
        return "BestEffort"
    if p.lim_cpu is not None and p.lim_mem is not None and p.req_cpu == p.lim_cpu and p.req_mem == p.lim_mem:
        return "Guaranteed"
    return "Burstable"


def schedule(pod, nodes):
    reasons, feasible = {}, []
    for n in nodes:
        if any(n.labels.get(k) != v for k, v in pod.node_selector.items()):
            reasons["node(s) didn't match Pod's node affinity/selector"] = reasons.get("node(s) didn't match Pod's node affinity/selector", 0) + 1
        elif any(t not in pod.tolerations for t in n.taints):
            msg = "node(s) had untolerated taint"
            reasons[msg] = reasons.get(msg, 0) + 1
        elif n.cpu - n.used_cpu < pod.req_cpu:
            reasons["Insufficient cpu"] = reasons.get("Insufficient cpu", 0) + 1
        elif n.mem - n.used_mem < pod.req_mem:
            reasons["Insufficient memory"] = reasons.get("Insufficient memory", 0) + 1
        else:
            feasible.append(n)
    if not feasible:
        why = ", ".join(f"{c} {m}" for m, c in reasons.items())
        return None, f"Pending: 0/{len(nodes)} nodes are available: {why}."
    def score(n):  # 剩余比例越高越好
        return ((n.cpu - n.used_cpu - pod.req_cpu) / n.cpu + (n.mem - n.used_mem - pod.req_mem) / n.mem) / 2 * 100
    best = max(feasible, key=score)
    msg = f"Scheduled to {best.name}（候选 {[x.name for x in feasible]}，得分 {score(best):.0f}）"
    best.used_cpu += pod.req_cpu; best.used_mem += pod.req_mem
    return best, msg


nodes = [Node("n1", 4000, 8192), Node("n2", 4000, 8192, taints=["gpu=true:NoSchedule"]), Node("n3", 2000, 4096, labels={"disk": "ssd"})]
pods = [
    Pod("web-1", 500, 512, 500, 512),
    Pod("web-2", 500, 512, 1000, 1024),
    Pod("batch", 0, 0),
    Pod("big", 3800, 1024),
    Pod("db", 1000, 2048, node_selector={"disk": "ssd"}),
    Pod("db-2", 1500, 2048, node_selector={"disk": "ssd"}),
    Pod("gpu-job", 1000, 1024, tolerations=["gpu=true:NoSchedule"]),
]
for p in pods:
    n, msg = schedule(p, nodes)
    print(f"{p.name:<8} QoS={qos(p):<10} -> {msg}")
print("\n节点已分配（requests 之和，不是实际用量）：")
for n in nodes:
    print(f"  {n.name}: cpu {n.used_cpu}/{n.cpu}m  mem {n.used_mem}/{n.mem}Mi  taints={n.taints}")
print("\n内存紧张时 kubelet 的驱逐倾向：BestEffort 先于 Burstable 先于 Guaranteed（Burstable 里看超出 requests 的程度）。")
print("容器内存超过 limit 会被内核 OOM kill（退出码 137）；CPU 超过 limit 只会被限流（throttling），不会被杀。")
