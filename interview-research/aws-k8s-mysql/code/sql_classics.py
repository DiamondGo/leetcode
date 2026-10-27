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
