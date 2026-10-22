# 示例代码

与《智能体系统工程：从第一性原理讲起》配套。纯标准库，Python 3.11 及以上，不需要 API key，也不需要联网。

```bash
cd code
python3 ch01_agent_loop.py      # 单独运行某一章
python3 run_all.py              # 运行全部，检查是否都能正常结束
```

说明：
- 用脚本化的"假模型"代替真实 LLM，目的是看清模型之外那一层的机制，不是生产实现。
- `durable.py` 是第 7、8 章共用的持久化执行玩具实现，`ch07_*`、`ch08_*` 依赖它。
- 第 9 章的耗时行取决于机器，可能有 0.1 秒的差别。
- `real_ch01_agent_loop.py` 是第 1.8 节的真实模型版本：会真实调用 Claude API、产生费用，需要 `pip install anthropic` 和环境变量 `ANTHROPIC_API_KEY`，所以不属于 `run_all.py` 的运行范围。它的循环逻辑已用假 SDK 离线验证，但未在真实 API 上运行过。
