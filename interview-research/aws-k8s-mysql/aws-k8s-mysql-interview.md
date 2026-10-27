# AWS、Kubernetes、MySQL：高级后端面试知识与题库

> **这份材料的来源与可信度**
>
> - 我先搜索了三个主题的面试题合集（AWS：[Educative](https://www.educative.io/blog/aws-interview-questions-by-service-group)、[Hyring 2026 题库](https://hyring.com/jobseeker-toolkit/interview-questions/technical/aws) 等；Kubernetes：[techinterview.org](https://www.techinterview.org/post/3233477276/what-kubernetes-interviewers-actually-ask/)、[akhileshmishra 的文章](https://akhileshmishra.substack.com/p/these-advanced-kubernetes-interview) 等；MySQL：[besthub 系列文章](https://www.besthub.dev/articles/mysql-interview-guide-indexes-transactions-schema-design-and-storage-engines-722840231e97)、[DEV 社区](https://dev.to/gowthampotureddi/mysql-interview-questions-answers-top-patterns-for-data-engineers-2j65) 等）。这些多是面向一般岗位的博客，**没有标注日期，也不是高级后端岗位专属的真实面经**，所以我只用它们确认“哪些主题常考”，具体内容主要来自我自己的知识。
> - **MySQL 的实验是在真实的 MySQL 8.0.46 上跑出来的**，输出原样贴在正文里。
> - **AWS 的实验不连真实 AWS**：SQS/DynamoDB 用 moto 模拟器（API 写法与真实一致，但时间、限流等行为不保证一致）；IAM 判定和 DynamoDB 热分区是我写的教学模型。
> - **Kubernetes 的实验不连真实集群**（这个环境里没有）：调度、HPA、滚动更新、退避时间都是我按文档描述写的模拟，用来理解规则，不是真集群的输出。
> - 文中的具体数字（服务限额、默认值、价格相关结论、Kubernetes 的版本特性）来自我的记忆，**没有逐条对照最新官方文档**。凡是数字，请以官方文档为准；我在最容易变的地方都标了“以官方文档为准”。
> - 术语在每个小节第一次出现时附英文原名，附录有中英术语表。

## 零、面试里这三块通常怎么考

**高级岗位不会考“某服务是什么”，而是考“为什么选它、它会怎么坏、坏了怎么办、花多少钱”。** 三块的共同套路：

1. **先问机制**：S3 为什么是强一致（strong consistency）的？InnoDB 的 MVCC 怎么工作？Pod 被杀时发生了什么？
2. **再问取舍**：DynamoDB 还是 RDS？Lambda 还是容器？乐观锁（optimistic locking）还是悲观锁（pessimistic locking）？
3. **然后给一个故障**：线上某条 SQL 突然变慢；Pod 一直 CrashLoopBackOff；跨可用区（availability zone, AZ）流量费用暴涨。看你怎么一步步排查。
4. **最后是设计题**：把以上组合起来，设计一个服务，说清楚高可用、数据一致性（consistency）、安全和成本。

**给你的建议**：你的简历里有 AWS RDS 的经历，面试官很可能顺着这条线深挖（复制、故障转移（failover）、备份恢复、存储引擎、运维自动化）。MySQL 和 AWS 数据库这两块要准备得比别的更深，能讲出你亲身处理过的故障和取舍。

**怎么用这份材料**：每一块先读“为什么”和机制，跑一遍实验，亲眼看到结果，再去做面试题。题目后面的答案只是要点，面试时请用自己的话和自己的经历展开。

---

## 一、AWS：从“服务清单”到“取舍”

### 1.1 AWS 面试为什么难背

AWS 有两百多个服务，没人能背完。面试官也不指望你背。他们想看的是三件事：

- **你懂得云上的“基本物理”**：可用区（availability zone, AZ）会挂；网络默认不通，要显式打通；权限默认拒绝，要显式授予；一切按用量收费。
- **你能在几个相近的服务里选，并说出理由**：用 SQS 还是 Kinesis？用 Aurora 还是 DynamoDB？
- **你有生产经验**：限流（rate limiting）、重试（retry）、幂等（idempotency）、成本失控、权限过宽这些坑你踩过或见过。

所以复习的主线是：**计算、网络、存储、数据库、消息、安全、可靠性、成本**，每一块抓住 2 到 3 个核心取舍。

### 1.2 服务地图（先有个全局印象）

| 领域 | 核心服务 | 一句话 |
|---|---|---|
| 计算 | EC2、ECS、EKS、Fargate、Lambda | 虚拟机、容器编排（orchestration）、无服务器容器、函数 |
| 存储 | S3、EBS、EFS | 对象、块、共享文件 |
| 数据库 | RDS、Aurora、DynamoDB、ElastiCache | 托管关系型、云原生关系型、键值/文档、缓存（cache） |
| 消息与事件 | SQS、SNS、EventBridge、Kinesis、MSK | 队列、发布订阅、事件总线、流、托管 Kafka |
| 网络 | VPC、ALB/NLB、Route 53、CloudFront、API Gateway | 虚拟网络、负载均衡、DNS、CDN、API 入口 |
| 安全 | IAM、KMS、Secrets Manager、WAF | 身份权限、密钥、机密、Web 防火墙 |
| 可观测 | CloudWatch、X-Ray、CloudTrail | 指标（metrics）日志告警（alerting）、分布式追踪（trace）、API 审计（audit） |

### 1.3 IAM：权限默认拒绝

**为什么重要**：云上最常见的严重事故，是权限过宽加上凭证（credentials）泄露。IAM（Identity and Access Management，身份与访问管理）是所有服务的入口。

**核心概念**

- **主体（principal）**：谁在发请求。用户、角色（role）、AWS 服务。
- **策略（policy）**：一份 JSON，列出若干语句（statement），每条有 Effect（Allow 或 Deny）、Action、Resource、可选 Condition。
- **角色（role）**：没有长期密码的身份，**被别人“扮演”（assume）**，通过 STS（Security Token Service）拿到临时凭证。EC2 用实例配置文件（instance profile），Lambda 用执行角色，EKS 的 Pod 用 IRSA 或 Pod Identity。**原则：能用角色就不用长期访问密钥。**
- **信任策略（trust policy）**：规定“谁可以扮演这个角色”。权限策略规定“扮演后能做什么”。两个都要对。

**判定逻辑（背熟这几句）**

1. 默认拒绝（implicit deny）。
2. 只要有任何一个策略显式 Deny，就拒绝，**显式 Deny 永远优先**。
3. 需要有 Allow。同账号内，身份策略或资源策略任一放行即可；**跨账号则两边都要放行**。
4. **SCP（Service Control Policy，组织级服务控制策略）和权限边界（permissions boundary）只设“上限”，本身不授予权限**。最终权限是各层的交集。

```python
"""实验 5：IAM 权限判定的简化模型（纯 Python，不连 AWS）。
实现文档里的核心规则：默认拒绝；显式 Deny 永远优先；Allow 要同时被 SCP、权限边界（permissions boundary）放行；
同账号内资源策略可单独放行，跨账号则身份策略和资源策略都要放行。
这是**教学用简化模型**：不含条件键（Condition）、会话策略、NotAction 等，真实判定以 AWS 文档为准。
"""
from fnmatch import fnmatchcase


def match(patterns, value):
    return any(fnmatchcase(value, p) for p in patterns)


def stmts(policy, effect, action, resource):
    return [s for s in policy if s["Effect"] == effect and match(s["Action"], action) and match(s["Resource"], resource)]


def allowed_by(policies, action, resource):
    """一组策略里有没有匹配的 Allow。"""
    return any(stmts(p, "Allow", action, resource) for p in policies)


def explicit_deny(policies, action, resource):
    return any(stmts(p, "Deny", action, resource) for p in policies)


def evaluate(action, resource, identity=(), boundary=None, scps=(), resource_policy=None, same_account=True):
    allp = list(identity) + ([boundary] if boundary else []) + list(scps) + ([resource_policy] if resource_policy else [])
    if explicit_deny(allp, action, resource):
        return "拒绝：命中显式 Deny"
    if any(not allowed_by([s], action, resource) for s in scps):
        return "拒绝：SCP 没有放行（SCP 只设上限，不授予权限）"
    if boundary is not None and not allowed_by([boundary], action, resource):
        return "拒绝：超出权限边界"
    ident = allowed_by(identity, action, resource)
    res = bool(resource_policy) and allowed_by([resource_policy], action, resource)
    if same_account:
        return "允许" if (ident or res) else "拒绝：默认拒绝（没有任何 Allow）"
    return "允许" if (ident and res) else "拒绝：跨账号需要身份策略和资源策略都放行"


def S(effect, action, resource="*"):
    return {"Effect": effect, "Action": [action] if isinstance(action, str) else action,
            "Resource": [resource] if isinstance(resource, str) else resource}


BUCKET = "arn:aws:s3:::reports/*"
cases = [
    ("1 没有任何策略", dict(action="s3:GetObject", resource=BUCKET)),
    ("2 身份策略允许 s3:Get*", dict(action="s3:GetObject", resource=BUCKET, identity=[[S("Allow", "s3:Get*")]])),
    ("3 允许 s3:* 但显式拒绝删除", dict(action="s3:DeleteObject", resource=BUCKET,
                                     identity=[[S("Allow", "s3:*"), S("Deny", "s3:DeleteObject")]])),
    ("4 身份策略允许，但权限边界只给 ec2", dict(action="s3:GetObject", resource=BUCKET,
                                          identity=[[S("Allow", "s3:*")]], boundary=[S("Allow", "ec2:*")])),
    ("5 身份策略允许，但 SCP 只放行 ec2", dict(action="s3:GetObject", resource=BUCKET,
                                          identity=[[S("Allow", "s3:*")]], scps=[[S("Allow", "ec2:*")]])),
    ("6 同账号：只有桶策略允许", dict(action="s3:GetObject", resource=BUCKET, resource_policy=[S("Allow", "s3:GetObject")])),
    ("7 跨账号：只有桶策略允许", dict(action="s3:GetObject", resource=BUCKET, resource_policy=[S("Allow", "s3:GetObject")], same_account=False)),
    ("8 跨账号：两边都允许", dict(action="s3:GetObject", resource=BUCKET, identity=[[S("Allow", "s3:Get*")]],
                              resource_policy=[S("Allow", "s3:GetObject")], same_account=False)),
]
if __name__ == "__main__":
    for name, kw in cases:
        print(f"{name:<34} -> {evaluate(**kw)}")
```

运行结果：

```text
1 没有任何策略                           -> 拒绝：默认拒绝（没有任何 Allow）
2 身份策略允许 s3:Get*                   -> 允许
3 允许 s3:* 但显式拒绝删除                  -> 拒绝：命中显式 Deny
4 身份策略允许，但权限边界只给 ec2               -> 拒绝：超出权限边界
5 身份策略允许，但 SCP 只放行 ec2             -> 拒绝：SCP 没有放行（SCP 只设上限，不授予权限）
6 同账号：只有桶策略允许                      -> 允许
7 跨账号：只有桶策略允许                      -> 拒绝：跨账号需要身份策略和资源策略都放行
8 跨账号：两边都允许                        -> 允许
```

看第 5、7 两个用例：身份策略写了 `s3:*`，但 SCP 不放行就是拒绝；跨账号只有桶策略也是拒绝。这正是线上“明明加了权限还是 AccessDenied”最常见的原因。再强调一次：这是简化模型，真实判定还有条件键、会话策略、NotAction 等，以官方文档为准。

**排查 AccessDenied 的顺序**：看 CloudTrail 里的事件和错误信息 → 确认是哪个主体（角色、会话）→ 检查身份策略 → 资源策略 → 权限边界与 SCP → 条件键（来源 IP、VPC 终端节点、MFA、标签）→ KMS 密钥策略（读加密对象还要有 KMS 权限，这是个高频坑）。

### 1.4 VPC：网络默认是隔离的

**为什么**：VPC（Virtual Private Cloud，虚拟私有云）是你在 AWS 里的私有网络。很多面试官用 VPC 来区分“用过”和“背过”。

**组成**

- **CIDR 块**：比如 `10.0.0.0/16`。规划（planning）时要留足地址，并且**不要和公司内网或其他 VPC 重叠**，否则以后无法对等连接（peering）或接入专线。
- **子网（subnet）**：属于一个可用区（availability zone, AZ）。**公有子网**的路由表里有指向互联网网关（Internet Gateway, IGW）的默认路由（routing），**私有子网**没有。
- **路由表（route table）**：决定流量去向。
- **NAT 网关**：让私有子网里的实例**主动访问**外网，但外部不能主动连进来。放在公有子网。**它按小时和处理的数据量计费，是常见的成本大头**（具体价格以官方为准）。每个 AZ 放一个，才能抗 AZ 故障，也避免跨 AZ 流量费。
- **安全组（security group）**：挂在网络接口（ENI）上，**有状态**（stateful，放行了请求，响应自动放行），**只有允许规则**。
- **网络 ACL（NACL）**：挂在子网上，**无状态**（stateless，请求和响应要分别放行），有允许和拒绝规则，按编号顺序匹配。
- **VPC 终端节点（endpoint）**：私下访问 AWS 服务，不走公网。**网关型**（Gateway endpoint，目前用于 S3 和 DynamoDB，免费）和**接口型**（Interface endpoint，基于 PrivateLink，按小时和流量计费）。让私有子网访问 S3 时，用网关终端节点比走 NAT 便宜。
- **VPC 对等连接（peering）**：两个 VPC 点对点，**不可传递**。**Transit Gateway**：中心化的路由枢纽，适合很多 VPC。**PrivateLink**：只暴露某个服务，而不是整个网络，且不要求 CIDR 不重叠。

**典型三层架构**：公有子网放 ALB 和 NAT；私有子网放应用服务器；更深的私有子网放数据库（没有任何指向互联网的路由）。每层跨至少两个 AZ。

### 1.5 计算：EC2、容器、Lambda 怎么选

| 选项 | 适合 | 代价 |
|---|---|---|
| EC2 | 需要完全控制、特殊硬件、长期稳定负载（可买预留或 Savings Plans 省钱） | 自己管补丁、扩缩容、利用率 |
| ECS / EKS + EC2 | 容器化服务，要控制节点 | 要管节点；EKS 的 Kubernetes 复杂度见第二部分 |
| Fargate | 容器但不想管节点 | 单价更高、定制性较低 |
| Lambda | 事件驱动、突发、低频、胶水逻辑 | 冷启动、执行时长上限、并发与下游压力、调试与本地开发较难 |

**Lambda 的几个必讲点**

- **冷启动（cold start）**：新执行环境要下载代码、启动运行时、执行初始化。受语言（Java 较重）、包大小、是否在 VPC 内影响。缓解：预置并发（provisioned concurrency）、减小包、延迟加载、较新的快速启动选项（如 Java 的 SnapStart，以官方文档为准）。
- **并发模型**：每个并发请求一个执行环境。账号有并发配额（quota）；可设**预留并发（reserved concurrency）**，既保证某函数的容量，也限制它的最大并发，保护下游。
- **与队列配合**：Lambda 从 SQS 轮询时，一批消息里有一条失败，整批会重试（retry），所以要用**部分批处理失败响应（partial batch response）**，并且处理逻辑必须幂等（idempotency）。
- **执行时长有上限**（文档写的是 15 分钟，以官方为准），长任务用 Step Functions 或容器。
- **不适合**：长时间稳定高负载（通常比容器贵）、需要大量连接池（connection pool）的场景（每个环境一个连接，容易压垮 RDS，解决办法是 RDS Proxy）。

**负载均衡**：ALB 在第 7 层（HTTP），支持路径/主机路由（routing）、WebSocket、gRPC；NLB 在第 4 层，吞吐高延迟低，支持固定 IP 和 TLS 透传。

### 1.6 S3：看似简单的细节

**为什么**：S3 几乎出现在每道设计题里（存文件、日志、备份、数据湖）。

- **一致性**：2020 年底起，S3 对对象的读写提供**强一致（strong consistency）的读后写一致性**（strong read-after-write consistency）。以前“最终一致（eventual consistency）”的说法已过时，面试里答旧答案会扣分。
- **存储类别**：Standard、Intelligent-Tiering、Standard-IA / One Zone-IA、Glacier 系列。选择依据是访问频率、取回时间、最短存储期限、取回费用。用**生命周期规则（lifecycle）**自动转换和过期。
- **大文件**：分片上传（multipart upload），可并行、可断点重试（retry）；要配置清理未完成的分片，否则一直计费。
- **预签名 URL（presigned URL）**：服务端（server）用自己的凭证（credentials）生成带过期时间的 URL，让客户端（client）直接上传或下载，数据不经过你的服务器。注意：URL 的权限等于签名者的权限，有效期要短。
- **安全**：默认私有；用 Block Public Access；桶策略 + IAM；服务器端加密（SSE-S3、SSE-KMS）；版本控制 + MFA Delete 防误删；对象锁（Object Lock）做合规（compliance）保留。
- **性能**：请求速率按前缀（prefix）扩展，文档给过“每前缀每秒数千次”的量级（以官方为准）；大量小对象的问题常在请求数而不是带宽。
- **事件**：对象创建可触发 SNS/SQS/Lambda/EventBridge；**通知至少一次（at-least-once）投递，处理要幂等（idempotency）**。
- **常见成本坑**：跨区域传输、请求次数（小文件很多）、未清理的旧版本和分片、NAT 流量（用网关（gateway）终端节点避免）。

### 1.7 数据库：RDS、Aurora、DynamoDB、缓存

**RDS 与 Aurora**

- **Multi-AZ（多可用区）部署**：同步复制到另一个 AZ 的备用实例，**用于高可用，不用于读扩展**；主库故障时自动 failover（DNS 指向备用）。时间通常是一到数分钟量级（以官方为准）。另有“Multi-AZ 数据库集群”形态，带两个可读备用实例（以官方文档为准）。
- **只读副本（read replica）**：**异步（asynchronous）**复制，用于读扩展和跨区域，**有复制延迟（replication lag）**，应用要容忍读到旧数据。
- **备份**：自动备份 + 事务日志实现**时间点恢复（point-in-time recovery, PITR）**；手动快照；恢复是**创建新实例**，不是原地回滚（rollback）。
- **Aurora**：计算和存储分离，存储层是跨三个 AZ 的六副本分布式日志存储；副本共享同一存储，所以复制延迟通常很小，failover 通常更快。代价是价格、行为与社区 MySQL 有差异。
- **RDS Proxy**：连接池（connection pool），缓解 Lambda 和大量短连接对数据库的冲击，failover 时也能更平滑。
- **运维常考**：参数组、维护窗口、存储自动扩容、慢查询（slow query）日志、Performance Insights、升级策略（蓝绿部署）。

**DynamoDB**

- **为什么存在**：为了在任意规模下保持个位数毫秒的访问延迟，不用管服务器。代价是**你必须提前知道访问模式**，数据建模围绕访问模式而不是围绕实体。
- **键**：分区键（partition key）决定数据落在哪个分区；排序键（sort key）让同一分区键下的数据有序，支持范围查询。**Query 用键，Scan 读全表（避免）**。
- **索引**：LSI（本地二级索引（secondary index），同分区键，必须建表时创建）、GSI（全局二级索引，不同的键，**最终一致（eventual consistency）**，有自己的容量）。
- **容量**：按需（on-demand）或预置（provisioned）。读写容量单位的计算见下面实验。
- **一致性（consistency）**：默认最终一致读，可选强一致（strong consistency）读（只对表和 LSI，不对 GSI）；事务（TransactWriteItems）成本是普通读写的两倍。
- **条件写入（conditional write）**：`ConditionExpression` 实现乐观锁（optimistic locking）、去重（deduplication）、防覆盖，是 DynamoDB 做幂等（idempotency）的基础工具。
- **Streams**：变更数据流，可触发 Lambda，实现派生数据、缓存失效、事件发布。
- **热分区（hot partition）**：单个分区的吞吐有上限（文档说法约每秒 3000 个读容量单位、1000 个写容量单位）。访问严重偏斜时，即使表的总容量够，热分区也会被限流（rate limiting）。

```python
"""实验 7：DynamoDB 容量计算与热分区（hot partition）。纯 Python 模拟，不连 AWS。
文档给出的规则（请以官方文档为准，数字可能调整）：
  读：每 4KB 一个读容量单位（RCU）= 1 次强一致读/秒；最终一致读是一半；事务读是两倍。
  写：每 1KB 一个写容量单位（WCU）= 1 次写/秒；事务写是两倍。
  单个分区的吞吐上限约 3000 RCU / 1000 WCU（文档说法，这是热点问题的根源）。
"""
import math, random, zlib


def rcu(item_kb, reads_per_s, consistent=True):
    units = math.ceil(item_kb / 4) * reads_per_s
    return units if consistent else units / 2


def wcu(item_kb, writes_per_s):
    return math.ceil(item_kb) * writes_per_s


print("容量计算：")
print(f"  2KB 的项，每秒 500 次强一致读  -> {rcu(2, 500):.0f} RCU")
print(f"  2KB 的项，每秒 500 次最终一致读 -> {rcu(2, 500, False):.0f} RCU")
print(f"  5KB 的项，每秒 100 次强一致读  -> {rcu(5, 100):.0f} RCU（5KB 向上取整到 8KB，即 2 个单位）")
print(f"  1.5KB 的项，每秒 200 次写      -> {wcu(1.5, 200)} WCU（向上取整到 2KB）")

random.seed(7)
PARTS, WRITES, LIMIT_PER_PART_PER_S = 64, 40_000, 1000   # 模拟 1 秒内 4 万次写，分到 64 个分区（平均每分区 625，低于上限）
keys = 10_000
weights = [1 / (i + 1) ** 1.1 for i in range(keys)]        # 访问偏斜：少数 key 非常热
hot = random.choices(range(keys), weights=weights, k=WRITES)


def over_limit(assign):
    load = [0] * PARTS
    for k in hot:
        load[assign(k)] += 1
    return max(load), sum(1 for x in load if x > LIMIT_PER_PART_PER_S), load


def part(key):
    return zlib.crc32(key.encode()) % PARTS


avg = WRITES / PARTS
m, n_over, _ = over_limit(lambda k: part(f"user{k}"))
print(f"\n4 万次写/秒落在 64 个分区，平均每分区 {avg:.0f}（低于上限 {LIMIT_PER_PART_PER_S}），访问偏斜（Zipf 1.1）：")
print(f"  最忙分区 {m} 次/秒，是平均值的 {m / avg:.1f} 倍；超过上限的分区有 {n_over} 个 -> 热分区会被限流，即使表的总容量足够")

for SHARDS in (10, 50):
    m2, n2, _ = over_limit(lambda k: part(f"user{k}#{random.randrange(SHARDS)}"))
    print(f"写分片：给 key 加随机后缀 0..{SHARDS - 1} 后：最忙分区 {m2} 次/秒，是平均值的 {m2 / avg:.1f} 倍；超限分区 {n2} 个")
print("分片数要按最热 key 的写入量来定：10 个分片不够，50 个才压下来。代价：读时要查询所有分片再合并（scatter-gather）。")
```

运行结果：

```text
容量计算：
  2KB 的项，每秒 500 次强一致读  -> 500 RCU
  2KB 的项，每秒 500 次最终一致读 -> 250 RCU
  5KB 的项，每秒 100 次强一致读  -> 200 RCU（5KB 向上取整到 8KB，即 2 个单位）
  1.5KB 的项，每秒 200 次写      -> 400 WCU（向上取整到 2KB）

4 万次写/秒落在 64 个分区，平均每分区 625（低于上限 1000），访问偏斜（Zipf 1.1）：
  最忙分区 6351 次/秒，是平均值的 10.2 倍；超过上限的分区有 7 个 -> 热分区会被限流，即使表的总容量足够
写分片：给 key 加随机后缀 0..9 后：最忙分区 1309 次/秒，是平均值的 2.1 倍；超限分区 10 个
写分片：给 key 加随机后缀 0..49 后：最忙分区 793 次/秒，是平均值的 1.3 倍；超限分区 0 个
分片数要按最热 key 的写入量来定：10 个分片不够，50 个才压下来。代价：读时要查询所有分片再合并（scatter-gather）。
```

要点：容量计算是向上取整的（5KB 的项读一次算 8KB，也就是 2 个读容量单位）；总量低于上限不代表安全，偏斜才是问题；写分片（write sharding）能压下热点，但**分片数要按最热键的写入量来定**，并且读的时候要查所有分片再合并。

**缓存（ElastiCache：Redis/Valkey/Memcached）**：常见模式是旁路缓存（cache-aside）。注意缓存穿透（cache penetration，不存在的键反复查库，用空值缓存或布隆过滤器）、击穿（热点键过期瞬间，用互斥锁或提前续期）、雪崩（大量键同时过期，加随机抖动（jitter））。

**怎么选 RDS/Aurora 还是 DynamoDB**：访问模式复杂、需要 JOIN 和事务、数据量中等 → 关系型；访问模式固定、需要无限水平扩展和稳定低延迟、按键访问 → DynamoDB。**不要说“NoSQL 更快”**，要说清楚一致性、查询灵活性、扩展方式的取舍。

### 1.8 消息：SQS、SNS、EventBridge、Kinesis

- **SQS 标准队列**：几乎无限吞吐、**至少一次（at-least-once）投递**、不保证顺序。**FIFO 队列**：严格顺序（在消息组内）、可去重（deduplication），吞吐有上限（以官方为准，有高吞吐模式）。
- **可见性超时（visibility timeout）**：消息被取走后在一段时间内对别人不可见。**处理完必须删除**；超时前没删，消息会再次出现，所以才是“至少一次”。处理时间可能超过超时就要延长超时或做心跳（heartbeat）。
- **死信队列（dead-letter queue, DLQ）**：消息被接收超过 `maxReceiveCount` 次仍未成功，就转入 DLQ，避免毒消息（poison message）一直占用消费者。要给 DLQ 配告警（alerting），并有重放（redrive）手段。
- **SNS**：发布订阅，扇出（fan-out）到多个 SQS、Lambda、HTTP。典型：SNS → 多个 SQS，每个下游独立消费，互不拖累。
- **EventBridge**：事件总线，基于规则路由（routing），内置大量 AWS 与 SaaS 事件源，适合松耦合的事件驱动。
- **Kinesis / MSK**：有序、可重放的流（按分片/分区）。需要重放、多个消费者独立读取同一流、严格的分区内顺序时选它们；只是任务队列时，SQS 更简单。

下面的实验用 moto 模拟 SQS 和 DynamoDB：

```python
"""实验 6：SQS 的“至少一次投递”、可见性超时、死信队列，以及用 DynamoDB 条件写入做幂等消费。
用 moto 在本地模拟 AWS API（boto3 调用写法和真实 AWS 一致，但 moto 是模拟器：时间行为、限流、
FIFO 细节等不保证和真实服务完全一致）。运行：pip install boto3 "moto[sqs,dynamodb]"
"""
import json, time
import boto3
from botocore.exceptions import ClientError
from moto import mock_aws

with mock_aws():
    kw = dict(region_name="us-east-1", aws_access_key_id="x", aws_secret_access_key="x")
    sqs, ddb = boto3.client("sqs", **kw), boto3.client("dynamodb", **kw)

    dlq = sqs.create_queue(QueueName="orders-dlq")["QueueUrl"]
    dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
    q = sqs.create_queue(QueueName="orders", Attributes={
        "VisibilityTimeout": "1",
        "RedrivePolicy": json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "3"})})["QueueUrl"]
    ddb.create_table(TableName="processed", KeySchema=[{"AttributeName": "msg_id", "KeyType": "HASH"}],
                     AttributeDefinitions=[{"AttributeName": "msg_id", "AttributeType": "S"}], BillingMode="PAY_PER_REQUEST")

    print("=== A. 消费者处理完但没来得及删除消息 -> 可见性超时后再次投递（至少一次）===")
    sqs.send_message(QueueUrl=q, MessageBody="charge:order-1")
    m = sqs.receive_message(QueueUrl=q, MaxNumberOfMessages=1)["Messages"][0]
    print("第 1 次收到:", m["Body"], "| 立刻再收一次:", sqs.receive_message(QueueUrl=q).get("Messages", "收不到（消息处于不可见期）"))
    time.sleep(1.2)
    m2 = sqs.receive_message(QueueUrl=q, MaxNumberOfMessages=1)["Messages"][0]
    print("可见性超时后第 2 次收到同一条消息:", m2["Body"], "（如果每次都扣款，就重复扣款了）")

    print("\n=== B. 幂等消费：先用条件写入“占位”，失败说明处理过了 ===")
    def handle(msg_id):
        try:
            ddb.put_item(TableName="processed", Item={"msg_id": {"S": msg_id}},
                         ConditionExpression="attribute_not_exists(msg_id)")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return "已处理过，跳过"
            raise
        return "首次处理，执行扣款"
    print("第 1 次:", handle("order-1"))
    print("第 2 次:", handle("order-1"))
    print("（真实系统要注意：占位成功后、业务完成前崩溃怎么办？见正文：状态要有 processing/done，并有超时接管；"
          "或把业务写入和去重记录放在同一个事务里。）")

    print("\n=== C. 一直处理失败的“毒消息”：超过 maxReceiveCount 后进入死信队列 ===")
    sqs.purge_queue(QueueUrl=q); time.sleep(0.1)
    sqs.send_message(QueueUrl=q, MessageBody="poison")
    for i in range(1, 5):
        r = sqs.receive_message(QueueUrl=q, MaxNumberOfMessages=1)
        print(f"第 {i} 次在主队列收消息:", "收到并处理失败（不删除）" if r.get("Messages") else "没有消息")
        time.sleep(1.2)
    d = sqs.receive_message(QueueUrl=dlq, MaxNumberOfMessages=1).get("Messages")
    print("死信队列里:", d[0]["Body"] if d else "没有")
```

运行结果：

```text
=== A. 消费者处理完但没来得及删除消息 -> 可见性超时后再次投递（至少一次）===
第 1 次收到: charge:order-1 | 立刻再收一次: 收不到（消息处于不可见期）
可见性超时后第 2 次收到同一条消息: charge:order-1 （如果每次都扣款，就重复扣款了）

=== B. 幂等消费：先用条件写入“占位”，失败说明处理过了 ===
第 1 次: 首次处理，执行扣款
第 2 次: 已处理过，跳过
（真实系统要注意：占位成功后、业务完成前崩溃怎么办？见正文：状态要有 processing/done，并有超时接管；或把业务写入和去重记录放在同一个事务里。）

=== C. 一直处理失败的“毒消息”：超过 maxReceiveCount 后进入死信队列 ===
第 1 次在主队列收消息: 收到并处理失败（不删除）
第 2 次在主队列收消息: 收到并处理失败（不删除）
第 3 次在主队列收消息: 收到并处理失败（不删除）
第 4 次在主队列收消息: 没有消息
死信队列里: poison
```

三个结论：

1. **至少一次意味着重复是常态**。处理完但没来得及删除，消息就会再来。
2. **幂等（idempotency）不是可选项**。用条件写入（conditional write）占位是最简单的办法；但“占位后、业务完成前崩溃”这个窗口要处理：把状态分成处理中和已完成，并加超时接管；或者让业务写入和去重记录在同一个事务（transaction）里。
3. **毒消息必须有出口（egress）**：DLQ + 告警 + 重放。

### 1.9 可靠性与灾备

- **可用区（AZ）** 是同一区域（region）内相互隔离的数据中心群。**多 AZ 抗机房级故障，多区域（multi-region）抗区域级故障**。多数业务做到多 AZ 就够了；多区域成本和复杂度高很多（数据复制、一致性（consistency）、流量切换）。
- **RTO 和 RPO**：恢复时间目标（recovery time objective）是能容忍停多久；恢复点目标（recovery point objective）是能容忍丢多久的数据。先问业务要这两个数字，再选方案。
- **灾备（disaster recovery）四档（成本由低到高，恢复由慢到快）**：备份恢复（backup and restore）→ 引导灯（pilot light，核心数据一直复制，计算平时关闭）→ 暖备份（warm standby，缩小规模常驻运行）→ 多活（multi-site active/active）。
- **流量切换**：Route 53 健康检查 + 故障转移（failover）路由（routing）或加权路由；注意 DNS TTL 和客户端（client）缓存（cache）。
- **设计原则**：无状态服务、状态放托管数据库、重试（retry）要带退避（backoff）和抖动（jitter）、超时与断路器、限流（rate limiting）与背压（backpressure）、定期演练故障转移。**没演练过的灾备等于没有。**
- **AWS Well-Architected 六大支柱**：卓越运营、安全、可靠性、性能效率、成本优化、可持续性。设计题收尾时用它们自查。

### 1.10 安全与成本，高级岗位的两个加分项

**安全**：最小权限（least privilege）；用角色不用长期密钥；机密放 Secrets Manager 或 Parameter Store 并定期轮换；KMS 密钥策略与授权（authorization）；传输和静态加密（encryption at rest）；VPC 终端节点和私有子网（subnet）；CloudTrail 审计（audit）；GuardDuty/Config/Security Hub 之类的检测服务；对外入口前面放 WAF、限流（rate limiting）。

**成本**：先看账单，再谈优化。常见大头和手段——
- NAT 网关（gateway）的数据处理费 → 网关终端节点、把服务放在同一 AZ 内通信。
- 跨 AZ 和跨区域流量 → 拓扑感知路由（routing）、减少不必要的跨区调用。
- 空闲和过大的实例 → 右调（rightsizing）、自动扩缩容、Graviton 实例。
- 稳定负载 → Savings Plans 或预留；可中断负载 → Spot。
- 存储 → 生命周期规则、Intelligent-Tiering、清理旧快照和日志保留期。
- 打标签（cost allocation tags），否则谁也说不清钱花在哪。

### 1.11 AWS 面试题与答案要点

**W1. IAM 角色和用户有什么区别？为什么推荐用角色？**
用户有长期凭证（credentials，密码、访问密钥），泄露后一直有效；角色没有长期凭证，被扮演时通过 STS 发临时凭证，自动过期。EC2、Lambda、EKS 等都应绑定角色。跨账号访问也用角色（信任策略（trust policy）指定谁能扮演）。

**W2. 一个请求被 AccessDenied，你怎么排查？**
见 1.3 的顺序：CloudTrail 找到主体和被拒的原因 → 身份策略 → 资源策略 → 权限边界（permissions boundary）和 SCP → 条件键 → KMS 密钥策略。强调显式 Deny 优先、SCP 与边界只设上限。

**W3. 安全组（security group）和网络 ACL 的区别？**
安全组：实例/网卡级、有状态、只有允许；NACL：子网（subnet）级、无状态、有允许和拒绝、按序号匹配。大多数场景靠安全组，NACL 用来加一道粗粒度的黑名单。

**W4. 私有子网里的服务怎么访问互联网？怎么访问 S3？**
访问互联网：NAT 网关（放在公有子网，路由表（route table）把默认路由（routing）指向它）。访问 S3 和 DynamoDB：网关终端节点，免费且不走公网；其他 AWS 服务用接口终端节点。别忘了 NAT 的数据处理费。

**W5. 如何设计一个高可用的三层 Web 应用？**
跨至少两个（通常三个）AZ；公有子网放 ALB，私有子网放应用（自动扩缩容组或容器），再深一层放数据库（Multi-AZ 或 Aurora）；NAT 每 AZ 一个；无状态应用，会话放缓存或令牌；健康检查；备份与 PITR；监控告警（alerting）。

**W6. Multi-AZ 和只读副本（read replica）有什么区别？**
Multi-AZ：同步复制，为高可用，备用实例通常不对外服务（集群形态例外），故障时自动切换。只读副本：异步（asynchronous）复制，为读扩展或跨区域，有延迟，需要应用主动读它，提升为主库是手动操作。

**W7. RDS 主库故障转移（failover）时应用会发生什么？怎么让应用平稳？**
连接中断，DNS 指向新主库，期间几十秒到几分钟的不可用。应用要：使用端点（endpoint）而不是 IP；连接池（connection pool）有重连和校验；JVM 等的 DNS 缓存 TTL 要短；写操作幂等（idempotency）并重试（带退避（backoff））；可以用 RDS Proxy。

**W8. 什么时候用 DynamoDB，什么时候用 RDS/Aurora？**
见 1.7 最后一段。再补：DynamoDB 里做临时的复杂查询很痛苦，需要分析时导出到 S3 用 Athena，或同步到 OpenSearch。

**W9. DynamoDB 怎么选分区键？什么是热分区（hot partition）？**
要选基数高、访问均匀的键。热分区是访问偏斜导致单分区超过上限而被限流（rate limiting），总容量够也没用。办法：键里加随机或计算出的后缀（写分片（write sharding））、读多时加缓存（DAX 或应用层）、重新设计键。见实验。

**W10. SQS 的至少一次（at-least-once）投递会带来什么问题？怎么处理？**
重复处理。必须幂等：用业务唯一键 + 条件写入（conditional write），或数据库唯一约束。设置合适的可见性超时（visibility timeout），处理完才删除，配 DLQ。FIFO 队列可以去重（deduplication），但只在去重窗口内，不替代业务层幂等。

**W11. SQS 标准队列和 Kinesis 怎么选？**
任务分发、削峰、每条消息被一个消费者处理一次 → SQS；需要重放（replay）、多个消费者独立消费同一份数据、分区内严格顺序、高吞吐流式（streaming）处理 → Kinesis（或 MSK）。

**W12. Lambda 冷启动（cold start）怎么缓解？**
预置并发（provisioned concurrency）；减小部署包；避免不必要的 VPC 附加（现在影响已小很多，以官方为准）；初始化放在处理函数之外复用；选启动快的运行时，或用 SnapStart 之类的特性。

**W13. Lambda 连接 RDS 有什么问题？**
每个执行环境一个连接，并发（concurrency）上来后连接数暴涨，压垮数据库。用 RDS Proxy 做连接池；限制预留并发（reserved concurrency）；或改用 HTTP 型的数据 API。

**W14. S3 是强一致（strong consistency）还是最终一致（eventual consistency）？**
对象的 PUT、DELETE 和后续 GET、LIST 是强一致（2020 年底起）。注意：跨区域复制是异步的；桶配置的传播等细节仍可能有延迟。

**W15. 怎么让用户把大文件传到 S3，而不经过你的服务器？**
服务端（server）生成预签名（presigned） URL（大文件用分片上传（multipart upload）的预签名 URL），客户端（client）直传。服务端限制大小、类型、过期时间；上传完成后用 S3 事件触发后续处理，并做病毒扫描和校验。

**W16. 怎么实现跨区域灾备（disaster recovery）？RTO/RPO 怎么定？**
先由业务定 RTO/RPO，再选四档方案。数据层：S3 跨区域复制、DynamoDB 全局表、Aurora 全局数据库或跨区域只读副本。流量层：Route 53 故障转移。重点是演练、配置也要同步（IaC）、密钥和 AMI 也要跨区。

**W17. 怎么在 AWS 上做零停机发布？**
蓝绿或滚动或金丝雀（CodeDeploy、ALB 加权目标组、Lambda 别名加权）；健康检查和自动回滚（rollback）；数据库变更用“扩展-迁移-收缩”（expand/contract）并保持向后兼容；功能开关。

**W18. CloudWatch 和 CloudTrail 有什么区别？**
CloudWatch：指标（metrics）、日志、告警（运行时观测）。CloudTrail：记录谁在什么时候调用了什么 AWS API（审计（audit）与安全调查）。

**W19. 怎么降低 AWS 账单？**
见 1.10：先分析（成本分配标签、Cost Explorer），再处理 NAT/跨区流量、右调（rightsizing）、Savings Plans/Spot、存储生命周期、无用资源清理。强调**用数据驱动**，并说明优化不能牺牲可靠性。

**W20. ALB 和 NLB 怎么选？**
HTTP 层的路由、WebSocket、gRPC、基于路径和主机 → ALB；极致吞吐和低延迟、固定 IP、非 HTTP 协议（protocol）、TLS 透传 → NLB。

**W21. 什么是最终一致？举一个 AWS 里遇到它的例子。**
写入后立刻读，可能读到旧值。例子：DynamoDB 最终一致读和 GSI；RDS 只读副本；S3 跨区域复制；IAM 变更的传播延迟。应对：必要时用强一致读、读主库、读己之写（read-your-writes）的路由策略、或在 UI 上做乐观更新。

**W22. 怎样保护 AWS 里的机密？**
Secrets Manager/Parameter Store，KMS 加密，角色读取，自动轮换，代码和环境变量里不放明文，审计访问日志；对容器可用外部机密注入。

**W23. 你怎么设计限流和防滥用？**
入口：CloudFront + WAF（速率规则）、API Gateway 的使用计划与节流（throttling）；服务内：令牌桶（token bucket）按租户（tenant）限流；下游：队列削峰、并发上限。返回 429 与 Retry-After，客户端指数退避（exponential backoff）加抖动（jitter）。

**W24. 最小权限（least privilege）怎么落地，而不是停在口号？**
从宽到窄：先用 IAM Access Analyzer 和访问记录找出实际用到的权限，再生成最小策略；资源级限定；条件键；权限边界给开发者自助创建角色的天花板；SCP 在组织层面禁掉危险操作；定期审计。

**W25. 你在生产里遇到过的最大的 AWS 事故是什么？怎么复盘？（行为题）**
准备一个真实案例：背景、现象、定位过程、根因、止血、长期修复、你的个人贡献、学到的东西。结构：时间线 + 影响面 + 根因（不要只写“人为失误”，要写系统为什么允许它发生）+ 防再发措施。

### 1.12 设计题（AWS 视角）

**设计题：一个图片上传与处理服务（用户上传图片，生成多种缩略图，之后可以快速访问）**

1. **上传**：客户端（client）向 API 申请预签名（presigned） URL，直传 S3 的 `uploads/` 前缀；API 在数据库记录 `status=pending`。
2. **处理**：S3 事件 → SQS（缓冲、削峰、失败重试（retry）和 DLQ）→ 消费者（Lambda 或容器）生成缩略图，写入 `processed/`，更新状态。消息可能重复，用对象键和状态做幂等（idempotency）。
3. **访问**：CloudFront 在前，S3 为源站；私有内容用签名 URL 或签名 Cookie。
4. **元数据（metadata）**：DynamoDB（按用户和图片编号访问）或 RDS（需要复杂查询时）。
5. **可靠性**：S3 本身多 AZ；队列和消费者无状态；DLQ 告警（alerting）；生命周期规则清理原图或转入低频存储。
6. **安全**：桶默认私有；服务端（server）按用户鉴权后才发预签名 URL，限制大小和类型；SSE-KMS；病毒扫描；用 VPC 终端节点访问 S3。
7. **成本**：缩略图按需生成还是预生成？CloudFront 缓存（cache）命中率；存储分层；避免小对象过多。
8. **取舍**：Lambda 方便但图片很大或处理很久时，换容器；是否需要多区域。


---

## 二、Kubernetes：从“声明期望状态”理解一切

### 2.1 为什么需要 Kubernetes

假设你有几十个服务，每个要跑多个副本，机器会坏，流量会涨落，版本要不停发布。手工做这些事（在哪台机器上起、挂了拉起、升级时不断流、服务之间怎么找到彼此）很快会失控。

Kubernetes（K8s）的核心思想只有一个：**你声明“期望状态”（desired state），系统不断把“实际状态”调和（reconcile）到期望状态**。你写“我要 3 个副本的这个镜像”，控制器（controller）发现只有 2 个，就去创建 1 个；某个节点挂了，副本少了，它又补上。理解了这个控制循环（control loop），Deployment、HPA、Job、Operator 都是同一个模式的不同实例。

### 2.2 架构

**控制平面（control plane）**

- **kube-apiserver**：唯一入口，所有组件和 kubectl 都通过它读写；做认证（authentication）、授权（authorization）、准入控制（admission control）。
- **etcd**：存全部集群状态的一致性（consistency）键值库（Raft）。它的性能和可用性决定集群的上限。只有 apiserver 直接访问它。
- **kube-scheduler**：给还没分配节点的 Pod 选一个节点（过滤 + 打分）。
- **kube-controller-manager**：运行一堆控制器（Deployment、ReplicaSet、Node、Job、Endpoint 等）。
- **cloud-controller-manager**：和云厂商对接（负载均衡、节点生命周期等）。

**节点（node）**

- **kubelet**：节点上的代理，按 apiserver 里分配给本节点的 Pod 规格，通过容器运行时（containerd、CRI-O）启动容器、执行探针（probe）、上报状态。
- **kube-proxy**：实现 Service 的转发规则（iptables 或 IPVS，有些网络方案会替代它）。
- **容器运行时**和 **CNI 网络插件**。

**一次 `kubectl apply` 发生了什么**（高频题，要能完整讲出来）：

1. kubectl 把 YAML 发给 apiserver；认证、授权、准入（变更型和校验型 webhook）、校验，通过后写入 etcd。
2. Deployment 控制器通过**监听（watch）**发现新对象，创建 ReplicaSet；ReplicaSet 控制器创建 Pod 对象（此时 `nodeName` 为空，状态 Pending）。
3. 调度器监听到未调度的 Pod，选定节点，把绑定结果写回 apiserver。
4. 目标节点的 kubelet 监听到分配给自己的 Pod，调用 CRI 拉镜像、创建容器，调用 CNI 配网络，挂载卷，启动容器，执行探针，把状态写回 apiserver。
5. Endpoint 控制器在 Pod 就绪后把它加入 Service 的后端；kube-proxy 更新转发规则。

关键点：**组件之间不直接对话，都通过 apiserver + watch 协作**，每个控制器只关心自己那一块。

### 2.3 Pod 与生命周期

- **Pod** 是最小调度单位：一个或多个共享网络命名空间（namespace，同一个 IP）和存储卷的容器。
- **init container（初始化容器）**：按顺序在应用容器之前运行，成功退出后才继续，用来做依赖检查、迁移、下载配置。
- **sidecar（边车）**：与主容器同生命周期的辅助容器（日志、代理）。较新版本把 sidecar 作为带 restartPolicy 的 init container 原生支持（具体版本以官方文档为准），解决了“Job 里 sidecar 不退出导致 Pod 不结束”之类的老问题。
- **Pod 阶段**：Pending、Running、Succeeded、Failed、Unknown。**容器状态**：Waiting、Running、Terminated，要结合 `reason`（如 CrashLoopBackOff、ImagePullBackOff、OOMKilled）。
- **优雅终止（graceful shutdown）**，必须会讲：
  1. Pod 被标记删除，同时发生两件事：从 Service 后端摘除（异步（asynchronous）），以及 kubelet 执行 `preStop` 钩子（hooks）后发送 **SIGTERM**。
  2. 在 `terminationGracePeriodSeconds`（默认 30 秒）内应用应当停止接收新请求、处理完在途请求、退出。
  3. 超时后发送 **SIGKILL**。
  - **常见坑**：摘除和 SIGTERM 是并行的，应用收到 SIGTERM 时仍可能收到新流量。办法：`preStop` 里 sleep 几秒，或应用收到 SIGTERM 后先继续服务一小会儿再关；应用必须真的处理 SIGTERM（容器里 PID 1 不转发信号是个经典问题，用 `exec` 形式启动或 init 进程）。

### 2.4 工作负载控制器

| 对象 | 用途 | 要点 |
|---|---|---|
| Deployment | 无状态服务 | 管 ReplicaSet，支持滚动更新（rolling update）与回滚（rollback） |
| StatefulSet | 有状态服务（数据库、Kafka） | 稳定的网络标识和序号（`db-0`），按序创建/删除，每个副本独立的 PVC |
| DaemonSet | 每个节点一份（日志、监控代理） | 新节点自动加上 |
| Job / CronJob | 一次性/定时任务 | `backoffLimit`、`activeDeadlineSeconds`、并发（concurrency）策略 |

StatefulSet 常考：为什么节点 NotReady 时它的 Pod 不会马上在别处重建？因为系统无法确认原节点上的 Pod 是否真的停了，**为避免同一个有状态副本同时运行两份（脑裂，会写坏数据），默认宁可等待**。需要运维介入（确认节点已死，强制删除 Pod）或依赖节点自动修复机制。

### 2.5 网络

- **基本规则**：每个 Pod 有自己的 IP；Pod 之间不经 NAT 直接互通（由 CNI 实现）。
- **Service**：给一组 Pod 一个稳定的虚拟 IP 和 DNS 名，用标签选择器（label selector）选后端。类型：ClusterIP（集群内）、NodePort、LoadBalancer（云上创建外部负载均衡）、ExternalName。**Headless Service**（`clusterIP: None`）不分配虚拟 IP，DNS 直接返回各 Pod 的 IP，StatefulSet 靠它提供稳定域名。
- **Ingress / Gateway API**：七层路由（routing），把外部 HTTP 流量按主机和路径转给 Service，需要 Ingress 控制器（如 AWS Load Balancer Controller、NGINX）实现。
- **DNS（CoreDNS）**：`svc.namespace.svc.cluster.local`。常见坑：`ndots:5` 导致外部域名查询要先试多个后缀，增加延迟和 CoreDNS 压力；NetworkPolicy 误拦 DNS（UDP/TCP 53）使得一切解析失败。
- **NetworkPolicy**：默认全通；一旦有策略选中某个 Pod，就只允许策略列出的流量。需要 CNI 支持才生效。**写“默认拒绝”后别忘了放行 DNS 和必要的出口（egress）。**
- **“Service 访问不通”的排查顺序**：Service 的选择器和 Pod 标签是否匹配 → `kubectl get endpoints`（EndpointSlice）是否为空 → Pod 是否 Ready（readiness 未通过不会进 Endpoint）→ targetPort 是否正确 → 应用是否监听 0.0.0.0（只监听 127.0.0.1 外部连不上）→ NetworkPolicy → DNS。

### 2.6 配置与存储

- **ConfigMap**：非敏感配置。**Secret**：敏感数据，默认只是 base64 编码，**不是加密**。要在 etcd 里启用静态加密（encryption at rest）或接入外部密钥管理，并用 RBAC 限制读取。
- 通过环境变量注入时更新不会生效，需要重启；以卷挂载时会最终更新（有延迟），但应用要自己重新读取。
- **PV / PVC / StorageClass**：PVC 是对存储的申请，StorageClass 决定动态创建什么存储（比如 EBS gp3），PV 是实际的卷。访问模式 ReadWriteOnce 等。**EBS 卷只能在一个 AZ 内**：Pod 被调度到别的 AZ 就挂不上，需要 `volumeBindingMode: WaitForFirstConsumer` 让卷在 Pod 调度后再创建。

### 2.7 资源、调度与服务质量

**requests 与 limits**

- **requests**：调度时用来判断节点放不放得下，也是 CPU 份额的权重。**调度器（scheduler）只看 requests，不看 limits，也不看实际用量。**
- **limits**：运行时的上限。内存超限 → 被内核 OOM kill（退出码 137）；CPU 超限 → 被**限流（throttling）**，不会被杀，但延迟上升。
- **QoS 类别**：每种资源 requests 等于 limits → Guaranteed；什么都没设 → BestEffort；其他 → Burstable。节点资源紧张时 kubelet 按 BestEffort、Burstable（超出 requests 越多越先）、Guaranteed 的倾向驱逐（eviction）。
- 经验：**内存 request 与 limit 设得接近**（内存不可压缩，超了就死）；CPU 可以不设 limit 或设宽松些，避免不必要的限流，但要有 request。

**调度器（过滤 → 打分）**，以及让 Pod 去或不去某些节点的工具：

- `nodeSelector` / 节点亲和性（node affinity）：想去哪。
- Pod 亲和 / 反亲和性、**拓扑分布约束（topology spread constraints）**：让副本分散到不同节点或 AZ，抗故障。
- **污点（taint）与容忍（toleration）**：节点“排斥”，Pod 声明“我能忍”。GPU 节点常用。注意：容忍只是“允许”，不等于“一定去”。
- **PodDisruptionBudget（PDB）**：限制自愿驱逐（节点排空、升级）时同时不可用的副本数。没有 PDB，升级节点可能一次带走所有副本。
- 优先级与抢占（PriorityClass）。

下面的实验用纯 Python 模拟了过滤、打分、QoS 判定和 Pending 原因的格式（不是真集群）：

```python
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
```

运行结果：

```text
web-1    QoS=Guaranteed -> Scheduled to n1（候选 ['n1', 'n3']，得分 91）
web-2    QoS=Burstable  -> Scheduled to n1（候选 ['n1', 'n3']，得分 81）
batch    QoS=BestEffort -> Scheduled to n3（候选 ['n1', 'n3']，得分 100）
big      QoS=Burstable  -> Pending: 0/3 nodes are available: 2 Insufficient cpu, 1 node(s) had untolerated taint.
db       QoS=Burstable  -> Scheduled to n3（候选 ['n3']，得分 50）
db-2     QoS=Burstable  -> Pending: 0/3 nodes are available: 2 node(s) didn't match Pod's node affinity/selector, 1 Insufficient cpu.
gpu-job  QoS=Burstable  -> Scheduled to n2（候选 ['n1', 'n2', 'n3']，得分 81）

节点已分配（requests 之和，不是实际用量）：
  n1: cpu 1000/4000m  mem 1024/8192Mi  taints=[]
  n2: cpu 1000/4000m  mem 1024/8192Mi  taints=['gpu=true:NoSchedule']
  n3: cpu 1000/2000m  mem 2048/4096Mi  taints=[]

内存紧张时 kubelet 的驱逐倾向：BestEffort 先于 Burstable 先于 Guaranteed（Burstable 里看超出 requests 的程度）。
容器内存超过 limit 会被内核 OOM kill（退出码 137）；CPU 超过 limit 只会被限流（throttling），不会被杀。
```

看 `big` 和 `db-2` 两个 Pending 的 Pod：事件信息 `0/3 nodes are available: ...` 把每个节点被淘汰的原因汇总出来，**这就是排查 Pending 的入口**（`kubectl describe pod` 的 Events）。再注意 n3 的 CPU 请求量已经满了，但它的实际使用率可能很低——调度看的是 requests 总和。这就是为什么“集群显示 CPU 使用率不高，但 Pod 调度不上”。

### 2.8 探针、发布与弹性伸缩

**三种探针（probe）**，几乎必考：

- **liveness（存活）**：失败 → kubelet **重启容器**。用来发现死锁（deadlock）、卡死。**不要把外部依赖（数据库）检查放进 liveness**，否则数据库抖动（jitter）会让所有 Pod 被重启，雪上加霜。
- **readiness（就绪）**：失败 → 把 Pod **从 Service 后端摘除**，不重启。用来表示“现在能不能接流量”（预热、依赖不可用、过载）。
- **startup（启动）**：成功之前，其他两种探针不执行。用于启动很慢的应用（比如大 Java 应用），避免 liveness 过早杀掉它。

经典场景：慢启动的 Java 应用，liveness 的 `initialDelaySeconds` 太短 → 还没启动完就被杀 → 重启 → 又被杀，进入 CrashLoopBackOff。修法：加 startup 探针。

**滚动更新（rolling update）**：Deployment 默认策略。`maxSurge`（可以多出多少个）与 `maxUnavailable`（可以少多少个），默认各 25%，maxSurge 向上取整，maxUnavailable 向下取整。新 Pod 要 **Ready 才算可用**，所以 readiness 探针决定了发布是否安全。回滚（rollback）：`kubectl rollout undo`。

**弹性伸缩**

- **HPA（Horizontal Pod Autoscaler）**：按指标调副本数。核心公式 `期望副本 = ceil(当前副本 × 当前指标 / 目标指标)`；比值在 1±0.1（容忍度（tolerance））内不动；缩容有稳定窗口（默认 5 分钟）防抖动；约每 15 秒检查一次。**前提**：有指标来源（metrics-server 或自定义指标适配器（adapter））；按资源利用率扩缩时，Pod **必须设置 requests**，因为利用率是相对 requests 算的。
- **VPA**：调整 requests/limits。**Cluster Autoscaler / Karpenter**：Pod 因资源不足 Pending 时加节点，节点闲置时回收。三者要配合：HPA 加 Pod → 不够放 → 加节点。

```python
"""实验 9：HPA 扩缩容公式、滚动更新的 maxSurge/maxUnavailable、CrashLoopBackOff 的退避时间。
纯 Python 模拟，按 Kubernetes 文档描述的公式实现（教学模型，不连集群）：
  HPA：desired = ceil(current × 当前指标 / 目标指标)；比值在 1±0.1 内不动（tolerance）；
       缩容取过去 5 分钟（stabilization window）内算出的最大值，防止抖动；每 15 秒同步一次。
  滚动更新：maxSurge 向上取整，maxUnavailable 向下取整；默认都是 25%。
  CrashLoopBackOff：重启延迟 10s、20s、40s…… 翻倍，上限 5 分钟。
"""
import math


def hpa(current, metric, target, tol=0.1):
    ratio = metric / target
    if abs(ratio - 1) <= tol:
        return current
    return math.ceil(current * ratio)


print("=== A. HPA：目标 CPU 利用率 60%，当前 4 个副本 ===")
for m in (50, 63, 66, 90, 120, 30):
    print(f"  当前平均利用率 {m:>3}% -> 期望副本 {hpa(4, m, 60)}")
print("  （63% 比值 1.05，落在容忍范围内不动；50% 算出 ceil(3.33)=4，向上取整所以还是 4；利用率是相对 **requests** 算的，没设 requests 就没法用）")

print("\n=== B. 缩容稳定窗口：流量尖峰过去后，副本不会立刻缩回去 ===")
load = [90] * 4 + [30] * 28   # 每步 15 秒；先高负载 1 分钟，然后骤降
replicas, history, window = 4, [], 20     # 窗口按 20 步（5 分钟）
trace = []
for t, m in enumerate(load):
    total_load = m * 4          # 总负载固定；平均利用率 = 总负载 / 副本数
    util = total_load / replicas
    raw = hpa(replicas, util, 60)
    history.append(raw)
    if raw < replicas:
        replicas = max(history[-window:])      # 缩容取窗口内最大值
    else:
        replicas = raw
    trace.append(replicas)
print("  每 15 秒一步，副本数:", trace)
print(f"  负载骤降后第 {next(i for i, r in enumerate(trace) if i >= 4 and r < max(trace)) * 15 - 60} 秒才开始缩容（稳定窗口约 300 秒）")


def surge_unavail(replicas, surge="25%", unavail="25%"):
    f = lambda x, up: (math.ceil if up else math.floor)(replicas * float(x[:-1]) / 100) if str(x).endswith("%") else int(x)
    s, u = f(surge, True), f(unavail, False)
    return s, u


print("\n=== C. 滚动更新 ===")
for n, sg, un in ((10, "25%", "25%"), (3, "25%", "25%"), (4, "25%", "25%"), (10, "0", "1"), (10, "100%", "0")):
    s, u = surge_unavail(n, sg, un)
    if s == 0 and u == 0:
        print(f"  replicas={n}: 不合法，两者不能同时为 0")
        continue
    print(f"  replicas={n:<2} maxSurge={sg:<4} maxUnavailable={un:<4} -> 最多同时 {n + s} 个，至少 {n - u} 个可用")
print("  （只有 readiness 通过的新 Pod 才算“可用”：readiness 写错会让滚动更新卡住；"
      "maxUnavailable=0 + 一个永远不 Ready 的新版本 = 旧版本继续服务，更新停在中间，这是好事。）")

print("\n=== D. CrashLoopBackOff 重启间隔 ===")
d, t, seq = 10, 0, []
for i in range(8):
    seq.append(d); t += d; d = min(d * 2, 300)
print("  第 1~8 次重启前等待（秒）:", seq, f"累计 {t}s")
print("  （容器稳定运行一段时间后退避会重置。CrashLoopBackOff 只是“反复崩溃”的状态，不是原因；"
      "先看 kubectl describe pod 的 Last State 和 exit code，再看 kubectl logs --previous。）")
```

运行结果：

```text
=== A. HPA：目标 CPU 利用率 60%，当前 4 个副本 ===
  当前平均利用率  50% -> 期望副本 4
  当前平均利用率  63% -> 期望副本 4
  当前平均利用率  66% -> 期望副本 5
  当前平均利用率  90% -> 期望副本 6
  当前平均利用率 120% -> 期望副本 8
  当前平均利用率  30% -> 期望副本 2
  （63% 比值 1.05，落在容忍范围内不动；50% 算出 ceil(3.33)=4，向上取整所以还是 4；利用率是相对 **requests** 算的，没设 requests 就没法用）

=== B. 缩容稳定窗口：流量尖峰过去后，副本不会立刻缩回去 ===
  每 15 秒一步，副本数: [6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 2, 2, 2, 2, 2, 2, 2, 2, 2]
  负载骤降后第 285 秒才开始缩容（稳定窗口约 300 秒）

=== C. 滚动更新 ===
  replicas=10 maxSurge=25%  maxUnavailable=25%  -> 最多同时 13 个，至少 8 个可用
  replicas=3  maxSurge=25%  maxUnavailable=25%  -> 最多同时 4 个，至少 3 个可用
  replicas=4  maxSurge=25%  maxUnavailable=25%  -> 最多同时 5 个，至少 3 个可用
  replicas=10 maxSurge=0    maxUnavailable=1    -> 最多同时 10 个，至少 9 个可用
  replicas=10 maxSurge=100% maxUnavailable=0    -> 最多同时 20 个，至少 10 个可用
  （只有 readiness 通过的新 Pod 才算“可用”：readiness 写错会让滚动更新卡住；maxUnavailable=0 + 一个永远不 Ready 的新版本 = 旧版本继续服务，更新停在中间，这是好事。）

=== D. CrashLoopBackOff 重启间隔 ===
  第 1~8 次重启前等待（秒）: [10, 20, 40, 80, 160, 300, 300, 300] 累计 1210s
  （容器稳定运行一段时间后退避会重置。CrashLoopBackOff 只是“反复崩溃”的状态，不是原因；先看 kubectl describe pod 的 Last State 和 exit code，再看 kubectl logs --previous。）
```

四个结论：

1. HPA 有容忍区间，63% 对 60% 目标不动；缩容有 5 分钟窗口，所以尖峰过去后副本数会“拖”一段时间才降，这是故意的。
2. 3 个副本、默认 25%：maxSurge 向上取整为 1，maxUnavailable 向下取整为 0——小规模服务的滚动更新实际上是“先起一个新的，再删一个旧的”。
3. `maxUnavailable=0` 加一个永远不 Ready 的新版本，更新会卡在中间但旧版本继续服务。这是安全的失败方式；要靠 `progressDeadlineSeconds` 和告警（alerting）发现它。
4. CrashLoopBackOff 的等待时间 10、20、40、80、160 秒，之后封顶 300 秒。看到这个状态你拿到的只是“反复崩溃”的事实，**原因要去看退出码和 `--previous` 日志**。

### 2.9 排障套路

**统一入口**：`kubectl get pod -o wide` → `kubectl describe pod`（看 Events 和 Last State）→ `kubectl logs [--previous]` → 必要时 `kubectl exec` / `kubectl debug`（临时调试容器）。

| 现象 | 常见原因 | 怎么确认 |
|---|---|---|
| Pending | requests 放不下、污点（taint）不被容忍、nodeSelector/亲和性（affinity）不匹配、PVC 未绑定（AZ 不对）、配额（quota）用完 | describe 的 Events：`0/N nodes are available: ...` |
| ImagePullBackOff | 镜像名/标签错、仓库无权限（imagePullSecrets）、网络不通、限流（rate limiting） | Events 里的拉取错误 |
| CrashLoopBackOff | 启动失败（配置缺失、依赖不通）、进程自己退出、探针（probe）杀死、OOM | 退出码：1/2 多为应用错误；137 = SIGKILL，多为 OOM（Last State 里 `OOMKilled`）；143 = SIGTERM；`logs --previous` |
| OOMKilled | 内存超 limit；JVM 堆 + 堆外超过容器限制；内存泄漏 | Last State、监控内存曲线；Java 要让 JVM 感知容器限制并留出堆外空间 |
| Evicted | 节点磁盘/内存压力 | 节点条件、QoS 类别 |
| Running 但不 Ready | readiness 失败 | describe 里的探针失败信息 |
| Service 不通 | 见 2.5 的顺序 | `get endpoints` |
| 滚动更新（rolling update）卡住 | 新版本不 Ready、资源不足、PDB 阻止 | `rollout status`、`describe` |

**节点 NotReady**：kubelet 失联、资源压力、网络。关注：节点上的 Pod 会在一段容忍时间后被驱逐（eviction）；有状态负载的行为见 2.4。

### 2.10 安全

- **RBAC**：角色（Role/ClusterRole）定义能做什么，绑定（RoleBinding/ClusterRoleBinding）定义谁能做。最小权限（least privilege）；避免给 `cluster-admin`；ServiceAccount 只给需要的权限，不用 default。
- **Pod 安全**：不以 root 运行、只读根文件系统、去掉不需要的 capability、禁止特权容器（Pod Security Standards / 准入策略）。
- **镜像**：固定版本或摘要（digest）、扫描漏洞、签名校验、最小基础镜像。
- **Secret**：见 2.6。**网络**：NetworkPolicy 默认拒绝。**审计（audit）日志**开启。
- **供应链与准入控制（admission control）**：用准入策略（Kyverno、OPA Gatekeeper、ValidatingAdmissionPolicy）强制规则。

### 2.11 EKS 相关（你在 AWS 上用 Kubernetes 的话）

- **控制平面（control plane）由 AWS 托管**，你管数据平面：托管节点组、Fargate、或 Karpenter 管理的节点。
- **VPC CNI**：Pod 直接使用 VPC 的 IP 地址（来自节点网卡的辅助 IP）。好处是 Pod 与 VPC 内资源直接互通；**代价是 IP 地址会耗尽**、每个实例类型能放的 Pod 数量有限。缓解：更大的子网（subnet）、前缀委派（prefix delegation）、自定义网络。
- **IRSA / EKS Pod Identity**：给**单个 ServiceAccount** 绑定 IAM 角色，Pod 拿到的是临时凭证（credentials），而不是继承节点角色。这是 EKS 上最小权限（least privilege）的关键。
- **AWS Load Balancer Controller**：Ingress → ALB，Service → NLB，可直接把 Pod IP 作为目标（ip 模式）。
- **升级**：控制平面先升，再升节点；注意 API 版本弃用；Kubernetes 版本支持期有限，要有升级节奏。

### 2.12 Kubernetes 面试题与答案要点

**K1. 讲讲 Kubernetes 的架构，以及 `kubectl apply` 之后发生了什么。**
见 2.2。重点是 apiserver 是唯一入口、etcd 存状态、一切通过 watch 协作，各控制器（controller）独立调和（reconcile）。

**K2. 什么是控制器模式 / 调和循环？**
不断比较期望状态（desired state）和实际状态并采取行动，使其收敛；是**水平触发**（level-triggered）而不是边沿触发，错过某个事件也没关系，下一轮仍会修正。Operator 就是用自定义资源（CRD）加自定义控制器把运维知识编码进去。

**K3. Deployment、ReplicaSet、Pod 的关系？回滚（rollback）怎么实现？**
Deployment 管 ReplicaSet（每个版本一个），ReplicaSet 管 Pod。回滚是把旧的 ReplicaSet 放大、新的缩小；`revisionHistoryLimit` 决定保留几个。

**K4. Deployment 和 StatefulSet 有什么区别？**
见 2.4：稳定标识、有序、独立存储。并说明有状态副本在节点失联时默认不会被自动搬走及原因。

**K5. liveness、readiness、startup 探针（probe）的区别？举出误用的后果。**
见 2.8。误用：liveness 检查外部依赖导致全体重启；readiness 与 liveness 用同一个端点；慢启动没有 startup 探针导致重启循环。

**K6. requests 和 limits 有什么区别？OOMKilled 和 CPU 限流（rate limiting）的区别？**
见 2.7。再补：调度看 requests；内存超限被杀，CPU 超限被限流；QoS 影响驱逐（eviction）顺序。

**K7. Pod 一直 Pending，你怎么排查？**
`describe pod` 的 Events：资源不足、污点（taint）、选择器、PVC、配额（quota）。然后看是扩容、调整 requests、还是改调度约束。

**K8. Pod 处于 CrashLoopBackOff，你怎么排查？**
先说明它只是现象；看 `describe` 的 Last State 与退出码、`logs --previous`；区分启动失败、OOM、探针杀死、依赖不可用；必要时用调试容器；回滚到上一个好版本止血。

**K9. 一个 Pod 被删除的完整过程？怎么做到发布时不丢请求？**
见 2.3：摘除与 SIGTERM 并行，需要 preStop 延迟、应用处理 SIGTERM、足够的 grace period；配合 readiness 与 PDB；上游负载均衡的连接排空（deregistration delay）。

**K10. Service 是怎么工作的？ClusterIP 是真实存在的 IP 吗？**
虚拟 IP，没有网卡绑定；kube-proxy 在每个节点设置 iptables/IPVS 规则，把访问虚拟 IP 的流量 DNAT 到某个后端 Pod。后端列表由 EndpointSlice 提供，只含 Ready 的 Pod。

**K11. Ingress 和 Service(LoadBalancer) 的区别？**
LoadBalancer 每个 Service 一个外部负载均衡（四层，成本高）；Ingress 一个入口按主机/路径七层路由（routing）到多个 Service，需要控制器。

**K12. HPA 的原理和前提？为什么扩容没生效？**
见 2.8。排查：指标是否可用（metrics-server）、是否设置了 requests、是否已到 maxReplicas、是否在容忍区间内、新 Pod 是否因资源不足 Pending（需要节点扩容）、冷却/稳定窗口。

**K13. 滚动更新（rolling update）参数怎么设？如何保证更新安全？**
maxSurge/maxUnavailable；readiness 探针；`minReadySeconds`；`progressDeadlineSeconds`；PDB；金丝雀或蓝绿配合服务网格或 Ingress 的权重；自动回滚由外部工具（Argo Rollouts、Flagger）实现。

**K14. 如何让副本分散到不同的 AZ？**
拓扑分布约束（topology spread constraints，`topologySpreadConstraints`，topologyKey 为 zone）或 Pod 反亲和性（affinity）；再配合 PDB。

**K15. 污点与容忍、亲和性分别解决什么？**
污点是节点排斥不合适的 Pod，容忍只是准许；亲和性是 Pod 主动选择位置。专用节点要“污点 + 亲和性”配合才能保证“专用”。

**K16. ConfigMap 更新后 Pod 会自动生效吗？**
环境变量方式不会；卷挂载方式最终会更新但应用要重新读取；`subPath` 挂载不会更新。常见做法：把配置哈希放进 Pod 模板注解，配置变就触发滚动更新。

**K17. Secret 安全吗？怎么加强？**
默认只是 base64。启用 etcd 静态加密（encryption at rest）或 KMS 提供者；RBAC 限制；不要写进镜像或日志；使用外部机密管理（如 Secrets Store CSI Driver）。

**K18. 解释 RBAC，如何给应用最小权限（least privilege）？**
见 2.10；每个应用独立 ServiceAccount，只绑定需要的 Role；在 EKS 上用 IRSA/Pod Identity 获取云权限。

**K19. etcd 出问题会怎样？**
etcd 不可用时，集群的写操作（包括创建、调度、扩缩）停止；已运行的 Pod 通常继续运行（数据平面不依赖实时访问 etcd），但无法自愈或变更。所以要备份 etcd、奇数个成员、独立磁盘。托管服务（EKS）替你做了这些。

**K20. 如何做多租户隔离（tenant isolation）？**
命名空间（namespace） + ResourceQuota/LimitRange + NetworkPolicy + RBAC + Pod 安全 + 节点池隔离（污点）；强隔离需求用多集群或虚拟集群，因为共享内核与控制平面（control plane）的隔离是“软”的。

**K21. 节点升级/排空时如何不影响服务？**
`kubectl drain` 受 PDB 约束；副本数大于 PDB 下限；Pod 反亲和；优雅终止（graceful shutdown）；先加新节点再排旧节点。

**K22. 你怎么做 Kubernetes 的可观测性（observability）？**
指标（Prometheus：golden signals、USE/RED）、日志（集中收集）、追踪（OpenTelemetry）、事件；告警（alerting）基于症状（延迟、错误率）而不是原因；对控制平面和节点也要监控。

**K23. 镜像和启动慢，怎么优化？**
小镜像、多阶段构建、层缓存（cache）、镜像预拉取、使用镜像仓库就近缓存、按需延迟加载；同时避免每次部署都 `Always` 拉取大镜像。

**K24. 什么时候不该用 Kubernetes？**
服务很少、团队小、没人维护集群、负载简单。托管的容器服务（ECS/Fargate、Cloud Run 类）或 PaaS 更省心。Kubernetes 的复杂度是实打实的成本，要说出这个判断。

### 2.13 设计题（Kubernetes 视角）

**设计题：把一个单体应用迁移到 Kubernetes，做到零停机发布和自动扩缩容**

1. **容器化**：无状态化（会话放缓存（cache），文件放对象存储（object storage）），配置外置（环境变量/ConfigMap），日志输出到标准输出，处理 SIGTERM。
2. **部署**：Deployment，多副本，requests/limits 依据压测设置；readiness 探针（probe）检查“能否接流量”，startup 探针处理慢启动，liveness 只检查进程自身。
3. **发布**：滚动更新（rolling update），maxUnavailable 为 0；PDB；`preStop` + 优雅终止（graceful shutdown）；金丝雀（按权重逐步放量，看错误率与延迟，自动回滚（rollback））。
4. **弹性**：HPA（CPU 或请求速率/队列长度等自定义指标（metrics）），加上 Cluster Autoscaler/Karpenter；设置最大副本与预算（budget）上限。
5. **高可用**：跨 AZ 拓扑分布；多个节点池；数据库放托管服务（Kubernetes 里跑数据库要慎重）。
6. **安全**：RBAC、IRSA、NetworkPolicy、Pod 安全、镜像扫描、机密外置。
7. **可观测**：指标、日志、追踪（trace）、SLO 与告警（alerting）；发布时的自动化验证。
8. **取舍与风险**：学习曲线、集群升级节奏、IP 耗尽（EKS）、成本（节点利用率）；先迁一个低风险服务验证流程。


---

## 三、MySQL：InnoDB 的内部机制与 SQL

> 本部分的实验全部在**真实的 MySQL 8.0.46**（InnoDB，默认隔离级别 REPEATABLE READ）上运行，输出原样贴出。耗时数字取决于机器，只看相对大小；并发实验里“哪个事务被选为死锁牺牲者”等细节每次运行可能不同。

### 3.1 为什么 MySQL 面试总是问到存储引擎

写 SQL 不难，难的是**同一条 SQL 为什么这次快、下次慢；为什么两个事务（transaction）会互相卡住；为什么主从数据不一致**。这些问题的答案都在存储引擎（InnoDB）里：数据怎么存（B+ 树、页）、怎么保证不丢（日志）、怎么并发（MVCC 与锁）、怎么复制（binlog）。面试官用这几块判断你是“会用”还是“懂”。

### 3.2 InnoDB 全景

一次 `UPDATE` 在 InnoDB 里大致经历：

1. 在**缓冲池（buffer pool）**里找到数据页（不在就从磁盘读入）。缓冲池是内存里的页缓存（cache），使用改进的 LRU（分为“新”区和“老”区，防止一次大表扫描把热数据全冲掉）。
2. 修改前，把旧版本写入**回滚日志（undo log）**：用于回滚（rollback），也用于 MVCC 读旧版本。
3. 在内存里修改页（此时是“脏页”），同时把这次物理修改写入**重做日志（redo log）**。
4. 事务（transaction）提交时，**redo log 刷盘**（由 `innodb_flush_log_at_trx_commit` 控制）。此后即使崩溃，重启时可以用 redo log 重放（replay）恢复。这就是**预写日志（WAL, write-ahead logging）**：先写日志，后写数据页，脏页由后台线程慢慢刷。
5. 在 MySQL Server 层，还有**二进制日志（binlog）**，记录逻辑变更，用于主从复制（replication）和按时间点恢复（PITR, point-in-time recovery）。redo log 和 binlog 通过**两阶段提交（two-phase commit）**保持一致：先写 redo（prepare）→ 写 binlog → 再写 redo（commit）。崩溃恢复（crash recovery）时，若 redo 处于 prepare 状态，则看 binlog 里是否有对应记录，有则提交，没有则回滚。这样主库和从库（用 binlog）不会出现“主库有、从库没有”的偏差。
6. **双写缓冲（doublewrite buffer）**：InnoDB 页是 16KB，操作系统/磁盘不保证 16KB 原子写。写数据页前先写一份到双写区，若崩溃时页写了一半（torn page），可用双写区的完整副本修复。
7. **修改缓冲（change buffer）**：对不在缓冲池里的**非唯一二级索引（secondary index）页**的修改，先记在缓冲里，之后读到该页时再合并，减少随机写。

**两个关键参数（面试高频）**

- `innodb_flush_log_at_trx_commit`：1（默认）每次提交都刷盘，最安全；2 提交时写到操作系统缓存，每秒刷盘，崩溃（整机）可能丢约 1 秒；0 更激进。
- `sync_binlog`：1 表示每次提交都同步 binlog。要“不丢数据”，通常两个都设为 1（俗称双一）。代价是写延迟。

### 3.3 索引：B+ 树、聚簇索引、回表

**为什么用 B+ 树**：磁盘（或页）读一次很贵，所以要让“树高”尽可能低。B+ 树的内部节点只存键和指针，一个 16KB 的页能放上千个键，树的扇出（fan-out）很大。叶子节点存数据，并用链表连起来，所以范围查询和排序很快。

**容量估算（面试常问）**：假设主键是 8 字节的 BIGINT，指针约 6 字节，一个内部节点大约放 16KB ÷ 14B ≈ 1170 个指针；叶子页放行数据，假设一行 1KB，则每页约 16 行。三层树：1170 × 1170 × 16 ≈ 2190 万行；四层可以到几百亿行的量级。结论：**千万级以下的表，一次主键查找通常只需 3 层，也就是 3 次页访问**，其中根和上层几乎总在缓冲池（buffer pool）里。这是估算，行大小变了结果就变了，不要说成定论。

**聚簇索引（clustered index）与二级索引（secondary index）**

- InnoDB 的表**就是**按主键组织的 B+ 树：叶子节点存整行数据。没有主键时选第一个非空唯一索引，再没有则隐藏一个行 ID。
- 二级索引的叶子存的是“索引列 + 主键值”。用二级索引查询其他列，要先在二级索引找到主键，再回到聚簇索引取整行，这一步叫**回表（table lookup, or bookmark lookup）**。
- **覆盖索引（covering index）**：查询要的列全在索引里，不用回表，`EXPLAIN` 的 Extra 里显示 `Using index`。
- 由此：**主键应该短、递增**。二级索引里每条都带着主键，主键长则所有索引都变大；随机主键（如随机 UUID）会让插入落在随机的页，导致**页分裂（page split）**和碎片。用自增或有序 ID（雪花 ID、UUIDv7）。
- **联合索引与最左前缀（leftmost prefix）**：`(a,b,c)` 的索引能支持 `a`、`a,b`、`a,b,c` 的查找，不能直接支持只用 `b`。**范围条件之后的列无法继续用于等值定位**（但可以用于索引下推）。
- **索引下推（ICP, index condition pushdown）**：存储引擎在遍历索引时就用索引列过滤，减少回表次数。`Extra` 里显示 `Using index condition`。
- **选择性（selectivity）**：区分度低的列（比如性别）单独建索引意义不大。
- 索引不是越多越好：每个索引都增加写入成本和空间。

**实验 1：用真实的 EXPLAIN 看索引**

```python
"""实验 1：索引到底带来什么？哪些写法会让索引失效？
用真实 MySQL 的 EXPLAIN 看执行计划，并实测耗时。
"""
import time
from mysql_common import connect, ensure_db, rows

ensure_db()
c = connect()
cur = c.cursor()
cur.execute("DROP TABLE IF EXISTS orders")
cur.execute("""CREATE TABLE orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  status VARCHAR(16) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  amount INT NOT NULL,
  created_at DATETIME NOT NULL,
  note VARCHAR(100) NOT NULL DEFAULT ''
) ENGINE=InnoDB""")
cur.execute("SET SESSION cte_max_recursion_depth=1000000")  # 递归 CTE 默认最多 1000 层
# 造 20 万行：用户 1..5000，状态 4 种，手机号是字符串
cur.execute("""INSERT INTO orders (user_id,status,phone,amount,created_at)
 WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i+1 FROM n WHERE i<200000)
 SELECT (i*7919)%5000+1, ELT(i%4+1,'new','paid','shipped','done'),
        CONCAT('1380000', LPAD(i%100000,5,'0')),
        i%1000, TIMESTAMP('2026-01-01') + INTERVAL i MINUTE FROM n""")
cur.execute("ANALYZE TABLE orders")
cur.fetchall()


def plan(sql):
    r = rows(c, "EXPLAIN " + sql)[0]
    # id, select_type, table, partitions, type, possible_keys, key, key_len, ref, rows, filtered, Extra
    return f"type={r[4]:<6} key={str(r[6]):<14} rows≈{r[9]:<7} Extra={r[11]}"


def timeit(sql, n=5):
    t = time.perf_counter()
    for _ in range(n):
        rows(c, sql)
    return (time.perf_counter() - t) / n * 1000


def show(title, sql):
    print(f"\n[{title}]\n  {sql}\n  {plan(sql)}   平均 {timeit(sql):.1f} ms")


Q = "SELECT id FROM orders WHERE user_id=42"
show("没有索引", Q)
cur.execute("CREATE INDEX idx_user ON orders(user_id)")
cur.execute("ANALYZE TABLE orders"); cur.fetchall()
show("加了 idx_user", Q)

print("\n=== 联合索引与最左前缀 ===")
cur.execute("CREATE INDEX idx_user_status_created ON orders(user_id,status,created_at)")
cur.execute("ANALYZE TABLE orders"); cur.fetchall()
show("用到前两列", "SELECT id FROM orders WHERE user_id=42 AND status='paid'")
show("跳过最左列 user_id（只查 status）", "SELECT id FROM orders WHERE status='paid' AND created_at>'2026-03-01'")

print("\n=== 让索引失效的常见写法 ===")
cur.execute("CREATE INDEX idx_phone ON orders(phone)")
cur.execute("CREATE INDEX idx_created ON orders(created_at)")
cur.execute("ANALYZE TABLE orders"); cur.fetchall()
show("正确：字符串列用字符串比较", "SELECT id FROM orders WHERE phone='138000012345'")
show("隐式类型转换：字符串列拿数字比较", "SELECT id FROM orders WHERE phone=13800012345")
show("在列上套函数", "SELECT id FROM orders WHERE DATE(created_at)='2026-03-01'")
show("改写成范围查询", "SELECT id FROM orders WHERE created_at>='2026-03-01' AND created_at<'2026-03-02'")
show("前导通配符 LIKE '%x'", "SELECT id FROM orders WHERE phone LIKE '%2345'")
show("前缀匹配 LIKE 'x%'", "SELECT id FROM orders WHERE phone LIKE '1380000123%'")

print("\n=== 覆盖索引（Using index）与回表 ===")
show("只查索引里有的列 -> 覆盖索引", "SELECT user_id,status FROM orders WHERE user_id=42")
show("多查一个 amount -> 要回表", "SELECT user_id,status,amount FROM orders WHERE user_id=42")

print("\n=== 排序 ===")
show("ORDER BY 无合适索引 -> filesort", "SELECT id FROM orders WHERE status='paid' ORDER BY amount LIMIT 10")
show("WHERE 等值 + ORDER BY 命中联合索引后续列", "SELECT id FROM orders WHERE user_id=42 AND status='paid' ORDER BY created_at LIMIT 10")

print("\n=== 深分页 ===")
show("OFFSET 150000", "SELECT id,amount FROM orders ORDER BY id LIMIT 10 OFFSET 150000")
show("游标（keyset）：记住上一页最后的 id", "SELECT id,amount FROM orders WHERE id>150000 ORDER BY id LIMIT 10")
cur.execute("DROP TABLE orders")
```

运行结果（20 万行）：

```text
[没有索引]
  SELECT id FROM orders WHERE user_id=42
  type=ALL    key=None           rows≈199432  Extra=Using where   平均 31.2 ms

[加了 idx_user]
  SELECT id FROM orders WHERE user_id=42
  type=ref    key=idx_user       rows≈40      Extra=Using index   平均 0.4 ms

=== 联合索引与最左前缀 ===

[用到前两列]
  SELECT id FROM orders WHERE user_id=42 AND status='paid'
  type=ref    key=idx_user_status_created rows≈1       Extra=Using index   平均 0.4 ms

[跳过最左列 user_id（只查 status）]
  SELECT id FROM orders WHERE status='paid' AND created_at>'2026-03-01'
  type=index  key=idx_user_status_created rows≈199432  Extra=Using where; Using index   平均 68.2 ms

=== 让索引失效的常见写法 ===

[正确：字符串列用字符串比较]
  SELECT id FROM orders WHERE phone='138000012345'
  type=ref    key=idx_phone      rows≈2       Extra=Using index   平均 0.3 ms

[隐式类型转换：字符串列拿数字比较]
  SELECT id FROM orders WHERE phone=13800012345
  type=index  key=idx_phone      rows≈199432  Extra=Using where; Using index   平均 37.3 ms

[在列上套函数]
  SELECT id FROM orders WHERE DATE(created_at)='2026-03-01'
  type=index  key=idx_created    rows≈199432  Extra=Using where; Using index   平均 39.8 ms

[改写成范围查询]
  SELECT id FROM orders WHERE created_at>='2026-03-01' AND created_at<'2026-03-02'
  type=range  key=idx_created    rows≈1440    Extra=Using where; Using index   平均 3.9 ms

[前导通配符 LIKE '%x']
  SELECT id FROM orders WHERE phone LIKE '%2345'
  type=index  key=idx_phone      rows≈199432  Extra=Using where; Using index   平均 48.8 ms

[前缀匹配 LIKE 'x%']
  SELECT id FROM orders WHERE phone LIKE '1380000123%'
  type=range  key=idx_phone      rows≈200     Extra=Using where; Using index   平均 0.9 ms

=== 覆盖索引（Using index）与回表 ===

[只查索引里有的列 -> 覆盖索引]
  SELECT user_id,status FROM orders WHERE user_id=42
  type=ref    key=idx_user_status_created rows≈40      Extra=Using index   平均 0.4 ms

[多查一个 amount -> 要回表]
  SELECT user_id,status,amount FROM orders WHERE user_id=42
  type=ref    key=idx_user       rows≈40      Extra=None   平均 0.9 ms

=== 排序 ===

[ORDER BY 无合适索引 -> filesort]
  SELECT id FROM orders WHERE status='paid' ORDER BY amount LIMIT 10
  type=ALL    key=None           rows≈199432  Extra=Using where; Using filesort   平均 46.1 ms

[WHERE 等值 + ORDER BY 命中联合索引后续列]
  SELECT id FROM orders WHERE user_id=42 AND status='paid' ORDER BY created_at LIMIT 10
  type=ref    key=idx_user_status_created rows≈1       Extra=Using index   平均 0.4 ms

=== 深分页 ===

[OFFSET 150000]
  SELECT id,amount FROM orders ORDER BY id LIMIT 10 OFFSET 150000
  type=index  key=PRIMARY        rows≈150010  Extra=None   平均 30.3 ms

[游标（keyset）：记住上一页最后的 id]
  SELECT id,amount FROM orders WHERE id>150000 ORDER BY id LIMIT 10
  type=range  key=PRIMARY        rows≈97542   Extra=Using where   平均 0.6 ms
```

怎么读这些结果（这些是重点，而且有一个容易误会的细节）：

1. **没有索引 31.2 ms，加了索引 0.4 ms**。`type=ALL` 是全表扫描（full table scan），`type=ref` 是按索引等值查找。
2. 我的查询只选 `id`，而 `id`（主键）本来就在每个二级索引里，所以查询被**覆盖**了。因此“失效”的写法没有显示 `type=ALL`，而是 **`type=index`**：这表示**扫描了整个索引**，仍然是全量扫描，只是扫的是更小的索引而不是整张表。**看到 `type=index` 且 rows 接近全表，同样要警惕。** 如果我选了 `*`，这些就会变成 `ALL`。
3. **跳过最左列**：`WHERE status=... AND created_at>...`，联合索引是 `(user_id,status,created_at)`，没法定位，只能扫描整个索引（68.2 ms，对比 0.4 ms）。
4. **隐式类型转换**：`phone` 是字符串列，拿数字 `13800012345` 去比较，MySQL 会把**列**转成数字再比较，索引用（citation）不上（37.3 ms 对 0.3 ms）。反过来（数字列拿字符串比较）则是把字符串转成数字，索引仍可用。这个坑在生产里非常常见。
5. **在列上套函数**（`DATE(created_at)=...`）索引失效；改写成范围查询（`>= ... AND < ...`）后用上 `range`，从 39.8 ms 降到 3.9 ms。8.0 支持函数索引，但最好先从改写 SQL 做起。
6. **前导通配符** `LIKE '%2345'` 用不了 B+ 树的有序性；**前缀匹配** `LIKE '1380000123%'` 可以。
7. **覆盖索引**：只选 `user_id,status` 时 Extra 是 `Using index`，换成多选一个 `amount` 就要回表。
8. **排序**：`ORDER BY amount` 没有合适索引，出现 `Using filesort`（需要额外排序）；而 `WHERE user_id=? AND status=? ORDER BY created_at` 正好命中联合索引的后续列，索引本身有序，直接读出，不用排序。
9. **深分页（deep pagination）**：`OFFSET 150000` 要先读出再丢弃前 15 万行（30.3 ms）；用“记住上一页最后一个 id”的**游标分页（keyset pagination）**直接定位（0.6 ms）。代价是不能随意跳页，需要稳定的排序键。
   - 注意 EXPLAIN 的 `rows` 是**估算值**，游标分页那一行显示约 97542，是因为优化器按范围估算、没把 `LIMIT` 算进去，实际只读 10 行（耗时 0.6 ms 可以证明）。**EXPLAIN 的 rows 不等于实际读取行数；要看真实情况用 `EXPLAIN ANALYZE`（8.0.18+）。**

**EXPLAIN 速查**

- `type`（访问方式，由好到差）：`const`/`system`（主键或唯一索引等值）→ `eq_ref`（连接时按唯一键）→ `ref`（非唯一索引等值）→ `range`（范围）→ `index`（全索引扫描）→ `ALL`（全表扫描）。
- `key`：实际用的索引；`possible_keys`：可能用的；`key_len`：用了联合索引的前几列（可推算）。
- `rows`：估算扫描行数；`filtered`：条件过滤后剩余的估算比例。
- `Extra`：`Using index`（覆盖）、`Using where`、`Using index condition`（ICP）、`Using filesort`（额外排序）、`Using temporary`（临时表，常见于 GROUP BY/DISTINCT 无合适索引）。

### 3.4 事务、隔离级别与 MVCC

**ACID**：原子性（atomicity，靠 undo log）、一致性（consistency，靠约束和应用）、隔离性（isolation，靠锁和 MVCC）、持久性（durability，靠 redo log）。

**并发读写会出什么问题**

- **脏读（dirty read）**：读到别人未提交的修改。
- **不可重复读（non-repeatable read）**：同一事务（transaction）内两次读同一行，结果不同（别人改并提交了）。
- **幻读（phantom read）**：同一事务内两次按条件查询，第二次多出（或少了）行。

**四个隔离级别（isolation level）**（SQL 标准）：READ UNCOMMITTED、READ COMMITTED、REPEATABLE READ、SERIALIZABLE。**MySQL InnoDB 默认是 REPEATABLE READ**（很多其他数据库默认 READ COMMITTED，这也是面试常问的差异；很多互联网公司为减少间隙锁（gap lock）和死锁（deadlock），会把它改成 READ COMMITTED）。

**MVCC（Multi-Version Concurrency Control，多版本并发控制）怎么做到“读不阻塞写，写不阻塞读”**

- 每行有隐藏列：最后修改它的事务 ID，以及指向 undo log 里旧版本的指针；旧版本串成一条**版本链（version chain）**。
- 事务读取时，会得到一个**读视图（ReadView）**：记录“此刻有哪些事务还没提交”。读一行时，沿版本链找到**对这个读视图可见的最新版本**。
- **REPEATABLE READ**：读视图在事务里**第一次读**时创建，之后一直用它，所以整个事务看到的是同一个快照。**READ COMMITTED**：**每条语句**都新建读视图，所以能读到别人刚提交的。
- **快照读（snapshot read） vs 当前读（current read）**：普通 `SELECT` 是快照读（用 MVCC，不加锁）；`SELECT ... FOR UPDATE`、`FOR SHARE`、`UPDATE`、`DELETE`、`INSERT` 是**当前读**，读最新已提交版本并加锁。**同一事务里混用两者，会看到“不一致”的现象**，这就是 REPEATABLE READ 下幻读讨论的核心。
- 长事务的代价：它的读视图要求保留很久以前的旧版本，undo log 无法清理（purge），history list length 增长，查询变慢、空间膨胀。**所以要避免长事务和“开了事务却长时间不提交”。**

**实验 2：真实 MySQL 上看隔离级别、幻读、间隙锁**

```python
"""实验 2：MVCC、隔离级别、间隙锁。两个连接 A、B 交替执行，观察 MySQL 的真实行为。
锁等待超时设成 2 秒：B 被 A 的锁挡住时，2 秒后报错，就说明“被锁住了”。
"""
import pymysql
from mysql_common import connect, ensure_db, rows

ensure_db()


def fresh():
    c = connect()
    cur = c.cursor()
    cur.execute("DROP TABLE IF EXISTS acct")
    cur.execute("CREATE TABLE acct (id INT PRIMARY KEY, name VARCHAR(10), bal INT, KEY k_bal(bal)) ENGINE=InnoDB")
    cur.execute("INSERT INTO acct VALUES (1,'a',100),(5,'b',500),(10,'c',1000)")
    return c


def pair(level):
    a, b = connect(autocommit=False), connect(autocommit=False)
    for x in (a, b):
        x.cursor().execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {level}")
        x.cursor().execute("SET SESSION innodb_lock_wait_timeout=2")
    return a, b


def try_sql(conn, sql):
    try:
        conn.cursor().execute(sql)
        return "成功"
    except pymysql.err.OperationalError as e:
        return f"被锁住，报错 {e.args[0]}（{e.args[1][:28]}…）"


print("=== A. 不可重复读：REPEATABLE READ 与 READ COMMITTED 的区别 ===")
for level in ("REPEATABLE READ", "READ COMMITTED"):
    fresh().close()
    a, b = pair(level)
    a.cursor().execute("BEGIN")
    first = rows(a, "SELECT bal FROM acct WHERE id=1")[0][0]
    b.cursor().execute("UPDATE acct SET bal=999 WHERE id=1"); b.commit()
    second = rows(a, "SELECT bal FROM acct WHERE id=1")[0][0]
    print(f"{level:<16} A 第一次读到 {first}，B 提交修改后 A 第二次读到 {second}")
    a.commit(); b.close(); a.close()

print("\n=== B. 幻读：快照读看不到，当前读看得到（REPEATABLE READ）===")
fresh().close()
a, b = pair("REPEATABLE READ")
a.cursor().execute("BEGIN")
print("A 快照读 count(*)  :", rows(a, "SELECT COUNT(*) FROM acct")[0][0])
b.cursor().execute("INSERT INTO acct VALUES (20,'d',2000)"); b.commit()
print("B 插入一行并提交后")
print("A 快照读 count(*)  :", rows(a, "SELECT COUNT(*) FROM acct")[0][0], "（还是旧快照）")
print("A 当前读 FOR UPDATE:", rows(a, "SELECT COUNT(*) FROM acct FOR UPDATE")[0][0], "（读到了最新数据）")
a.cursor().execute("UPDATE acct SET name='x' WHERE id=20")
print("A 能 UPDATE 一行自己“看不见”的数据；更新之后快照读 count(*) =", rows(a, "SELECT COUNT(*) FROM acct")[0][0])
a.commit(); a.close(); b.close()

print("\n=== C. 间隙锁：A 锁住范围，B 往里插入 ===")
for level in ("REPEATABLE READ", "READ COMMITTED"):
    fresh().close()
    a, b = pair(level)
    a.cursor().execute("BEGIN")
    a.cursor().execute("SELECT * FROM acct WHERE id BETWEEN 2 AND 8 FOR UPDATE")  # 只有 id=5 存在
    print(f"[{level}] A 对 id BETWEEN 2 AND 8 加 FOR UPDATE（实际只有 id=5 这一行）")
    print("   B 插入 id=3（在间隙里）:", try_sql(b, "INSERT INTO acct VALUES (3,'n',1)"))
    print("   B 更新 id=1（范围外） :", try_sql(b, "UPDATE acct SET bal=bal+1 WHERE id=1"))
    print("   B 插入 id=12（范围外）:", try_sql(b, "INSERT INTO acct VALUES (12,'n',1)"))
    a.rollback(); b.rollback(); a.close(); b.close()

print("\n=== D. 没有索引的 WHERE 会锁住整张表（RR 下）===")
fresh().close()
a, b = pair("REPEATABLE READ")
a.cursor().execute("BEGIN")
a.cursor().execute("SELECT * FROM acct WHERE name='b' FOR UPDATE")   # name 上没有索引
print("A: SELECT ... WHERE name='b' FOR UPDATE（name 无索引，只命中 id=5 一行）")
print("   B 更新 id=1（和 A 要的行毫无关系）:", try_sql(b, "UPDATE acct SET bal=bal+1 WHERE id=1"))
a.rollback(); b.rollback(); a.close(); b.close()
fresh().close()
a, b = pair("REPEATABLE READ")
a.cursor().execute("BEGIN")
a.cursor().execute("SELECT * FROM acct WHERE id=5 FOR UPDATE")        # 主键等值，只锁一行
print("A: SELECT ... WHERE id=5 FOR UPDATE（主键等值）")
print("   B 更新 id=1:", try_sql(b, "UPDATE acct SET bal=bal+1 WHERE id=1"))
print("   B 更新 id=5:", try_sql(b, "UPDATE acct SET bal=bal+1 WHERE id=5"))
a.rollback(); b.rollback(); a.close(); b.close()
```

运行结果：

```text
=== A. 不可重复读：REPEATABLE READ 与 READ COMMITTED 的区别 ===
REPEATABLE READ  A 第一次读到 100，B 提交修改后 A 第二次读到 100
READ COMMITTED   A 第一次读到 100，B 提交修改后 A 第二次读到 999

=== B. 幻读：快照读看不到，当前读看得到（REPEATABLE READ）===
A 快照读 count(*)  : 3
B 插入一行并提交后
A 快照读 count(*)  : 3 （还是旧快照）
A 当前读 FOR UPDATE: 4 （读到了最新数据）
A 能 UPDATE 一行自己“看不见”的数据；更新之后快照读 count(*) = 4

=== C. 间隙锁：A 锁住范围，B 往里插入 ===
[REPEATABLE READ] A 对 id BETWEEN 2 AND 8 加 FOR UPDATE（实际只有 id=5 这一行）
   B 插入 id=3（在间隙里）: 被锁住，报错 1205（Lock wait timeout exceeded; …）
   B 更新 id=1（范围外） : 成功
   B 插入 id=12（范围外）: 成功
[READ COMMITTED] A 对 id BETWEEN 2 AND 8 加 FOR UPDATE（实际只有 id=5 这一行）
   B 插入 id=3（在间隙里）: 成功
   B 更新 id=1（范围外） : 成功
   B 插入 id=12（范围外）: 成功

=== D. 没有索引的 WHERE 会锁住整张表（RR 下）===
A: SELECT ... WHERE name='b' FOR UPDATE（name 无索引，只命中 id=5 一行）
   B 更新 id=1（和 A 要的行毫无关系）: 被锁住，报错 1205（Lock wait timeout exceeded; …）
A: SELECT ... WHERE id=5 FOR UPDATE（主键等值）
   B 更新 id=1: 成功
   B 更新 id=5: 被锁住，报错 1205（Lock wait timeout exceeded; …）
```

逐条解读：

- **A**：REPEATABLE READ 下，A 在 B 提交修改之后再读仍是 100（快照没变）；READ COMMITTED 下读到 999。这是两者最直观的区别。
- **B**：REPEATABLE READ 下，B 插入一行并提交后，A 的快照读 `COUNT(*)` 还是 3，所以**快照读看不到幻影**；但当前读（`FOR UPDATE`）读到 4，并且 A 能更新“自己看不见”的那一行，更新之后这一行就对 A 可见了（因为是自己改的）。结论：**MySQL 的 REPEATABLE READ 对纯快照读避免了幻读，但一旦混用当前读，就能观察到“幻影”**。回答“MySQL 的 RR 能不能解决幻读”时，正确答案是：**快照读由 MVCC 解决，当前读由间隙锁/临键锁（next-key lock）防止别人插入；但事务内混用会出现可见性差异**。不要只答“能”或“不能”。
- **C**：A 对 `id BETWEEN 2 AND 8` 加 `FOR UPDATE`，而表里只有 `id=5` 一行。REPEATABLE READ 下，B 往间隙里插入 `id=3` **被锁住**（锁等待超时报 1205）；范围外的 `id=1` 更新、`id=12` 插入都成功。READ COMMITTED 下，连间隙里的 `id=3` 都能插入：**READ COMMITTED 没有间隙锁**。这就是为什么改成 READ COMMITTED 可以显著减少锁冲突和死锁（代价是不可重复读，以及 binlog 要用 ROW 格式）。
- **D**：`WHERE name='b' FOR UPDATE`，`name` 没有索引，只命中一行，但 B 更新毫不相干的 `id=1` 也**被锁住**。因为没有索引可用，InnoDB 要扫描聚簇索引（clustered index）的所有行，在 REPEATABLE READ 下对扫描过的每一行都加锁，等于锁了全表。而按主键等值 `id=5` 加锁，只锁这一行，B 更新 `id=1` 成功，更新 `id=5` 被锁。结论：**加锁读的 WHERE 条件必须走索引，否则小心“锁全表”。**

### 3.5 InnoDB 的锁

- **锁的粒度**：表锁、行锁。InnoDB 的行锁是**加在索引记录上**的，不是加在“行”本身；没有索引可用就退化成扫描所有记录并加锁（见实验 D）。
- **记录锁（record lock）**：锁住一条索引记录。**间隙锁（gap lock）**：锁住两条索引记录之间的“空隙”（不含记录本身），**只阻止别人往里插入**，间隙锁之间不互相冲突。**临键锁（next-key lock）**= 记录锁 + 该记录之前的间隙锁，是 REPEATABLE READ 下默认的加锁单位。
- **规律（简化版，以实验验证为准）**：对**唯一索引等值查询命中**的记录，退化成记录锁；未命中，则锁住所在的间隙；范围查询会加临键锁并可能锁到范围外的下一个记录之前的间隙；非唯一索引的等值查询会加临键锁，并在右侧再加一个间隙锁。
- **意向锁（intention lock）**：表级，表示事务（transaction）想在表内的行上加共享/排他锁，让“加表锁”的检查变快。一般不会成为你的问题。
- **插入意向锁**：插入前在间隙上加的一种特殊间隙锁；多个事务往同一间隙的不同位置插入互不阻塞。
- **元数据锁（MDL）**：DDL 与查询之间。**经典事故**：一个长事务（或没提交的查询）持有表的 MDL，这时有人执行 `ALTER TABLE`，DDL 排队等待；**排在它后面的所有普通查询也被 DDL 的等待请求挡住**，整张表看起来“卡死”。预防：DDL 前检查长事务，设置 `lock_wait_timeout`，用在线变更工具。
- **自增锁**、**唯一键冲突检查加的锁**等细节，面试官追问时再展开。

**死锁（deadlock）**

- 成因：多个事务以**不同顺序**请求彼此持有的锁，形成环。InnoDB 自动检测环，选一个“代价较小”的事务回滚（rollback，错误 1213），其余继续。
- 排查：`SHOW ENGINE INNODB STATUS` 的 `LATEST DETECTED DEADLOCK` 部分；也可以开启 `innodb_print_all_deadlocks`。
- 预防：所有事务**按固定顺序**访问表和行；事务尽量短；加锁读尽量走索引、精确到行；降低隔离级别（isolation level）到 READ COMMITTED（少了间隙锁）；批量更新分批；**应用层对 1213 做整个事务的重试（retry）**。

**实验 3：真实的死锁，以及“先读后写”的丢失更新**

```python
"""实验 3：死锁，以及“先读后写”的丢失更新（lost update）和三种修法。真实 MySQL。"""
import threading, time
import pymysql
from mysql_common import connect, ensure_db, rows

ensure_db()
c = connect()
cur = c.cursor()

print("=== A. 死锁：两个事务以相反顺序锁两行 ===")
cur.execute("DROP TABLE IF EXISTS acct")
cur.execute("CREATE TABLE acct (id INT PRIMARY KEY, bal INT) ENGINE=InnoDB")
cur.execute("INSERT INTO acct VALUES (1,100),(2,100)")
res = {}


def txn(name, first, second, barrier=None):
    conn = connect(autocommit=False)
    cu = conn.cursor()
    try:
        cu.execute("UPDATE acct SET bal=bal-1 WHERE id=%s", (first,))
        if barrier:
            barrier.wait()      # 保证两边都拿到第一把锁再去要第二把
        time.sleep(0.2)
        cu.execute("UPDATE acct SET bal=bal-1 WHERE id=%s", (second,))
        conn.commit(); res[name] = "提交成功"
    except pymysql.err.OperationalError as e:
        conn.rollback(); res[name] = f"被回滚，错误 {e.args[0]}（{e.args[1][:40]}）"
    finally:
        conn.close()


bar = threading.Barrier(2)
ts = [threading.Thread(target=txn, args=("T1 先锁1再锁2", 1, 2, bar)), threading.Thread(target=txn, args=("T2 先锁2再锁1", 2, 1, bar))]
[t.start() for t in ts]; [t.join() for t in ts]
for k, v in sorted(res.items()):
    print(f"  {k}: {v}")
print("  （InnoDB 检测到环，选一个代价小的事务回滚；应用要对 1213 重试整个事务）")
print("\n  --- 修法：所有事务按同一顺序（按 id 升序）加锁 ---")
res.clear()
ts = [threading.Thread(target=txn, args=("T1 先锁1再锁2", 1, 2)), threading.Thread(target=txn, args=("T2 也先锁1再锁2", 1, 2))]
[t.start() for t in ts]; [t.join() for t in ts]
for k, v in sorted(res.items()):
    print(f"  {k}: {v}")

print("\n=== B. 丢失更新：20 个线程各给同一账户 +1，重复 50 次 ===")
N_THREADS, N_EACH = 20, 50


def run(label, worker):
    c2 = connect(); cu2 = c2.cursor()
    cu2.execute("DROP TABLE IF EXISTS counter")
    cu2.execute("CREATE TABLE counter (id INT PRIMARY KEY, v INT, ver INT NOT NULL DEFAULT 0) ENGINE=InnoDB")
    cu2.execute("INSERT INTO counter (id,v) VALUES (1,0)")
    retries = [0]
    t0 = time.perf_counter()
    ths = [threading.Thread(target=worker, args=(retries,)) for _ in range(N_THREADS)]
    [t.start() for t in ths]; [t.join() for t in ths]
    v = rows(c2, "SELECT v FROM counter WHERE id=1")[0][0]
    extra = f"，乐观锁重试 {retries[0]} 次" if retries[0] else ""
    print(f"  {label:<34} 期望 {N_THREADS*N_EACH}，实际 {v}{extra}，耗时 {time.perf_counter()-t0:.2f}s")
    c2.close()


def naive(_):
    cn = connect(autocommit=False); cu = cn.cursor()
    for _ in range(N_EACH):
        cu.execute("SELECT v FROM counter WHERE id=1"); v = cu.fetchone()[0]   # 先读（普通快照读）
        cu.execute("UPDATE counter SET v=%s WHERE id=1", (v + 1,))             # 再写
        cn.commit()
    cn.close()


def for_update(_):
    cn = connect(autocommit=False); cu = cn.cursor()
    for _ in range(N_EACH):
        cu.execute("SELECT v FROM counter WHERE id=1 FOR UPDATE"); v = cu.fetchone()[0]
        cu.execute("UPDATE counter SET v=%s WHERE id=1", (v + 1,))
        cn.commit()
    cn.close()


def atomic(_):
    cn = connect(autocommit=False); cu = cn.cursor()
    for _ in range(N_EACH):
        cu.execute("UPDATE counter SET v=v+1 WHERE id=1")
        cn.commit()
    cn.close()


def optimistic(retries):
    cn = connect(autocommit=False); cu = cn.cursor()
    for _ in range(N_EACH):
        while True:
            cu.execute("SELECT v,ver FROM counter WHERE id=1"); v, ver = cu.fetchone(); cn.commit()
            n = cu.execute("UPDATE counter SET v=%s, ver=ver+1 WHERE id=1 AND ver=%s", (v + 1, ver))
            cn.commit()
            if n == 1:
                break
            retries[0] += 1
    cn.close()


run("先读后写（无保护）", naive)
run("SELECT ... FOR UPDATE（悲观锁）", for_update)
run("UPDATE v=v+1（原子更新）", atomic)
run("版本号 CAS（乐观锁）", optimistic)
```

运行结果：

```text
=== A. 死锁：两个事务以相反顺序锁两行 ===
  T1 先锁1再锁2: 提交成功
  T2 先锁2再锁1: 被回滚，错误 1213（Deadlock found when trying to get lock; ）
  （InnoDB 检测到环，选一个代价小的事务回滚；应用要对 1213 重试整个事务）

  --- 修法：所有事务按同一顺序（按 id 升序）加锁 ---
  T1 先锁1再锁2: 提交成功
  T2 也先锁1再锁2: 提交成功

=== B. 丢失更新：20 个线程各给同一账户 +1，重复 50 次 ===
  先读后写（无保护）                          期望 1000，实际 59，耗时 0.95s
  SELECT ... FOR UPDATE（悲观锁）         期望 1000，实际 1000，耗时 1.82s
  UPDATE v=v+1（原子更新）                 期望 1000，实际 1000，耗时 1.44s
  版本号 CAS（乐观锁）                       期望 1000，实际 1000，乐观锁重试 13124 次，耗时 6.70s
```

解读：

- **A**：T1 先锁 1 再锁 2，T2 先锁 2 再锁 1，必然形成环，InnoDB 回滚了 T2，T1 提交成功，错误码 1213。两边都**按相同顺序**（先 1 后 2）则都提交成功，没有死锁。哪个事务被选为牺牲者每次可能不同。
- **B**：20 个线程各加 50 次，期望 1000。**无保护的“先读后写”只得到几十（这次是 59，我另外几次跑出过 80、85，每次不同）**：多个事务读到同一个旧值，各自加一后写回，彼此覆盖，这就是**丢失更新（lost update）**。三种修法：
  1. `SELECT ... FOR UPDATE`（悲观锁（pessimistic locking））：读的时候就加行锁，别人等着。正确，但有锁等待。
  2. `UPDATE ... SET v = v + 1`（原子更新）：**最简单也最快**，让数据库在一条语句里完成“读-改-写”。能这样写就这样写。
  3. 版本号（version number） CAS（乐观锁（optimistic locking））：`UPDATE ... WHERE ver = ?`，影响行数为 0 则重试。这次竞争非常激烈，**重试了一万三千多次**，耗时最长。乐观锁适合**冲突少**的场景；热点行用它会白白浪费大量重试。
- 在这个实验里，三种正确做法的耗时在同一个量级，原子更新最快、乐观锁最慢，具体数字取决于机器。

### 3.6 日志、崩溃恢复与复制

**崩溃恢复（crash recovery）**：重启后，用 redo log 把已提交但脏页未刷盘的修改重放（replay，前滚）；用 undo log 回滚（rollback）未提交的事务（transaction）；两阶段提交（two-phase commit）决定 prepare 状态的事务去留。

**主从复制（replication）**

- 主库把变更写入 binlog；从库的 I/O 线程拉取并写入中继日志（relay log），SQL 线程（或多个并行 worker）重放。
- **binlog 格式**：STATEMENT（记录 SQL，遇到不确定函数会不一致）、ROW（记录行变更，默认，最可靠，体积更大）、MIXED。READ COMMITTED 下要用 ROW。
- **GTID**（全局事务标识）：用事务编号代替“文件+位置”，主从切换和故障恢复容易得多。
- **同步方式**：默认异步（asynchronous），主库提交即返回，主库宕机可能丢尚未传到从库的事务。**半同步（semi-sync）**：提交要等至少一个从库确认收到 binlog（`AFTER_SYNC` 模式下不丢已确认的事务），延迟增加；仍不是强一致（strong consistency）。**MySQL Group Replication / InnoDB Cluster**：基于 Paxos 类协议（protocol）的组复制，提供自动故障转移（failover）。
- **复制延迟（replication lag）** 的常见原因：从库单线程重放（可开启基于 LOGICAL_CLOCK 或 WRITESET 的并行复制）、主库有**大事务**、从库配置低或被大查询占用、从库 I/O 瓶颈。
- **读写分离（read/write splitting）的坑**：写后马上读从库，读到旧数据。解决：关键读走主库；会话级“读己之写（read-your-writes）”（写后一段时间内读主，或带上 GTID 等待从库追上）；接受最终一致（eventual consistency）并在产品层面处理。
- **主从切换的风险**：切换时丢数据（异步）、双主脑裂、应用连接串变更；需要工具（Orchestrator、MHA）或托管服务（RDS/Aurora）。

**备份与恢复**：逻辑备份（mysqldump，慢但可移植）、物理备份（Percona XtraBackup、RDS 快照，快）、加上 binlog 做**时间点恢复（PITR, point-in-time recovery）**。**没验证过能恢复的备份不算备份。**


### 3.7 表设计、大表与线上变更

- **范式（normalization）与反范式**：先按范式设计保证正确，再为读性能有选择地冗余；冗余字段要有同步机制。
- **字段类型**：用最小够用的类型；金额用 `DECIMAL` 或以“分”为单位的整数，不用浮点；时间用 `DATETIME`（范围大、不受时区影响）或 `TIMESTAMP`（2038 年问题，随会话时区转换）；字符串用 `utf8mb4`（`utf8` 在 MySQL 里是三字节的残缺版本，存不了 emoji）；尽量 `NOT NULL`（NULL 让索引和比较更复杂）。
- **主键**：见 3.3，短且递增。不要用业务字段（如手机号）当主键。分布式 ID 用雪花 ID 或有序 UUID。
- **`COUNT(*)`**：InnoDB 因为 MVCC 不能缓存（cache）精确行数，要扫描（会选最小的二级索引（secondary index））。大表上频繁 `COUNT(*)` 是性能隐患：改用近似值、计数表或缓存。`COUNT(1)` 与 `COUNT(*)` 没有实质区别；`COUNT(col)` 不统计 NULL。
- **在线 DDL（online DDL）**：8.0 的 `ALGORITHM=INSTANT` 可瞬间加列（有限制），`INPLACE` 不阻塞读写但仍消耗资源；大表改结构用 gh-ost 或 pt-online-schema-change，并避开 MDL 长事务（transaction，见 3.5）。
- **大表治理（governance）**：归档历史数据；分区表（按时间，便于整块删除，不是万能加速器）；**分库分表（sharding）**是最后的手段，因为它带来跨分片查询、分布式事务、全局唯一 ID、扩容迁移等一系列复杂度。先做：索引与 SQL 优化、读写分离（read/write splitting）、缓存、归档，再考虑分片。分片键要选访问最频繁、分布均匀的（比如用户 ID），并考虑一致性（consistency）哈希或预分片以便扩容。
- **批量写入**：多行 `INSERT`、合适的批量大小、避免大事务（会造成主从延迟、锁持有久）。
- **慢查询（slow query）排查流程**：开慢查询日志 → 找出最耗时/最频繁的语句 → `EXPLAIN`（必要时 `EXPLAIN ANALYZE`）→ 加索引或改写 → 对比 → 观察锁等待与缓冲池（buffer pool）命中率；线上用 `performance_schema`/`sys` 库或 RDS 的 Performance Insights。

### 3.8 SQL 手写题（在真实 MySQL 上验证过）

面试里一定会有一两道手写 SQL。这九道覆盖最常见的套路：排名、连续区间、窗口函数（window function）、去重（deduplication）、自连接（self join）、NULL 陷阱。

```python
"""实验 4：面试里常考的 SQL 手写题，在真实 MySQL 8.0 上跑一遍。每题先说考点，再给 SQL 和结果。"""
from mysql_common import connect, ensure_db, rows

ensure_db()
c = connect(); cur = c.cursor()
for t in ("emp", "login", "ord_", "dup"):
    cur.execute(f"DROP TABLE IF EXISTS {t}")
cur.execute("CREATE TABLE emp (id INT PRIMARY KEY, name VARCHAR(10), dept VARCHAR(10), salary INT, mgr INT)")
cur.execute("""INSERT INTO emp VALUES (1,'Ann','eng',300,NULL),(2,'Bob','eng',200,1),(3,'Cat','eng',200,1),
 (4,'Dan','eng',100,2),(5,'Eve','ops',150,1),(6,'Fay','ops',150,5),(7,'Gus','ops',90,5),(8,'Hal','hr',120,1)""")
cur.execute("CREATE TABLE login (uid INT, d DATE)")
cur.execute("""INSERT INTO login VALUES (1,'2026-10-01'),(1,'2026-10-02'),(1,'2026-10-03'),(1,'2026-10-05'),(1,'2026-10-06'),
 (2,'2026-10-01'),(2,'2026-10-03'),(2,'2026-10-04'),(2,'2026-10-04')""")
cur.execute("CREATE TABLE ord_ (id INT PRIMARY KEY, uid INT, amt INT, d DATE)")
cur.execute("""INSERT INTO ord_ VALUES (1,1,10,'2026-10-01'),(2,1,20,'2026-10-02'),(3,2,5,'2026-10-02'),
 (4,1,30,'2026-10-04'),(5,2,15,'2026-10-05'),(6,3,50,'2026-10-05')""")
cur.execute("CREATE TABLE dup (id INT PRIMARY KEY, email VARCHAR(20))")
cur.execute("INSERT INTO dup VALUES (1,'a@x'),(2,'b@x'),(3,'a@x'),(4,'c@x'),(5,'b@x'),(6,'a@x')")


def q(title, sql, note=""):
    print(f"\n【{title}】{note}\n{sql.strip()}")
    for r in rows(c, sql):
        print("  ", r)


q("1. 每个部门工资第 N 高（这里 N=2，并列不跳号）用 DENSE_RANK", """
SELECT dept,name,salary FROM (
  SELECT dept,name,salary, DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) rk FROM emp) t
WHERE rk=2""", "考点：窗口函数；RANK 与 DENSE_RANK 与 ROW_NUMBER 的区别")

q("1b. 三种排名函数的区别（eng 部门，工资 300/200/200/100）", """
SELECT name,salary,
 ROW_NUMBER() OVER w rn, RANK() OVER w rk, DENSE_RANK() OVER w drk
FROM emp WHERE dept='eng' WINDOW w AS (ORDER BY salary DESC)""")

q("2. 全公司第二高工资，没有就返回 NULL", """
SELECT (SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET 1) AS second_highest""",
  "考点：DISTINCT 去并列；用子查询包一层才能在没有第二高时得到 NULL")

q("3. 连续登录 3 天及以上的用户（gaps and islands）", """
SELECT uid, MIN(d) start_d, MAX(d) end_d, COUNT(*) days FROM (
  SELECT uid,d, DATE_SUB(d, INTERVAL DENSE_RANK() OVER (PARTITION BY uid ORDER BY d) DAY) grp
  FROM (SELECT DISTINCT uid,d FROM login) x) t
GROUP BY uid,grp HAVING COUNT(*)>=3""",
  "考点：日期减行号，连续的日期会得到同一个值；先 DISTINCT 去掉同一天重复登录")

q("4. 每个用户的累计消费和相邻两单的间隔", """
SELECT uid,d,amt,
 SUM(amt) OVER (PARTITION BY uid ORDER BY d, id) running_total,
 DATEDIFF(d, LAG(d) OVER (PARTITION BY uid ORDER BY d, id)) days_since_prev
FROM ord_ ORDER BY uid,d,id""", "考点：SUM() OVER、LAG")

q("5. 删除重复邮箱，每个邮箱只保留 id 最小的一行（先看会删哪些；DISTINCT 是因为 id=6 比 1 和 3 都大，会匹配两次）", """
SELECT DISTINCT d.id FROM dup d JOIN dup k ON d.email=k.email AND d.id>k.id ORDER BY d.id""",
  "考点：自连接；MySQL 不能在同一条语句里直接对被子查询的同一张表做 DELETE，要用 JOIN 形式")
cur.execute("DELETE d FROM dup d JOIN dup k ON d.email=k.email AND d.id>k.id")
q("5b. 删除之后", "SELECT id,email FROM dup ORDER BY id")

q("6. 没有下属的员工，以及每个经理有几个直接下属（自连接 / LEFT JOIN）", """
SELECT m.name, COUNT(e.id) reports FROM emp m LEFT JOIN emp e ON e.mgr=m.id GROUP BY m.id,m.name ORDER BY reports DESC, m.name""",
  "考点：LEFT JOIN 保留 0 个下属的人；COUNT(e.id) 不数 NULL，COUNT(*) 会数成 1")

q("7. 薪水高于本部门平均的人（相关子查询 vs 窗口函数，结果相同）", """
SELECT name,dept,salary FROM (SELECT name,dept,salary, AVG(salary) OVER (PARTITION BY dept) a FROM emp) t WHERE salary>a ORDER BY dept,name""")

q("8. 分组后过滤：WHERE 和 HAVING 的区别", """
SELECT dept, COUNT(*) n, AVG(salary) avg_sal FROM emp WHERE salary>=100 GROUP BY dept HAVING COUNT(*)>=2""",
  "WHERE 在分组前过滤行，HAVING 在分组后过滤组")

q("9. NULL 的陷阱：NOT IN 遇到 NULL", """
SELECT (SELECT COUNT(*) FROM emp WHERE id NOT IN (SELECT mgr FROM emp)) not_in_cnt,
       (SELECT COUNT(*) FROM emp e WHERE NOT EXISTS (SELECT 1 FROM emp x WHERE x.mgr=e.id)) not_exists_cnt""",
  "子查询里有 NULL 时 NOT IN 永远得不到 TRUE，结果是 0 行；NOT EXISTS 才是对的")
```

运行结果：

```text
【1. 每个部门工资第 N 高（这里 N=2，并列不跳号）用 DENSE_RANK】考点：窗口函数；RANK 与 DENSE_RANK 与 ROW_NUMBER 的区别
SELECT dept,name,salary FROM (
  SELECT dept,name,salary, DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) rk FROM emp) t
WHERE rk=2
   ('eng', 'Bob', 200)
   ('eng', 'Cat', 200)
   ('ops', 'Gus', 90)

【1b. 三种排名函数的区别（eng 部门，工资 300/200/200/100）】
SELECT name,salary,
 ROW_NUMBER() OVER w rn, RANK() OVER w rk, DENSE_RANK() OVER w drk
FROM emp WHERE dept='eng' WINDOW w AS (ORDER BY salary DESC)
   ('Ann', 300, 1, 1, 1)
   ('Bob', 200, 2, 2, 2)
   ('Cat', 200, 3, 2, 2)
   ('Dan', 100, 4, 4, 3)

【2. 全公司第二高工资，没有就返回 NULL】考点：DISTINCT 去并列；用子查询包一层才能在没有第二高时得到 NULL
SELECT (SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET 1) AS second_highest
   (200,)

【3. 连续登录 3 天及以上的用户（gaps and islands）】考点：日期减行号，连续的日期会得到同一个值；先 DISTINCT 去掉同一天重复登录
SELECT uid, MIN(d) start_d, MAX(d) end_d, COUNT(*) days FROM (
  SELECT uid,d, DATE_SUB(d, INTERVAL DENSE_RANK() OVER (PARTITION BY uid ORDER BY d) DAY) grp
  FROM (SELECT DISTINCT uid,d FROM login) x) t
GROUP BY uid,grp HAVING COUNT(*)>=3
   (1, datetime.date(2026, 10, 1), datetime.date(2026, 10, 3), 3)

【4. 每个用户的累计消费和相邻两单的间隔】考点：SUM() OVER、LAG
SELECT uid,d,amt,
 SUM(amt) OVER (PARTITION BY uid ORDER BY d, id) running_total,
 DATEDIFF(d, LAG(d) OVER (PARTITION BY uid ORDER BY d, id)) days_since_prev
FROM ord_ ORDER BY uid,d,id
   (1, datetime.date(2026, 10, 1), 10, Decimal('10'), None)
   (1, datetime.date(2026, 10, 2), 20, Decimal('30'), 1)
   (1, datetime.date(2026, 10, 4), 30, Decimal('60'), 2)
   (2, datetime.date(2026, 10, 2), 5, Decimal('5'), None)
   (2, datetime.date(2026, 10, 5), 15, Decimal('20'), 3)
   (3, datetime.date(2026, 10, 5), 50, Decimal('50'), None)

【5. 删除重复邮箱，每个邮箱只保留 id 最小的一行（先看会删哪些；DISTINCT 是因为 id=6 比 1 和 3 都大，会匹配两次）】考点：自连接；MySQL 不能在同一条语句里直接对被子查询的同一张表做 DELETE，要用 JOIN 形式
SELECT DISTINCT d.id FROM dup d JOIN dup k ON d.email=k.email AND d.id>k.id ORDER BY d.id
   (3,)
   (5,)
   (6,)

【5b. 删除之后】
SELECT id,email FROM dup ORDER BY id
   (1, 'a@x')
   (2, 'b@x')
   (4, 'c@x')

【6. 没有下属的员工，以及每个经理有几个直接下属（自连接 / LEFT JOIN）】考点：LEFT JOIN 保留 0 个下属的人；COUNT(e.id) 不数 NULL，COUNT(*) 会数成 1
SELECT m.name, COUNT(e.id) reports FROM emp m LEFT JOIN emp e ON e.mgr=m.id GROUP BY m.id,m.name ORDER BY reports DESC, m.name
   ('Ann', 4)
   ('Eve', 2)
   ('Bob', 1)
   ('Cat', 0)
   ('Dan', 0)
   ('Fay', 0)
   ('Gus', 0)
   ('Hal', 0)

【7. 薪水高于本部门平均的人（相关子查询 vs 窗口函数，结果相同）】
SELECT name,dept,salary FROM (SELECT name,dept,salary, AVG(salary) OVER (PARTITION BY dept) a FROM emp) t WHERE salary>a ORDER BY dept,name
   ('Ann', 'eng', 300)
   ('Eve', 'ops', 150)
   ('Fay', 'ops', 150)

【8. 分组后过滤：WHERE 和 HAVING 的区别】WHERE 在分组前过滤行，HAVING 在分组后过滤组
SELECT dept, COUNT(*) n, AVG(salary) avg_sal FROM emp WHERE salary>=100 GROUP BY dept HAVING COUNT(*)>=2
   ('eng', 4, Decimal('200.0000'))
   ('ops', 2, Decimal('150.0000'))

【9. NULL 的陷阱：NOT IN 遇到 NULL】子查询里有 NULL 时 NOT IN 永远得不到 TRUE，结果是 0 行；NOT EXISTS 才是对的
SELECT (SELECT COUNT(*) FROM emp WHERE id NOT IN (SELECT mgr FROM emp)) not_in_cnt,
       (SELECT COUNT(*) FROM emp e WHERE NOT EXISTS (SELECT 1 FROM emp x WHERE x.mgr=e.id)) not_exists_cnt
   (0, 5)
```

**每道题的套路总结**

1. **分组内第 N 高**：`DENSE_RANK() OVER (PARTITION BY ... ORDER BY ... DESC)`，再在外层过滤。`ROW_NUMBER` 不处理并列（强行排出先后），`RANK` 并列后跳号（1,2,2,4），`DENSE_RANK` 并列后不跳号（1,2,2,3）。要“并列都算第二”用 `DENSE_RANK`。
2. **全局第二高，没有时返回 NULL**：外面再包一层子查询，空结果会变成 NULL。
3. **连续区间（gaps and islands）**：把日期减去“按日期排的序号”，连续的日期会得到相同的值，按它分组。先 `DISTINCT` 去掉同一天重复的记录，否则序号会错。
4. **累计和与前后行**：`SUM() OVER (PARTITION BY ... ORDER BY ...)`、`LAG/LEAD`。注意排序键要能区分同一天的多条记录（这里加了 `id`），否则累计和的顺序不确定。
5. **删除重复行保留一行**：自连接 `ON 重复键相等 AND d.id > k.id`，删除 id 更大的。MySQL 不允许在 `DELETE` 的子查询里直接引用（citation）被删除的同一张表，用 `DELETE ... JOIN` 的形式。
6. **统计每个经理的下属数**：`LEFT JOIN` 保留没有下属的人；数 `COUNT(e.id)`（不数 NULL）而不是 `COUNT(*)`（会把没有下属的数成 1）。
7. **高于组内平均**：窗口函数 `AVG() OVER (PARTITION BY ...)` 一次扫描完成，比相关子查询清晰。
8. **WHERE 与 HAVING**：WHERE 在分组前过滤行（可以用索引），HAVING 在分组后过滤聚合结果。能放 WHERE 的条件不要放 HAVING。
9. **`NOT IN` 遇到 NULL**：`x NOT IN (1, NULL)` 的结果是 UNKNOWN，不是 TRUE，所以整个条件什么都选不出来（实验里得到 0）。用 `NOT EXISTS`（得到 5，正确）。同理，`= NULL` 永远不为真，要用 `IS NULL`。

**JOIN 要点**：INNER 只留匹配；LEFT 保留左表全部；`WHERE` 里对右表列的条件会把 LEFT JOIN 变成 INNER（要放在 `ON` 里）；MySQL 8.0.18 起支持哈希连接（hash join），之前主要是嵌套循环连接（nested loop）——被驱动表的连接列必须有索引。**小表驱动大表**是优化器通常会自己做的事，但统计信息不准时它会选错，可以用 `ANALYZE TABLE` 或索引提示作为最后手段。

### 3.9 MySQL 面试题与答案要点

**S1. 为什么 InnoDB 用 B+ 树而不是哈希、红黑树或 B 树？**
哈希不支持范围和排序；红黑树等二叉树太高，磁盘访问次数多；B 树的内部节点也存数据，扇出（fan-out）变小；B+ 树内部节点只存键，树更矮，叶子链表使范围扫描快。

**S2. 聚簇索引（clustered index）和二级索引（secondary index）的区别？什么是回表（table lookup, or bookmark lookup）？覆盖索引（covering index）呢？**
见 3.3。

**S3. 联合索引 (a,b,c) 下，哪些查询能用上索引？**
`a`；`a,b`；`a,b,c`；`a` 等值 + `b` 范围（`c` 不能再用于定位，可用于下推）；只用 `b` 或 `c` 不能定位；`a` 范围之后 `b` 无法定位。结合排序：`WHERE a=? ORDER BY b` 能用索引排序。写“能”之前请 EXPLAIN 验证。

**S4. 哪些情况下索引会失效？**
列上用函数或运算、隐式类型转换（字符串列比数字）、前导通配符、`OR` 的一边没有索引、联合索引没满足最左前缀（leftmost prefix）、优化器认为全表更快（选择性（selectivity）低、返回比例大）。**用实验里的写法解释，比背列表更有说服力。**

**S5. 讲一下 MVCC。**
见 3.4：隐藏列、版本链（version chain）、undo log、读视图（ReadView）；RR 读视图在第一次读时创建，RC 每条语句创建；快照读（snapshot read）不加锁，当前读（current read）加锁读最新。

**S6. 四个隔离级别（isolation level）分别解决什么问题？MySQL 默认是什么？为什么很多公司改成 RC？**
默认 RR。RC 没有间隙锁（gap lock），锁冲突和死锁（deadlock）更少，语义也更接近其他数据库；代价是同一事务（transaction）内不可重复读（non-repeatable read），要求 binlog 为 ROW 格式。

**S7. MySQL 的 RR 真的解决了幻读（phantom read）吗？**
见实验 B：快照读由 MVCC 保证一致；当前读由临键锁（next-key lock，间隙锁）阻止别人插入，因此在加锁读的范围内不会出现幻影；但同一事务里混用快照读和当前读，仍然能观察到不一致。

**S8. 间隙锁和临键锁是什么？什么时候会加？**
见 3.5，并用实验 C 说明：范围加锁读在 RR 下会锁间隙，RC 下没有；没有索引时会锁很多。

**S9. 什么是死锁？怎么排查和避免？**
见 3.5：不同顺序加锁成环；`SHOW ENGINE INNODB STATUS`；固定顺序、短事务、走索引、降低隔离级别、应用层重试（retry）。

**S10. 解释 redo log、undo log、binlog 的区别。两阶段提交（two-phase commit）是为了什么？**
redo：InnoDB 物理日志，保证持久性和崩溃恢复（crash recovery）；undo：回滚（rollback）和 MVCC；binlog：Server 层逻辑日志，复制和时间点恢复（PITR, point-in-time recovery）。两阶段提交让 redo 和 binlog 对同一事务要么都有要么都没有，避免主从不一致。

**S11. `innodb_flush_log_at_trx_commit` 和 `sync_binlog` 怎么配？**
要求不丢数据：两者都为 1。吞吐优先、可容忍丢约 1 秒：前者 2，后者调大。说明风险是整机/操作系统崩溃，而不是 MySQL 进程崩溃。

**S12. 什么是页分裂（page split）？为什么不建议随机 UUID 做主键？**
页满了还要插入时把页拆成两个；随机主键让插入位置随机，频繁分裂、碎片多、缓冲池（buffer pool）命中率下降；有序主键总是追加到最后一页。

**S13. `COUNT(*)`、`COUNT(1)`、`COUNT(col)` 的区别？大表 COUNT 慢怎么办？**
见 3.7。

**S14. 深分页（deep pagination）怎么优化？**
实验里：`OFFSET 150000` 约 30 ms，游标分页（keyset pagination）不到 1 ms。方案：记住上一页的最后一个键；或先在覆盖索引上取出主键再回表（延迟关联）；限制最大页数。

**S15. 乐观锁（optimistic locking）和悲观锁（pessimistic locking）怎么选？怎么实现？**
冲突少 → 乐观（版本号（version number） CAS，影响行数为 0 就重试）；冲突多或重试代价大 → 悲观（`FOR UPDATE`）；最简单的是单条原子 `UPDATE`。热点行用乐观锁会白白重试（实验 B 里重试一万多次）。

**S16. 主从复制（replication）的原理？延迟的原因和解决方法？**
见 3.6。

**S17. 异步（asynchronous）、半同步、组复制的区别？主库宕机会丢数据吗？**
异步可能丢；半同步（AFTER_SYNC）不丢已向客户端（client）确认的事务但有性能代价；组复制是多数派确认。

**S18. 读写分离（read/write splitting）后读到旧数据怎么办？**
关键读走主库；写后一段时间读主；用 GTID 等待从库追上；接受最终一致（eventual consistency）并做产品层面的处理。

**S19. 线上有个慢查询（slow query），你怎么排查？**
慢日志定位 → EXPLAIN/EXPLAIN ANALYZE → 索引/改写 → 观察锁等待、缓冲池、IO → 验证 → 灰度（canary release）上线；预防：代码评审里检查 SQL、压测。给一个你自己的真实案例。

**S20. 线上要给一张 5 亿行的表加字段/加索引，怎么做？**
评估 INSTANT/INPLACE 是否可行；否则用 gh-ost/pt-osc；避开 MDL 长事务；低峰期执行；限速、观察主从延迟；准备回滚；先在同量级的测试库演练。

**S21. 什么时候需要分库分表（sharding）？怎么做？**
先穷尽索引优化、读写分离、缓存（cache）、归档；单表/单库容量或写入吞吐触顶才分。分片键选择、全局 ID、跨分片查询与事务（避免或用最终一致/Saga）、扩容迁移（预分片、双写迁移）、中间件（ShardingSphere、Vitess）。

**S22. InnoDB 和 MyISAM 的区别？**
InnoDB：事务、行锁、MVCC、外键（foreign key）、崩溃恢复，是默认引擎；MyISAM：表锁、无事务、崩溃后可能损坏，已很少使用。

**S23. 什么是缓冲池？怎么判断它够不够？**
见 3.2。看命中率与 `Innodb_buffer_pool_reads`（物理读）占比；专用库的缓冲池常设为物理内存的一半以上（具体比例视情况）。

**S24. 说一个你用窗口函数（window function）解决的问题。**
准备一个真实例子，比如“每个用户最近 N 次订单”“连续活跃天数”“同比环比”。

**S25. 表里有 NULL 会有什么问题？**
比较和 `NOT IN` 的三值逻辑；聚合函数忽略 NULL；唯一索引允许多个 NULL；索引与统计更复杂。

**S26. 事务里能不能做外部调用（HTTP、消息）？**
不建议：事务持锁时间被外部延迟拉长，容易拖垮连接池（connection pool）；“写库+发消息”要一致时用事务发件箱（transactional outbox）或可靠消息。

**S27. 怎样实现幂等（idempotency）写入？**
业务唯一键 + 唯一约束，`INSERT ... ON DUPLICATE KEY UPDATE` 或 `INSERT IGNORE`（注意后者会吞掉其他错误）；或先插入去重（deduplication）记录再处理；状态机（state machine）配合条件更新。

**S28. 唯一索引和普通索引在读写上有什么区别？**
读差别极小；写时普通索引可以用修改缓冲（change buffer）延迟合并，唯一索引每次都要先读页检查冲突，所以不能用。不是说“唯一索引不好”，该唯一就要用唯一。

**S29. 外键用不用？**
外键保证引用（citation）完整性，但增加写入开销、锁范围和分库分表的难度。很多互联网场景在应用层保证，数据完整性要求极高的系统仍会用。说出取舍。

**S30. RDS MySQL 和自建 MySQL，Aurora MySQL 有什么区别？（和你简历相关，务必准备）**
托管服务替你做备份、补丁、Multi-AZ、监控；你失去了操作系统访问和一些参数/插件的自由；Aurora 的存储是共享分布式存储，副本延迟小、故障转移（failover）快，但行为与社区版有差异（比如它不使用 binlog 做自身的存储复制，仍可开启 binlog 用于外部复制）。结合你在 RDS 团队的经历，讲你处理过的具体故障、你负责的自动化、性能或可靠性改进。

### 3.10 设计题（MySQL 视角）

**设计题：订单库的读写扩展与一致性（consistency）**

1. **起点**：单主库 + 两个从库，跨 AZ；主键用有序 ID；订单表按 `(user_id, created_at)` 建联合索引支持“我的订单”。
2. **写入**：下单是事务（transaction）：库存扣减用条件更新（`UPDATE stock SET n=n-1 WHERE sku=? AND n>0`，判断影响行数），避免超卖；热点商品用队列削峰或把库存放 Redis 预扣、异步（asynchronous）落库。
3. **读**：详情走缓存（cache）；列表走从库；“下单后立即查看”走主库或带 GTID 等待。
4. **一致性**：订单与支付、库存的跨服务一致性用事务发件箱（transactional outbox） + 幂等（idempotency）消费 + 补偿（Saga），不用分布式事务。
5. **容量**：监控单表行数和 QPS；历史订单归档；达到阈值后按 `user_id` 分片，查询带分片键。
6. **运维**：在线 DDL（online DDL） 流程、慢查询（slow query）巡检、备份与 PITR 演练、复制延迟（replication lag）告警（alerting）、故障转移（failover）演练。
7. **取舍**：隔离级别（isolation level）选 RC 还是 RR（死锁（deadlock）与一致性）；缓存一致性策略（先更新库再删缓存，加延迟双删或订阅 binlog）；分片的时机。

---

## 四、把三块串起来

一个典型的高级后端问题会同时碰到三块。比如“**订单服务在大促时变慢**”：

```text
用户请求 → ALB（AWS）→ Pod（Kubernetes）→ MySQL（RDS/Aurora）
  │           │              │                    │
  │           │              │                    └─ 慢查询/锁等待/连接数耗尽/复制延迟
  │           │              └─ HPA 来不及扩 / Pod 被 OOMKilled / 节点资源不足 Pending / 探针误杀
  │           └─ 健康检查、连接排空、5xx 的来源（是目标超时还是目标拒绝）
  └─ 限流、重试风暴（客户端重试放大了故障）
```

**排查次序**：先看症状（错误率、延迟、饱和度），定位是哪一层 → 入口层（负载均衡指标（metrics））→ 应用层（Pod 重启、CPU 限流（rate limiting）、内存、线程池、连接池（connection pool））→ 数据库层（连接数、慢查询（slow query）、锁等待、IOPS、复制延迟（replication lag））→ 依赖（缓存（cache）、队列）。**关键习惯：先止血（回滚（rollback）、限流、扩容、降级），再找根因。**

**自测表**（能用 2 分钟讲清的打勾）

| 主题 | 你应该能讲清 |
|---|---|
| IAM | 默认拒绝、显式 Deny 优先、SCP/边界只设上限、跨账号两边都要放行、AccessDenied 排查顺序 |
| VPC | 公私有子网（subnet）、NAT、安全组（security group）与 NACL、网关（gateway）终端节点省钱、三层架构 |
| 数据库选型 | Multi-AZ 与只读副本（read replica）、Aurora 的存储、DynamoDB 热分区（hot partition）、什么时候选谁 |
| 消息 | 至少一次（at-least-once）、可见性超时（visibility timeout）、DLQ、幂等（idempotency） |
| 灾备（disaster recovery） | RTO/RPO、四档方案、演练 |
| K8s 核心 | 调和（reconcile）循环、apply 全过程、Pod 优雅终止（graceful shutdown） |
| K8s 运维 | 三种探针（probe）、requests 与 limits、QoS、滚动更新（rolling update）参数、HPA 公式、排障表 |
| K8s on AWS | VPC CNI IP 耗尽、IRSA、EBS 与 AZ |
| MySQL 索引 | B+ 树、聚簇与回表（table lookup, or bookmark lookup）、最左前缀（leftmost prefix）、失效写法、EXPLAIN |
| MySQL 事务（transaction） | MVCC、RR 与 RC、快照读（snapshot read）与当前读（current read）、幻读（phantom read）的准确说法 |
| MySQL 锁 | 记录锁（record lock）/间隙锁（gap lock）/临键锁（next-key lock）、无索引锁全表、死锁（deadlock）排查与预防、MDL 事故 |
| MySQL 日志与复制 | redo/undo/binlog、两阶段提交（two-phase commit）、双一、复制延迟、读写分离（read/write splitting）的坑 |
| SQL 手写 | 排名、连续区间、自连接（self join）、NULL 陷阱 |

---

## 附录 A：来源与说明

**我搜到并参考了题目范围的页面**（都是一般性博客，非高级岗位专属，也没有日期；只用来确认常考主题）：

- AWS：[Educative：按服务组整理的 AWS 面试题](https://www.educative.io/blog/aws-interview-questions-by-service-group)、[Hyring：Top 50 AWS Interview Questions (2026)](https://hyring.com/jobseeker-toolkit/interview-questions/technical/aws)、[Analytics Vidhya：Top 30 AWS Interview Questions](https://www.analyticsvidhya.com/blog/2024/08/aws-interview-questions-with-answers/)
- Kubernetes：[techinterview.org：Kubernetes 面试官在 Pod 之后问什么](https://www.techinterview.org/post/3233477276/what-kubernetes-interviewers-actually-ask/)、[进阶 Kubernetes 面试题](https://akhileshmishra.substack.com/p/these-advanced-kubernetes-interview)、[GoLinuxCloud](https://www.golinuxcloud.com/kubernetes-interview-questions/)、[DataCamp](https://www.datacamp.com/zh/blog/kubernetes-interview-questions)
- MySQL：[besthub：MySQL 面试指南（索引、事务、表设计）](https://www.besthub.dev/articles/mysql-interview-guide-indexes-transactions-schema-design-and-storage-engines-722840231e97)、[besthub：10 道 InnoDB 核心问题](https://www.besthub.dev/articles/10-core-mysql-innodb-interview-questions-explained-72394cfea545)、[DEV 社区：MySQL 面试题](https://dev.to/gowthampotureddi/mysql-interview-questions-answers-top-patterns-for-data-engineers-2j65)、[25 道进阶 MySQL 题](https://secondtalent.com/?p=31309)
- 权威来源应以官方文档为准：AWS 文档与 Well-Architected 框架、Kubernetes 官方文档、MySQL 8.0 参考手册（InnoDB 锁、隔离级别（isolation level）、MVCC 章节）。

**已验证（真实运行）**：MySQL 8.0.46 上的四个实验（索引与 EXPLAIN、隔离级别与间隙锁（gap lock）、死锁（deadlock）与丢失更新（lost update）、SQL 手写题）；moto 模拟器上的 SQS/DynamoDB 行为。

**模拟或教学模型（不是真实服务的输出）**：IAM 判定、DynamoDB 热分区（hot partition）、Kubernetes 调度/QoS、HPA、滚动更新（rolling update）、退避（backoff）时间。

**未逐条核对最新官方文档的内容（请面试前确认）**：

- AWS 的各项限额与默认值（Lambda 时长、DynamoDB 分区上限、S3 请求速率、SQS FIFO 吞吐）、RDS/Aurora 的 failover 时间量级、各服务的价格与计费细节、SnapStart、Multi-AZ 数据库集群的细节。
- Kubernetes 的版本相关特性（原生 sidecar 的版本、拓扑分布约束（topology spread constraints）的默认行为、各控制器（controller）默认值如 HPA 容忍度（tolerance） 0.1 和稳定窗口 5 分钟、CrashLoopBackOff 上限 5 分钟）。
- MySQL 的加锁规则只写了简化版，复杂的范围/非唯一索引加锁细节以官方手册和实验为准；复制、半同步（semi-synchronous replication）和组复制的细节；Aurora 与社区 MySQL 的差异；B+ 树容量是估算。
- 这份材料里没有真实的、带日期的“某公司面经”。

## 附录 B：术语表（中英对照）

按在文中第一次出现的顺序排列。

- 强一致：strong consistency
- 乐观锁：optimistic locking
- 悲观锁：pessimistic locking
- 可用区：availability zone, AZ
- 一致性：consistency
- 故障转移：failover
- 限流：rate limiting
- 重试：retry
- 幂等：idempotency
- 编排：orchestration
- 缓存：cache
- 指标：metrics
- 告警：alerting
- 追踪：trace
- 审计：audit
- 凭证：credentials
- 实例配置文件：instance profile
- 信任策略：trust policy
- 权限边界：permissions boundary
- 规划：planning
- 子网：subnet
- 互联网网关：internet gateway
- 网关：gateway
- 路由：routing
- 路由表：route table
- 安全组：security group
- 冷启动：cold start
- 预置并发：provisioned concurrency
- 并发：concurrency
- 配额：quota
- 预留并发：reserved concurrency
- 连接池：connection pool
- 最终一致：eventual consistency
- 分片上传：multipart upload
- 服务端：server
- 客户端：client
- 合规：compliance
- 至少一次：at-least-once
- 只读副本：read replica
- 异步：asynchronous
- 复制延迟：replication lag
- 时间点恢复：PITR, point-in-time recovery
- 回滚：rollback
- 慢查询：slow query
- 二级索引：secondary index
- 事务：transaction
- 条件写入：conditional write
- 去重：deduplication
- 热分区：hot partition
- 写分片：write sharding
- 旁路缓存：cache-aside
- 缓存穿透：cache penetration
- 抖动：jitter
- 可见性超时：visibility timeout
- 心跳：heartbeat
- 死信队列：dead-letter queue
- 毒消息：poison message
- 重放：replay
- 扇出：fan-out
- 出口：egress
- 恢复时间目标：RTO, recovery time objective
- 恢复点目标：RPO, recovery point objective
- 灾备：disaster recovery
- 引导灯：pilot light
- 暖备份：warm standby
- 多活：active-active
- 退避：backoff
- 背压：backpressure
- 最小权限：least privilege
- 授权：authorization
- 静态加密：encryption at rest
- 右调：rightsizing
- 流式：streaming
- 预签名：presigned
- 协议：protocol
- 读己之写：read-your-writes
- 节流：throttling
- 令牌桶：token bucket
- 租户：tenant
- 指数退避：exponential backoff
- 元数据：metadata
- 调和：reconcile
- 控制器：controller
- 控制循环：control loop
- 控制平面：control plane
- 认证：authentication
- 准入控制：admission control
- 容器运行时：container runtime
- 探针：probe
- 命名空间：namespace
- 优雅终止：graceful shutdown
- 钩子：hooks
- 滚动更新：rolling update
- 调度器：scheduler
- 驱逐：eviction
- 亲和性：affinity
- 拓扑分布约束：topology spread constraints
- 污点：taint
- 死锁：deadlock
- 容忍度：tolerance
- 适配器：adapter
- 期望状态：desired state
- 自定义资源：CRD, custom resource definition
- 租户隔离：tenant isolation
- 可观测性：observability
- 对象存储：object storage
- 预算：budget
- 缓冲池：buffer pool
- 回滚日志：undo log
- 重做日志：redo log
- 预写日志：WAL, write-ahead logging
- 二进制日志：binlog
- 主从复制：replication
- 两阶段提交：two-phase commit
- 崩溃恢复：crash recovery
- 双写缓冲：doublewrite buffer
- 修改缓冲：change buffer
- 聚簇索引：clustered index
- 回表：table lookup, or bookmark lookup
- 覆盖索引：covering index
- 页分裂：page split
- 最左前缀：leftmost prefix
- 索引下推：ICP, index condition pushdown
- 选择性：selectivity
- 全表扫描：full table scan
- 引用：citation
- 深分页：deep pagination
- 分页：pagination
- 游标分页：keyset pagination
- 脏读：dirty read
- 不可重复读：non-repeatable read
- 幻读：phantom read
- 隔离级别：isolation level
- 间隙锁：gap lock
- 版本链：version chain
- 读视图：ReadView
- 快照读：snapshot read
- 当前读：current read
- 临键锁：next-key lock
- 记录锁：record lock
- 意向锁：intention lock
- 元数据锁：MDL, metadata lock
- 丢失更新：lost update
- 版本号：version number
- 半同步：semi-synchronous replication
- 读写分离：read/write splitting
- 范式：normalization
- 在线 DDL：online DDL
- 治理：governance
- 分库分表：sharding
- 窗口函数：window function
- 自连接：self join
- 灰度：canary release
- 外键：foreign key
- 事务发件箱：transactional outbox
- 发件箱：outbox
- 状态机：state machine
- 补偿：compensation
