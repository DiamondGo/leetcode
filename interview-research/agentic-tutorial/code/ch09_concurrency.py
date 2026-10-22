"""第 9 章：并发与规模。有界并发（信号量）、逐个调用的超时、取消；以及多租户下的公平调度。"""
import asyncio
import time


# ---------- 1. 有界并发的并行工具调用 ----------
async def fake_tool(name, delay, fail=False):
    await asyncio.sleep(delay)
    if fail:
        raise RuntimeError(f"{name} 失败")
    return f"{name}:ok"


async def run_tools(calls, limit=3, per_call_timeout=0.25):
    sem = asyncio.Semaphore(limit)
    running, peak = 0, 0

    async def one(name, delay, fail=False):
        nonlocal running, peak
        async with sem:                                   # 同时最多 limit 个在跑
            running += 1
            peak = max(peak, running)
            try:
                async with asyncio.timeout(per_call_timeout):     # 每个调用有自己的超时
                    return name, await fake_tool(name, delay, fail)
            except TimeoutError:
                return name, "timeout"
            except RuntimeError as e:                     # 部分失败：不让一个失败拖垮全部
                return name, f"error: {e}"
            finally:
                running -= 1

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(one(*c)) for c in calls]
    return [t.result() for t in tasks], peak


# ---------- 2. 取消要能传播并清理 ----------
async def cancellable_demo():
    cleaned = []

    async def worker(i):
        try:
            await asyncio.sleep(10)
        finally:
            cleaned.append(i)                             # 被取消时也要释放资源

    try:
        async with asyncio.timeout(0.1):                  # 整体截止时间
            async with asyncio.TaskGroup() as tg:
                for i in range(3):
                    tg.create_task(worker(i))
    except TimeoutError:
        pass
    return sorted(cleaned)


# ---------- 3. 公平调度：一个大租户不应饿死小租户 ----------
def fifo_finish_position(jobs):
    """jobs: [(tenant, id)] 先到先得。返回各租户最后一个任务完成的位置（第几个被处理）。"""
    last = {}
    for pos, (tenant, _) in enumerate(jobs, 1):
        last[tenant] = pos
    return last


def round_robin_finish_position(jobs):
    queues = {}
    for tenant, jid in jobs:
        queues.setdefault(tenant, []).append(jid)
    last, pos = {}, 0
    while any(queues.values()):
        for tenant, q in queues.items():                  # 每个租户轮流出一个
            if q:
                q.pop(0)
                pos += 1
                last[tenant] = pos
    return last


if __name__ == "__main__":
    calls = [("a", 0.2), ("b", 0.2), ("c", 0.2), ("d", 0.2), ("e", 0.6), ("f", 0.1, True)]
    t0 = time.perf_counter()
    results, peak = asyncio.run(run_tools(calls, limit=3, per_call_timeout=0.25))
    elapsed = time.perf_counter() - t0
    print("结果：", results)
    print(f"最高并发数 {peak}（上限 3）；总耗时约 {elapsed:.1f}s，串行至少需要 {sum(c[1] for c in calls):.1f}s")
    print("取消后被清理的任务：", asyncio.run(cancellable_demo()))

    jobs = [("大租户", i) for i in range(100)] + [("小租户", i) for i in range(3)]
    print("先到先得，小租户全部做完是第几个：", fifo_finish_position(jobs)["小租户"])
    print("按租户轮流，小租户全部做完是第几个：", round_robin_finish_position(jobs)["小租户"])
