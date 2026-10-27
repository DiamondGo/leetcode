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
