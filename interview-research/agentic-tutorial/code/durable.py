"""一个约 90 行的"持久化执行"最小实现，用来理解 Temporal 这类系统的核心思想。
核心：每一步的结果都先写进持久的日志（journal）；崩溃后用同一个 run_id 重新运行，
已完成的步骤直接从日志里取结果（replay），不会再次真正执行。

注意：这是教学用的玩具，不是生产实现（没有并发控制、租约、版本管理等）。
"""
import json
import sqlite3


class Crash(Exception):
    """用来模拟进程崩溃。"""


class Suspended(Exception):
    """工作流在等待外部信号（如人工审批），本次运行先挂起。"""


class Journal:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS steps(run_id TEXT, seq INT, name TEXT, result TEXT, "
                        "PRIMARY KEY(run_id, seq))")
        self.db.execute("CREATE TABLE IF NOT EXISTS signals(run_id TEXT, name TEXT, payload TEXT, "
                        "PRIMARY KEY(run_id, name))")
        self.db.execute("CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, status TEXT, result TEXT)")

    def get_step(self, run_id, seq):
        row = self.db.execute("SELECT result FROM steps WHERE run_id=? AND seq=?", (run_id, seq)).fetchone()
        return None if row is None else json.loads(row[0])

    def put_step(self, run_id, seq, name, result):
        self.db.execute("INSERT OR REPLACE INTO steps VALUES(?,?,?,?)", (run_id, seq, name, json.dumps(result)))
        self.db.commit()

    def get_signal(self, run_id, name):
        row = self.db.execute("SELECT payload FROM signals WHERE run_id=? AND name=?", (run_id, name)).fetchone()
        return None if row is None else json.loads(row[0])

    def put_signal(self, run_id, name, payload):
        self.db.execute("INSERT OR REPLACE INTO signals VALUES(?,?,?)", (run_id, name, json.dumps(payload)))
        self.db.commit()

    def set_run(self, run_id, status, result=None):
        self.db.execute("INSERT OR REPLACE INTO runs VALUES(?,?,?)", (run_id, status, json.dumps(result)))
        self.db.commit()


class Ctx:
    """工作流代码拿到的"上下文"。所有会产生副作用或不确定结果的事情，都必须通过它来做。"""
    def __init__(self, journal, run_id, crash_points):
        self.journal, self.run_id, self.crash_points, self.seq = journal, run_id, crash_points, 0
        self.executed = []            # 本次进程里真正执行（而不是回放）的步骤，便于演示

    def activity(self, name, fn, *args):
        seq, self.seq = self.seq, self.seq + 1
        recorded = self.journal.get_step(self.run_id, seq)
        if recorded is not None:                      # 回放：日志里已有结果，不再真正执行
            return recorded
        if (seq, "before") in self.crash_points:
            raise Crash(f"崩溃于第{seq}步（{name}）执行之前")
        key = f"{self.run_id}:{seq}"                  # 稳定的幂等键：同一次运行的同一步，重试时不变
        result = fn(*args, idem_key=key)
        self.executed.append(name)
        if (seq, "after") in self.crash_points:       # 已执行、但结果还没记进日志——最危险的窗口
            raise Crash(f"崩溃于第{seq}步（{name}）执行之后、记录之前")
        self.journal.put_step(self.run_id, seq, name, result)
        return result

    def wait_signal(self, name):
        payload = self.journal.get_signal(self.run_id, name)
        if payload is None:
            raise Suspended(f"等待信号 {name}")
        return payload


class Runner:
    def __init__(self, journal, crash_points=()):
        self.journal, self.crash_points = journal, set(crash_points)

    def run(self, workflow, run_id, *args):
        ctx = Ctx(self.journal, run_id, self.crash_points)
        try:
            result = workflow(ctx, *args)
        except Suspended:
            self.journal.set_run(run_id, "SUSPENDED")
            return "SUSPENDED", None, ctx
        self.journal.set_run(run_id, "DONE", result)
        return "DONE", result, ctx

    def signal(self, run_id, name, payload):
        self.journal.put_signal(run_id, name, payload)
