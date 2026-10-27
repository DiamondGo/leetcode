"""实验 5：IAM 权限判定的简化模型（纯 Python，不连 AWS）。
实现文档里的核心规则：默认拒绝；显式 Deny 永远优先；Allow 要同时被 SCP、权限边界（permissions boundary）放行；
同账号内资源策略可单独放行，跨账号则身份策略和资源策略都要放行。
这是**教学用简化模型**：不含条件键（Condition）、会话策略、NotAction 等，真实判定以 AWS 文档为准。
"""
from fnmatch import fnmatchcase


def match(patterns, value):
    return any(fnmatchcase(value, p) for p in patterns)


def stmts(policy, effect, action, resource):
    return [s for s in policy if s["Effect"] == effect and match(s["Action"], action) and match(s["Resource"], resource)]


def allowed_by(policies, action, resource):
    """一组策略里有没有匹配的 Allow。"""
    return any(stmts(p, "Allow", action, resource) for p in policies)


def explicit_deny(policies, action, resource):
    return any(stmts(p, "Deny", action, resource) for p in policies)


def evaluate(action, resource, identity=(), boundary=None, scps=(), resource_policy=None, same_account=True):
    allp = list(identity) + ([boundary] if boundary else []) + list(scps) + ([resource_policy] if resource_policy else [])
    if explicit_deny(allp, action, resource):
        return "拒绝：命中显式 Deny"
    if any(not allowed_by([s], action, resource) for s in scps):
        return "拒绝：SCP 没有放行（SCP 只设上限，不授予权限）"
    if boundary is not None and not allowed_by([boundary], action, resource):
        return "拒绝：超出权限边界"
    ident = allowed_by(identity, action, resource)
    res = bool(resource_policy) and allowed_by([resource_policy], action, resource)
    if same_account:
        return "允许" if (ident or res) else "拒绝：默认拒绝（没有任何 Allow）"
    return "允许" if (ident and res) else "拒绝：跨账号需要身份策略和资源策略都放行"


def S(effect, action, resource="*"):
    return {"Effect": effect, "Action": [action] if isinstance(action, str) else action,
            "Resource": [resource] if isinstance(resource, str) else resource}


BUCKET = "arn:aws:s3:::reports/*"
cases = [
    ("1 没有任何策略", dict(action="s3:GetObject", resource=BUCKET)),
    ("2 身份策略允许 s3:Get*", dict(action="s3:GetObject", resource=BUCKET, identity=[[S("Allow", "s3:Get*")]])),
    ("3 允许 s3:* 但显式拒绝删除", dict(action="s3:DeleteObject", resource=BUCKET,
                                     identity=[[S("Allow", "s3:*"), S("Deny", "s3:DeleteObject")]])),
    ("4 身份策略允许，但权限边界只给 ec2", dict(action="s3:GetObject", resource=BUCKET,
                                          identity=[[S("Allow", "s3:*")]], boundary=[S("Allow", "ec2:*")])),
    ("5 身份策略允许，但 SCP 只放行 ec2", dict(action="s3:GetObject", resource=BUCKET,
                                          identity=[[S("Allow", "s3:*")]], scps=[[S("Allow", "ec2:*")]])),
    ("6 同账号：只有桶策略允许", dict(action="s3:GetObject", resource=BUCKET, resource_policy=[S("Allow", "s3:GetObject")])),
    ("7 跨账号：只有桶策略允许", dict(action="s3:GetObject", resource=BUCKET, resource_policy=[S("Allow", "s3:GetObject")], same_account=False)),
    ("8 跨账号：两边都允许", dict(action="s3:GetObject", resource=BUCKET, identity=[[S("Allow", "s3:Get*")]],
                              resource_policy=[S("Allow", "s3:GetObject")], same_account=False)),
]
if __name__ == "__main__":
    for name, kw in cases:
        print(f"{name:<34} -> {evaluate(**kw)}")
