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
