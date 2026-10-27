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
