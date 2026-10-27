"""MySQL 实验的公共部分：连接参数从环境变量读，默认连本机 127.0.0.1:33306 的 root（无密码）。
需要一个本地 MySQL 8.0。数据库名固定为 iv，实验会自己建表、删表，不要对着有真实数据的库运行。
"""
import os
import pymysql


def connect(autocommit=True, db="iv"):
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "33306")),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=db, autocommit=autocommit, charset="utf8mb4",
    )


def ensure_db():
    c = connect(db=None)
    c.cursor().execute("CREATE DATABASE IF NOT EXISTS iv")
    c.close()


def rows(conn, sql, args=None):
    cur = conn.cursor()
    cur.execute(sql, args)
    return cur.fetchall()
