"""实验 6：SQS 的“至少一次投递”、可见性超时、死信队列，以及用 DynamoDB 条件写入做幂等消费。
用 moto 在本地模拟 AWS API（boto3 调用写法和真实 AWS 一致，但 moto 是模拟器：时间行为、限流、
FIFO 细节等不保证和真实服务完全一致）。运行：pip install boto3 "moto[sqs,dynamodb]"
"""
import json, time
import boto3
from botocore.exceptions import ClientError
from moto import mock_aws

with mock_aws():
    kw = dict(region_name="us-east-1", aws_access_key_id="x", aws_secret_access_key="x")
    sqs, ddb = boto3.client("sqs", **kw), boto3.client("dynamodb", **kw)

    dlq = sqs.create_queue(QueueName="orders-dlq")["QueueUrl"]
    dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
    q = sqs.create_queue(QueueName="orders", Attributes={
        "VisibilityTimeout": "1",
        "RedrivePolicy": json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "3"})})["QueueUrl"]
    ddb.create_table(TableName="processed", KeySchema=[{"AttributeName": "msg_id", "KeyType": "HASH"}],
                     AttributeDefinitions=[{"AttributeName": "msg_id", "AttributeType": "S"}], BillingMode="PAY_PER_REQUEST")

    print("=== A. 消费者处理完但没来得及删除消息 -> 可见性超时后再次投递（至少一次）===")
    sqs.send_message(QueueUrl=q, MessageBody="charge:order-1")
    m = sqs.receive_message(QueueUrl=q, MaxNumberOfMessages=1)["Messages"][0]
    print("第 1 次收到:", m["Body"], "| 立刻再收一次:", sqs.receive_message(QueueUrl=q).get("Messages", "收不到（消息处于不可见期）"))
    time.sleep(1.2)
    m2 = sqs.receive_message(QueueUrl=q, MaxNumberOfMessages=1)["Messages"][0]
    print("可见性超时后第 2 次收到同一条消息:", m2["Body"], "（如果每次都扣款，就重复扣款了）")

    print("\n=== B. 幂等消费：先用条件写入“占位”，失败说明处理过了 ===")
    def handle(msg_id):
        try:
            ddb.put_item(TableName="processed", Item={"msg_id": {"S": msg_id}},
                         ConditionExpression="attribute_not_exists(msg_id)")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return "已处理过，跳过"
            raise
        return "首次处理，执行扣款"
    print("第 1 次:", handle("order-1"))
    print("第 2 次:", handle("order-1"))
    print("（真实系统要注意：占位成功后、业务完成前崩溃怎么办？见正文：状态要有 processing/done，并有超时接管；"
          "或把业务写入和去重记录放在同一个事务里。）")

    print("\n=== C. 一直处理失败的“毒消息”：超过 maxReceiveCount 后进入死信队列 ===")
    sqs.purge_queue(QueueUrl=q); time.sleep(0.1)
    sqs.send_message(QueueUrl=q, MessageBody="poison")
    for i in range(1, 5):
        r = sqs.receive_message(QueueUrl=q, MaxNumberOfMessages=1)
        print(f"第 {i} 次在主队列收消息:", "收到并处理失败（不删除）" if r.get("Messages") else "没有消息")
        time.sleep(1.2)
    d = sqs.receive_message(QueueUrl=dlq, MaxNumberOfMessages=1).get("Messages")
    print("死信队列里:", d[0]["Body"] if d else "没有")
