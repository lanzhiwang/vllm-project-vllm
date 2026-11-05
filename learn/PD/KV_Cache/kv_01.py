import torch
import torch.nn as nn
import torch.nn.functional as F

# 统一打印格式与随机种子
torch.manual_seed(42)
torch.set_printoptions(precision=4, sci_mode=False)


class MinimalCausalSelfAttention(nn.Module):
    """
    极简的因果自注意力层, 支持有 KV Cache 和无 KV Cache 两种前向模式
    """

    def __init__(self, d_model):
        super().__init__()
        self.d_model = d_model
        # 为简化直观, 使用单头注意力, 无偏置
        self.w_q = nn.Linear(d_model, d_model, bias=False)
        self.w_k = nn.Linear(d_model, d_model, bias=False)
        self.w_v = nn.Linear(d_model, d_model, bias=False)
        self.w_out = nn.Linear(d_model, d_model, bias=False)

    def forward(self, x, past_kv=None):
        """
        x: [batch_size, seq_len, d_model]
        past_kv: 元组 (past_k, past_v), 其中 past_k/v 的形状为 [batch_size, past_seq_len, d_model]
        """
        batch_size, seq_len, d_model = x.shape

        # 1. 投影计算当前的 Q, K, V
        q = self.w_q(x)  # [B, L, D]
        k = self.w_k(x)  # [B, L, D]
        v = self.w_v(x)  # [B, L, D]

        # 2. 如果存在 past_kv, 则把历史的 K, V 和当前步计算的 K, V 拼起来
        if past_kv is not None:
            past_k, past_v = past_kv
            k = torch.cat([past_k, k], dim=1)  # 拼接序列维度: [B, past_len + L, D]
            v = torch.cat([past_v, v], dim=1)

        # 记录本次更新后的完整 KV, 供下一步使用
        present_kv = (k, v)

        # 3. 计算注意力分数
        # q 的长度为 L (如果是增量生成阶段, L=1)
        # k 的长度为 total_seq_len (past_len + L)
        scores = torch.matmul(q, k.transpose(-2, -1)) / (self.d_model**0.5)

        # 4. 因果掩码(Causal Mask)
        total_seq_len = k.shape[1]
        if seq_len > 1:
            # Prefill 阶段或非增量模式下, 需要 mask 掉未来的位置
            # 上三角矩阵(不含对角线)置为 -inf
            mask = torch.triu(
                torch.full((seq_len, total_seq_len), float("-inf")), diagonal=1
            )
            scores = scores + mask.to(x.device)
        else:
            # 当 seq_len=1 时(自回归单步生成), 当前只有 1 个 token,
            # 它需要关注所有历史 token 和它自己, 所以不需要做未来的 mask(全部可见)
            pass

        attn_weights = F.softmax(scores, dim=-1)
        out = torch.matmul(attn_weights, v)
        out = self.w_out(out)

        return out, present_kv, k, v, attn_weights


def main():
    d_model = 4  # 隐藏层维度设小一点, 方便打印矩阵查看
    model = MinimalCausalSelfAttention(d_model)
    model.eval()

    print("=" * 70)
    print("[第一部分: 数据不变性验证] 证明历史 Token 的 K、V 在新 Token 产生时不会改变")
    print("=" * 70)

    # 模拟输入序列: 由 3 个 token 组成(例如句子: ["我", "爱", "吃"])
    x_step1 = torch.randn(1, 1, d_model)  # Token 0
    x_step2 = torch.randn(1, 1, d_model)  # Token 1
    x_step3 = torch.randn(1, 1, d_model)  # Token 2

    # 假设一次性把 [Token 0, Token 1, Token 2] 作为整句输入
    x_full = torch.cat([x_step1, x_step2, x_step3], dim=1)
    with torch.no_grad():
        _, _, k_full, v_full, _ = model(x_full)

    # 单独拿 Token 0 计算 K、V
    with torch.no_grad():
        _, _, k_t0, v_t0, _ = model(x_step1)

    print("\n1. 比较 Token 0 单独计算的 K 与整句输入中 Token 0 对应的 K:")
    print("单独计算 Token 0 的 K:\n", k_t0[0, 0])
    print("整句计算中 Token 0 的 K:\n", k_full[0, 0])
    is_k_same = torch.allclose(k_t0[0, 0], k_full[0, 0])
    print(f"--> 两者是否完全一致? {is_k_same}")

    print("\n[结论]:")
    print("因为 K = X * W_k 是逐位置(position-wise)的线性变换,")
    print("第 t 步输入一个新 token, 根本不会影响 0 到 t-1 位置的 K 和 V!")
    print(
        "既然过去位置的 K 和 V 从始至终不会变, 那为什么每次还要重复去算它呢? 这就是 KV Cache 的理论根基!"
    )

    print("\n" + "=" * 70)
    print("[第二部分: 模拟前向生成流程] 无 Cache (Naive) VS 有 Cache (KV Cache)")
    print("=" * 70)

    # 假设我们现在已经有 Prompt: [Token 0, Token 1]
    # 我们要自回归生成接下来的 2 个 token: Token 2, Token 3
    prompt = torch.randn(1, 2, d_model)
    token_2 = torch.randn(1, 1, d_model)
    token_3 = torch.randn(1, 1, d_model)

    # ----------------- 方式 A: 无 KV Cache(每次全量重算) -----------------
    print("\n>>> [模式 A] 无 KV Cache: 生成 Token 2 和 Token 3")

    # 生成 Token 2 时: 输入包含 [prompt, token_2], 长度为 3
    seq_for_step2 = torch.cat([prompt, token_2], dim=1)
    with torch.no_grad():
        out_naive_2, _, _, _, weights_naive_2 = model(seq_for_step2)
        # 模型只需要关注序列最后一个位置的输出(即新 token 处的隐状态)
        token_2_out_naive = out_naive_2[:, -1:, :]

    # 生成 Token 3 时: 输入包含 [prompt, token_2, token_3], 长度为 4
    seq_for_step3 = torch.cat([prompt, token_2, token_3], dim=1)
    with torch.no_grad():
        out_naive_3, _, _, _, weights_naive_3 = model(seq_for_step3)
        token_3_out_naive = out_naive_3[:, -1:, :]

    print(f"生成 Token 2 时参与投影的序列长度: {seq_for_step2.shape[1]}")
    print(f"生成 Token 3 时参与投影的序列长度: {seq_for_step3.shape[1]}")
    print(
        "缺点: 历史 token 不断被重新参与 W_q, W_k, W_v 矩阵运算, 冗余计算随长度呈 O(N^2) 膨胀!"
    )

    # ----------------- 方式 B: 使用 KV Cache -----------------
    print("\n>>> [模式 B] 启用 KV Cache: 增量生成")

    # 1. Prefill 阶段: 处理 Prompt(序列长度 2)
    with torch.no_grad():
        _, past_kv, _, _, _ = model(prompt)
    print(
        f"Prefill 结束, 当前已缓存 K 的形状: {past_kv[0].shape}, V 的形状: {past_kv[1].shape}"
    )

    # 2. Decode 阶段 step 1: 生成 Token 2 时, 只将 token_2 作为输入 (seq_len=1)
    with torch.no_grad():
        token_2_out_cached, past_kv, _, _, weights_cache_2 = model(
            token_2, past_kv=past_kv
        )
    print(f"生成 Token 2, 输入序列长度仅为: {token_2.shape[1]}")
    print(f"更新后, 已缓存 K 的形状: {past_kv[0].shape}, V 的形状: {past_kv[1].shape}")

    # 3. Decode 阶段 step 2: 生成 Token 3 时, 只将 token_3 作为输入 (seq_len=1)
    with torch.no_grad():
        token_3_out_cached, past_kv, _, _, weights_cache_3 = model(
            token_3, past_kv=past_kv
        )
    print(f"生成 Token 3, 输入序列长度仅为: {token_3.shape[1]}")
    print(f"更新后, 已缓存 K 的形状: {past_kv[0].shape}, V 的形状: {past_kv[1].shape}")

    print("\n" + "=" * 70)
    print("[第三部分: 数学等价性严谨验证]")
    print("=" * 70)

    # 验证输出向量是否一致
    diff_step2 = (token_2_out_naive - token_2_out_cached).abs().max().item()
    diff_step3 = (token_3_out_naive - token_3_out_cached).abs().max().item()
    print(
        f"Token 2 输出的最大绝对误差: {diff_step2:.8f} (完全等价: {torch.allclose(token_2_out_naive, token_2_out_cached)})"
    )
    print(
        f"Token 3 输出的最大绝对误差: {diff_step3:.8f} (完全等价: {torch.allclose(token_3_out_naive, token_3_out_cached)})"
    )

    # 验证注意力权重是否一致
    # 在无 cache 时, 最后一步的 weights 形状为 [1, 4, 4], 最后一行是对 4 个 token 的注意力
    # 在有 cache 时, weights 形状为 [1, 1, 4], 即当前单个 Query 对所有 4 个 Key 的注意力
    naive_last_row_weights = weights_naive_3[0, -1, :]
    cache_weights = weights_cache_3[0, 0, :]
    print("\n观察 Token 3 生成时对所有历史 Token 的注意力权重:")
    print("无 Cache 模式(全矩阵最后一行):", naive_last_row_weights)
    print("有 Cache 模式(增量单行计算)  :", cache_weights)
    print(
        f"注意力分布是否完全一致: {torch.allclose(naive_last_row_weights, cache_weights)}"
    )


if __name__ == "__main__":
    main()

"""
root@c80c6635b325:/code/KV_Cache# python3 kv_01.py
======================================================================
[第一部分: 数据不变性验证] 证明历史 Token 的 K、V 在新 Token 产生时不会改变
======================================================================

1. 比较 Token 0 单独计算的 K 与整句输入中 Token 0 对应的 K:
单独计算 Token 0 的 K:
 tensor([ 0.2390, -0.1699,  0.1589, -0.5015])
整句计算中 Token 0 的 K:
 tensor([ 0.2390, -0.1699,  0.1589, -0.5015])
--> 两者是否完全一致? True

[结论]:
因为 K = X * W_k 是逐位置(position-wise)的线性变换,
第 t 步输入一个新 token, 根本不会影响 0 到 t-1 位置的 K 和 V!
既然过去位置的 K 和 V 从始至终不会变, 那为什么每次还要重复去算它呢? 这就是 KV Cache 的理论根基!

======================================================================
[第二部分: 模拟前向生成流程] 无 Cache (Naive) VS 有 Cache (KV Cache)
======================================================================

>>> [模式 A] 无 KV Cache: 生成 Token 2 和 Token 3
生成 Token 2 时参与投影的序列长度: 3
生成 Token 3 时参与投影的序列长度: 4
缺点: 历史 token 不断被重新参与 W_q, W_k, W_v 矩阵运算, 冗余计算随长度呈 O(N^2) 膨胀!

>>> [模式 B] 启用 KV Cache: 增量生成
Prefill 结束, 当前已缓存 K 的形状: torch.Size([1, 2, 4]), V 的形状: torch.Size([1, 2, 4])
生成 Token 2, 输入序列长度仅为: 1
更新后, 已缓存 K 的形状: torch.Size([1, 3, 4]), V 的形状: torch.Size([1, 3, 4])
生成 Token 3, 输入序列长度仅为: 1
更新后, 已缓存 K 的形状: torch.Size([1, 4, 4]), V 的形状: torch.Size([1, 4, 4])

======================================================================
[第三部分: 数学等价性严谨验证]
======================================================================
Token 2 输出的最大绝对误差: 0.00000003 (完全等价: True)
Token 3 输出的最大绝对误差: 0.00000001 (完全等价: True)

观察 Token 3 生成时对所有历史 Token 的注意力权重:
无 Cache 模式(全矩阵最后一行): tensor([0.3173, 0.1665, 0.2820, 0.2342])
有 Cache 模式(增量单行计算)  : tensor([0.3173, 0.1665, 0.2820, 0.2342])
注意力分布是否完全一致: True
root@c80c6635b325:/code/KV_Cache#
"""
