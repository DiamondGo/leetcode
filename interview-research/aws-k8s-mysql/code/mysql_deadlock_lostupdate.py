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
