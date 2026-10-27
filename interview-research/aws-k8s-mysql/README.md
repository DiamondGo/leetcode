# AWS、Kubernetes、MySQL：高级后端面试知识与题库

- `aws-k8s-mysql-interview.md`：正文（AWS、Kubernetes、MySQL 的机制、取舍、排障、面试题与答案要点、设计题、术语表）
- `code/`：实验脚本
  - MySQL（需要本地 MySQL 8.0，连接参数见 `mysql_common.py`，数据库名固定为 `iv`，会建表删表，不要对真实数据运行；依赖 `pip install pymysql`）：`mysql_index_explain.py`、`mysql_isolation_locks.py`、`mysql_deadlock_lostupdate.py`、`sql_classics.py`
  - AWS：`aws_sqs_idempotency.py`（用 moto 模拟，`pip install boto3 "moto[sqs,dynamodb]"`）、`aws_iam_eval.py`、`aws_dynamodb_hotkey.py`（纯 Python 教学模型）
  - Kubernetes：`k8s_scheduler_qos.py`、`k8s_hpa_rollout.py`（纯 Python 模拟，不连集群）
- `sample_output/`：我运行时的输出（耗时和并发实验里的随机细节每次不同）

说明：MySQL 实验在真实 MySQL 8.0.46 上运行；AWS 与 Kubernetes 的实验是模拟或教学模型。具体数字（限额、默认值、版本特性）没有逐条对照最新官方文档，详见正文附录 A。
