# AI 应用工程六大主题：知识与面试

- `ai-six-topics-knowledge.md`：正文（RAG、智能体与多智能体、工具调用、MCP、评测、微调，附面试题、设计题、术语表）
- `code/rag_hybrid_toy.py`：混合检索玩具实验（BM25 vs 稠密 vs RRF 融合），纯标准库
- `code/finetune_memory.py`：全量微调 / LoRA / QLoRA 显存估算，纯标准库

运行：`python3 code/rag_hybrid_toy.py`、`python3 code/finetune_memory.py`

说明：MCP 2026-07-28 版本的具体改动、各厂商微调服务细节来自搜索摘要，未核对官方原文；详见正文附录 A。
