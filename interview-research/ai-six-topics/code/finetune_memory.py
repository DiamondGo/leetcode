"""微调实验：为什么全量微调很贵，LoRA / QLoRA 为什么便宜？
用最常见的粗略估算公式算显存。注意：只是**数量级估计**，不含激活值（随序列长度和批大小变化）、梯度检查点、框架和碎片开销。
"""

GB = 1024 ** 3


def full_ft_bytes(params):
    """混合精度 + Adam 的常用估算：权重 fp16(2) + 梯度 fp16(2) + fp32 主权重(4) + Adam 的 m 和 v(4+4) = 16 字节/参数。"""
    return params * 16


def lora_trainable(d_in, d_out, r):
    """LoRA 用 W + B·A 代替更新 W：A 是 r×d_in，B 是 d_out×r，只训练这两个小矩阵。"""
    return r * (d_in + d_out)


def lora_ft_bytes(params, trainable):
    """基座冻结（fp16，2 字节/参数）；只有适配器需要梯度和优化器状态（约 16 字节/参数）。"""
    return params * 2 + trainable * 16


def qlora_ft_bytes(params, trainable):
    """QLoRA：基座量化到 4 比特（约 0.5 字节/参数），适配器照常训练。"""
    return params * 0.5 + trainable * 16


MODELS = [("7B", 7e9, 4096, 32), ("13B", 13e9, 5120, 40), ("70B", 70e9, 8192, 80)]

if __name__ == "__main__":
    r = 16
    print(f"LoRA 秩 r={r}，对每层的 q、k、v、o 四个 d×d 投影矩阵加适配器")
    print(f"{'模型':<5} {'可训练参数':>12} {'占比':>8} | {'全量微调':>10} {'LoRA':>10} {'QLoRA':>10}   （显存估计，GB）")
    for name, p, d, layers in MODELS:
        tr = layers * 4 * lora_trainable(d, d, r)
        print(f"{name:<5} {tr / 1e6:>10.1f}M {tr / p * 100:>7.2f}% | "
              f"{full_ft_bytes(p) / GB:>10.0f} {lora_ft_bytes(p, tr) / GB:>10.0f} {qlora_ft_bytes(p, tr) / GB:>10.0f}")

    print("\n适配器大小（fp16，每个任务一个）：")
    for name, p, d, layers in MODELS:
        tr = layers * 4 * lora_trainable(d, d, r)
        print(f"  {name}: 约 {tr * 2 / 1024 ** 2:.0f} MB，而完整模型权重（fp16）约 {p * 2 / GB:.0f} GB")

    print("\n秩 r 对可训练参数的影响（7B）：")
    _, p, d, layers = MODELS[0]
    for rr in (4, 8, 16, 64):
        tr = layers * 4 * lora_trainable(d, d, rr)
        print(f"  r={rr:<3} 可训练 {tr / 1e6:>6.1f}M ({tr / p * 100:.2f}%)")
