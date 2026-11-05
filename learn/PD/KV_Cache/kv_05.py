import torch
import torch.nn as nn
import torch.nn.functional as F

# 固定随机种子并设置打印精度
torch.manual_seed(42)
torch.set_printoptions(precision=3, sci_mode=False)

# 1. 现实世界词表 (Vocabulary)
VOCAB = {0: "[PAD]", 1: "我", 2: "爱", 3: "吃", 4: "面", 5: "米"}
VOCAB_SIZE = len(VOCAB)
D_MODEL = 4  # 隐藏层维度设为 4, 便于查看矩阵具体数值


class MiniLLM(nn.Module):
    """
    具备完整 LLM 结构的单层 Decoder-only 语言模型
    结构: Embedding -> Attention(Q, K, V) -> FFN -> LM Head -> Softmax
    """

    def __init__(self, vocab_size=VOCAB_SIZE, d_model=D_MODEL):
        super().__init__()
        self.d_model = d_model

        # 1. 词嵌入层
        self.token_embedding = nn.Embedding(vocab_size, d_model)

        # 2. 注意力投影层
        self.w_q = nn.Linear(d_model, d_model, bias=False)
        self.w_k = nn.Linear(d_model, d_model, bias=False)
        self.w_v = nn.Linear(d_model, d_model, bias=False)
        self.w_out = nn.Linear(d_model, d_model, bias=False)

        # 3. 前馈全连接网络 (FFN / MLP)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 2), nn.ReLU(), nn.Linear(d_model * 2, d_model)
        )

        # 4. 语言模型分类头 (LM Head)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=True)

    def forward(self, input_ids):
        seq_len = input_ids.shape[1]
        print(f"\n{'#' * 30} 前向传播开始 (当前序列长度 = {seq_len}) {'#' * 30}")
        print(f"输入 input_ids 形状: {input_ids.shape}")
        print(f"输入 input_ids:\n{input_ids}")

        # =====================================================================
        # 步骤 1: Embedding 映射
        # =====================================================================
        x = self.token_embedding(input_ids)
        print(f"\n[Layer 1: Embedding 输出]")
        print(f"X 的形状: {x.shape} -> [batch, seq_len, d_model]")
        print(f"X:\n{x}")

        # =====================================================================
        # 步骤 2: 计算 Q, K, V
        # =====================================================================
        Q = self.w_q(x)
        K = self.w_k(x)
        V = self.w_v(x)

        print(f"\n[Layer 2: 投影计算 Q, K, V]")
        print(f"Q 的形状: {Q.shape} | Q:\n{Q}")
        print(f"K 的形状: {K.shape} | K:\n{K}")
        print(f"V 的形状: {V.shape} | V:\n{V}")

        # =====================================================================
        # 步骤 3: 因果注意力计算 (Scaled Dot-Product + Mask + Weighting)
        # =====================================================================
        print(f"\n{'-' * 25} 步骤 3 深度展开: 因果自注意力计算 {'-' * 25}")

        # 3.1 转置 K 矩阵
        K_T = K.transpose(-2, -1)
        print(f"1. K 转置矩阵 K_T 形状: {K_T.shape} -> [batch, d_model, seq_len]")
        print(f"   K_T:\n{K_T}")

        # 3.2 矩阵点积 Q @ K_T
        raw_scores = torch.matmul(Q, K_T)
        print(
            f"\n2. 点积结果 (Q @ K_T) 形状: {raw_scores.shape} -> [batch, seq_len, seq_len]"
        )
        print(f"   raw_scores:\n{raw_scores}")

        # 3.3 缩放除以 sqrt(d_model)
        scores = raw_scores / (self.d_model**0.5)
        print(
            f"\n3. 缩放打分 (除以 sqrt({self.d_model})={self.d_model**0.5}) 形状: {scores.shape}"
        )
        print(f"   scores:\n{scores}")

        # 3.4 因果掩码 (Mask)
        mask = torch.triu(torch.full((seq_len, seq_len), float("-inf")), diagonal=1)
        print(f"\n4. 因果掩码 mask 形状: {mask.shape} (严格上三角为 -inf)")
        print(f"   mask:\n{mask}")

        # 3.5 掩码相加
        masked_scores = scores + mask
        print(
            f"\n5. 遮蔽后的打分 masked_scores (scores + mask) 形状: {masked_scores.shape}"
        )
        print(f"   masked_scores:\n{masked_scores}")

        # 3.6 Softmax 归一化注意力权重
        attn_weights = F.softmax(masked_scores, dim=-1)
        print(
            f"\n6. 注意力权重矩阵 attn_weights (Softmax 后) 形状: {attn_weights.shape}"
        )
        print(f"   attn_weights:\n{attn_weights}")

        # 3.7 注意力加权求和: context = attn_weights @ V
        context = torch.matmul(attn_weights, V)
        print(
            f"\n7. 加权求和上下文 context (attn_weights @ V) 形状: {context.shape} -> [batch, seq_len, d_model]"
        )
        print(f"   context:\n{context}")

        # 3.8 输出线性投影: attn_out = w_out(context)
        attn_out = self.w_out(context)
        print(
            f"\n8. 注意力最终投影输出 attn_out (w_out(context)) 形状: {attn_out.shape}"
        )
        print(f"   attn_out:\n{attn_out}")

        # =====================================================================
        # 步骤 4: 前馈神经网络 (FFN) 深度展开
        # =====================================================================
        print(f"\n{'-' * 25} 步骤 4 深度展开: 前馈神经网络 (FFN) {'-' * 25}")

        # 4.1 线性升维: [B, L, 4] -> [B, L, 8]
        ffn_linear1_out = self.ffn[0](attn_out)
        print(f"1. FFN 升维层 Linear(4 -> 8) 形状: {ffn_linear1_out.shape}")
        print(f"   ffn_linear1_out:\n{ffn_linear1_out}")

        # 4.2 ReLU 非线性激活
        ffn_relu_out = self.ffn[1](ffn_linear1_out)
        print(f"\n2. ReLU 激活输出 (所有负数被置 0) 形状: {ffn_relu_out.shape}")
        print(f"   ffn_relu_out:\n{ffn_relu_out}")

        # 4.3 线性降维: [B, L, 8] -> [B, L, 4]
        ffn_out = self.ffn[2](ffn_relu_out)
        print(f"\n3. FFN 降维层 Linear(8 -> 4) (即最终 ffn_out) 形状: {ffn_out.shape}")
        print(f"   ffn_out:\n{ffn_out}")

        # =====================================================================
        # 步骤 5: LM Head 输出词表概率
        # =====================================================================
        print(f"\n{'-' * 25} 步骤 5 深度展开: 语言模型头 (LM Head) 预测概率 {'-' * 25}")

        # 5.1 全连接层投影到词表维度 (Logits)
        logits = self.lm_head(ffn_out)
        print(
            f"1. 未归一化打分 logits (Linear(4 -> 6)) 形状: {logits.shape} -> [batch, seq_len, vocab_size]"
        )
        print(f"   logits:\n{logits}")

        # 5.2 Softmax 转为词表上的真实概率分布
        probs = F.softmax(logits, dim=-1)
        print(
            f"\n2. 最终归一化概率分布 probs (Softmax 后, 每行求和为 1.0) 形状: {probs.shape}"
        )
        print(f"   probs:\n{probs}")

        return Q, K, V, probs


def main():
    model = MiniLLM()
    model.eval()

    # 偏置微调, 确保生成 "面" (ID: 4)
    with torch.no_grad():
        model.lm_head.bias[4] += 5.0

    print("\n" + "=" * 80)
    print("[第一轮前向传播]: 输入 Prompt 提示词 ['我', '爱', '吃'] (seq_len = 3)")
    print("=" * 80)

    input_ids_1 = torch.tensor([[1, 2, 3]])
    with torch.no_grad():
        Q1, K1, V1, probs1 = model(input_ids_1)

    next_token_probs = probs1[0, -1, :]
    next_token_id = torch.argmax(next_token_probs).item()
    next_token_word = VOCAB[next_token_id]

    print("\n" + "-" * 60)
    print(f"第 1 轮末尾词 '吃' 对下一个词的预测:")
    print(
        f"预测概率最高的词是: ID={next_token_id} 即['{next_token_word}'](概率: {next_token_probs[next_token_id].item():.4f})"
    )
    print("-" * 60)

    print("\n" + "=" * 80)
    print(
        "[第二轮前向传播]: 把预测的 '面' 追加到末尾, 全量重算 ['我', '爱', '吃', '面'] (seq_len = 4)"
    )
    print("=" * 80)

    input_ids_2 = torch.tensor([[1, 2, 3, 4]])
    with torch.no_grad():
        Q2, K2, V2, probs2 = model(input_ids_2)

    # 核心结论展示
    print("\n" + "=" * 80)
    print("[最终数值对比验证]")
    print("=" * 80)
    print(f"前 3 个 Token 的 K 是否 100% 重复重算? {torch.allclose(K1[0], K2[0, :3])}")
    print(f"前 3 个 Token 的 V 是否 100% 重复重算? {torch.allclose(V1[0], V2[0, :3])}")
    print(f"前 3 个 Token 的 Q 是否 100% 重复重算? {torch.allclose(Q1[0], Q2[0, :3])}")
    print(
        "\n总结提示: 观察上方输出可知, 第 2 轮前 3 个位置的 Q、K、V、raw_scores、ffn 都在机械重复执行."
    )
    print(
        "而第 2 轮为了生成第 5 个字, 真正用到的仅仅是第 2 轮中的 Q[-1] (即'面'的Q) 以及全局拼接的历史 K 和 V!"
    )


if __name__ == "__main__":
    main()
"""
root@413cb62f96b6:/code/KV_Cache# python3 kv_05.py

================================================================================
[第一轮前向传播]: 输入 Prompt 提示词 ['我', '爱', '吃'] (seq_len = 3)
================================================================================

############################## 前向传播开始 (当前序列长度 = 3) ##############################
输入 input_ids 形状: torch.Size([1, 3])
输入 input_ids:
tensor([[1, 2, 3]])

[Layer 1: Embedding 输出]
X 的形状: torch.Size([1, 3, 4]) -> [batch, seq_len, d_model]
X:
tensor([[[ 0.678, -1.235, -0.043, -1.605],
         [ 0.356, -0.687, -0.493,  0.241],
         [-1.111,  0.092, -2.317, -0.217]]])

[Layer 2: 投影计算 Q, K, V]
Q 的形状: torch.Size([1, 3, 4]) | Q:
tensor([[[-0.467,  0.310,  0.880, -1.105],
         [ 0.145,  0.132,  0.497, -0.439],
         [-0.746, -1.029,  0.879,  0.085]]])
K 的形状: torch.Size([1, 3, 4]) | K:
tensor([[[ 0.671,  0.712,  0.690, -0.121],
         [-0.217,  0.128, -0.150, -0.083],
         [-1.006, -0.386, -1.076, -0.774]]])
V 的形状: torch.Size([1, 3, 4]) | V:
tensor([[[ 1.485, -1.153,  0.559,  0.963],
         [ 0.605, -0.247, -0.038, -0.045],
         [ 0.662, -0.113, -0.315, -0.926]]])

------------------------- 步骤 3 深度展开: 因果自注意力计算 -------------------------
1. K 转置矩阵 K_T 形状: torch.Size([1, 4, 3]) -> [batch, d_model, seq_len]
   K_T:
tensor([[[ 0.671, -0.217, -1.006],
         [ 0.712,  0.128, -0.386],
         [ 0.690, -0.150, -1.076],
         [-0.121, -0.083, -0.774]]])

2. 点积结果 (Q @ K_T) 形状: torch.Size([1, 3, 3]) -> [batch, seq_len, seq_len]
   raw_scores:
tensor([[[ 0.648,  0.100,  0.259],
         [ 0.588, -0.053, -0.392],
         [-0.638, -0.109,  0.136]]])

3. 缩放打分 (除以 sqrt(4)=2.0) 形状: torch.Size([1, 3, 3])
   scores:
tensor([[[ 0.324,  0.050,  0.129],
         [ 0.294, -0.026, -0.196],
         [-0.319, -0.054,  0.068]]])

4. 因果掩码 mask 形状: torch.Size([3, 3]) (严格上三角为 -inf)
   mask:
tensor([[0., -inf, -inf],
        [0., 0., -inf],
        [0., 0., 0.]])

5. 遮蔽后的打分 masked_scores (scores + mask) 形状: torch.Size([1, 3, 3])
   masked_scores:
tensor([[[ 0.324,   -inf,   -inf],
         [ 0.294, -0.026,   -inf],
         [-0.319, -0.054,  0.068]]])

6. 注意力权重矩阵 attn_weights (Softmax 后) 形状: torch.Size([1, 3, 3])
   attn_weights:
tensor([[[1.000, 0.000, 0.000],
         [0.579, 0.421, 0.000],
         [0.265, 0.345, 0.390]]])

7. 加权求和上下文 context (attn_weights @ V) 形状: torch.Size([1, 3, 4]) -> [batch, seq_len, d_model]
   context:
tensor([[[ 1.485, -1.153,  0.559,  0.963],
         [ 1.115, -0.772,  0.308,  0.539],
         [ 0.860, -0.434,  0.012, -0.122]]])

8. 注意力最终投影输出 attn_out (w_out(context)) 形状: torch.Size([1, 3, 4])
   attn_out:
tensor([[[-0.614, -0.409,  0.309, -0.956],
         [-0.435, -0.186,  0.325, -0.631],
         [-0.266,  0.137,  0.524, -0.257]]])

------------------------- 步骤 4 深度展开: 前馈神经网络 (FFN) -------------------------
1. FFN 升维层 Linear(4 -> 8) 形状: torch.Size([1, 3, 8])
   ffn_linear1_out:
tensor([[[-0.151, -0.034,  0.297,  0.242,  0.583,  0.244,  0.138, -0.108],
         [-0.321, -0.145,  0.161,  0.057,  0.431, -0.013,  0.249, -0.171],
         [-0.616, -0.186, -0.091, -0.226,  0.238, -0.347,  0.431, -0.230]]])

2. ReLU 激活输出 (所有负数被置 0) 形状: torch.Size([1, 3, 8])
   ffn_relu_out:
tensor([[[0.000, 0.000, 0.297, 0.242, 0.583, 0.244, 0.138, 0.000],
         [0.000, 0.000, 0.161, 0.057, 0.431, 0.000, 0.249, 0.000],
         [0.000, 0.000, 0.000, 0.000, 0.238, 0.000, 0.431, 0.000]]])

3. FFN 降维层 Linear(8 -> 4) (即最终 ffn_out) 形状: torch.Size([1, 3, 4])
   ffn_out:
tensor([[[-0.009,  0.315,  0.263, -0.325],
         [-0.057,  0.273,  0.287, -0.328],
         [-0.149,  0.221,  0.239, -0.373]]])

------------------------- 步骤 5 深度展开: 语言模型头 (LM Head) 预测概率 -------------------------
1. 未归一化打分 logits (Linear(4 -> 6)) 形状: torch.Size([1, 3, 6]) -> [batch, seq_len, vocab_size]
   logits:
tensor([[[ 0.137, -0.143, -0.263, -0.292,  4.814,  0.162],
         [ 0.123, -0.162, -0.260, -0.326,  4.817,  0.201],
         [ 0.103, -0.205, -0.240, -0.371,  4.806,  0.224]]])

2. 最终归一化概率分布 probs (Softmax 后, 每行求和为 1.0) 形状: torch.Size([1, 3, 6])
   probs:
tensor([[[0.009, 0.007, 0.006, 0.006, 0.963, 0.009],
         [0.009, 0.007, 0.006, 0.006, 0.963, 0.010],
         [0.009, 0.006, 0.006, 0.005, 0.963, 0.010]]])

------------------------------------------------------------
第 1 轮末尾词 '吃' 对下一个词的预测:
预测概率最高的词是: ID=4 即['面'](概率: 0.9633)
------------------------------------------------------------

================================================================================
[第二轮前向传播]: 把预测的 '面' 追加到末尾, 全量重算 ['我', '爱', '吃', '面'] (seq_len = 4)
================================================================================

############################## 前向传播开始 (当前序列长度 = 4) ##############################
输入 input_ids 形状: torch.Size([1, 4])
输入 input_ids:
tensor([[1, 2, 3, 4]])

[Layer 1: Embedding 输出]
X 的形状: torch.Size([1, 4, 4]) -> [batch, seq_len, d_model]
X:
tensor([[[ 0.678, -1.235, -0.043, -1.605],
         [ 0.356, -0.687, -0.493,  0.241],
         [-1.111,  0.092, -2.317, -0.217],
         [-0.310, -0.396,  0.803, -0.622]]])

[Layer 2: 投影计算 Q, K, V]
Q 的形状: torch.Size([1, 4, 4]) | Q:
tensor([[[-0.467,  0.310,  0.880, -1.105],
         [ 0.145,  0.132,  0.497, -0.439],
         [-0.746, -1.029,  0.879,  0.085],
         [-0.096,  0.173, -0.236, -0.057]]])
K 的形状: torch.Size([1, 4, 4]) | K:
tensor([[[ 0.671,  0.712,  0.690, -0.121],
         [-0.217,  0.128, -0.150, -0.083],
         [-1.006, -0.386, -1.076, -0.774],
         [ 0.490,  0.356,  0.511,  0.468]]])
V 的形状: torch.Size([1, 4, 4]) | V:
tensor([[[ 1.485, -1.153,  0.559,  0.963],
         [ 0.605, -0.247, -0.038, -0.045],
         [ 0.662, -0.113, -0.315, -0.926],
         [-0.141, -0.090,  0.554,  0.424]]])

------------------------- 步骤 3 深度展开: 因果自注意力计算 -------------------------
1. K 转置矩阵 K_T 形状: torch.Size([1, 4, 4]) -> [batch, d_model, seq_len]
   K_T:
tensor([[[ 0.671, -0.217, -1.006,  0.490],
         [ 0.712,  0.128, -0.386,  0.356],
         [ 0.690, -0.150, -1.076,  0.511],
         [-0.121, -0.083, -0.774,  0.468]]])

2. 点积结果 (Q @ K_T) 形状: torch.Size([1, 4, 4]) -> [batch, seq_len, seq_len]
   raw_scores:
tensor([[[ 0.648,  0.100,  0.259, -0.186],
         [ 0.588, -0.053, -0.392,  0.167],
         [-0.638, -0.109,  0.136, -0.243],
         [-0.097,  0.083,  0.327, -0.132]]])

3. 缩放打分 (除以 sqrt(4)=2.0) 形状: torch.Size([1, 4, 4])
   scores:
tensor([[[ 0.324,  0.050,  0.129, -0.093],
         [ 0.294, -0.026, -0.196,  0.083],
         [-0.319, -0.054,  0.068, -0.121],
         [-0.049,  0.042,  0.164, -0.066]]])

4. 因果掩码 mask 形状: torch.Size([4, 4]) (严格上三角为 -inf)
   mask:
tensor([[0., -inf, -inf, -inf],
        [0., 0., -inf, -inf],
        [0., 0., 0., -inf],
        [0., 0., 0., 0.]])

5. 遮蔽后的打分 masked_scores (scores + mask) 形状: torch.Size([1, 4, 4])
   masked_scores:
tensor([[[ 0.324,   -inf,   -inf,   -inf],
         [ 0.294, -0.026,   -inf,   -inf],
         [-0.319, -0.054,  0.068,   -inf],
         [-0.049,  0.042,  0.164, -0.066]]])

6. 注意力权重矩阵 attn_weights (Softmax 后) 形状: torch.Size([1, 4, 4])
   attn_weights:
tensor([[[1.000, 0.000, 0.000, 0.000],
         [0.579, 0.421, 0.000, 0.000],
         [0.265, 0.345, 0.390, 0.000],
         [0.232, 0.254, 0.287, 0.228]]])

7. 加权求和上下文 context (attn_weights @ V) 形状: torch.Size([1, 4, 4]) -> [batch, seq_len, d_model]
   context:
tensor([[[ 1.485, -1.153,  0.559,  0.963],
         [ 1.115, -0.772,  0.308,  0.539],
         [ 0.860, -0.434,  0.012, -0.122],
         [ 0.655, -0.383,  0.156,  0.043]]])

8. 注意力最终投影输出 attn_out (w_out(context)) 形状: torch.Size([1, 4, 4])
   attn_out:
tensor([[[-0.614, -0.409,  0.309, -0.956],
         [-0.435, -0.186,  0.325, -0.631],
         [-0.266,  0.137,  0.524, -0.257],
         [-0.213, -0.003,  0.316, -0.261]]])

------------------------- 步骤 4 深度展开: 前馈神经网络 (FFN) -------------------------
1. FFN 升维层 Linear(4 -> 8) 形状: torch.Size([1, 4, 8])
   ffn_linear1_out:
tensor([[[-0.151, -0.034,  0.297,  0.242,  0.583,  0.244,  0.138, -0.108],
         [-0.321, -0.145,  0.161,  0.057,  0.431, -0.013,  0.249, -0.171],
         [-0.616, -0.186, -0.091, -0.226,  0.238, -0.347,  0.431, -0.230],
         [-0.479, -0.270,  0.051, -0.115,  0.272, -0.288,  0.378, -0.271]]])

2. ReLU 激活输出 (所有负数被置 0) 形状: torch.Size([1, 4, 8])
   ffn_relu_out:
tensor([[[0.000, 0.000, 0.297, 0.242, 0.583, 0.244, 0.138, 0.000],
         [0.000, 0.000, 0.161, 0.057, 0.431, 0.000, 0.249, 0.000],
         [0.000, 0.000, 0.000, 0.000, 0.238, 0.000, 0.431, 0.000],
         [0.000, 0.000, 0.051, 0.000, 0.272, 0.000, 0.378, 0.000]]])

3. FFN 降维层 Linear(8 -> 4) (即最终 ffn_out) 形状: torch.Size([1, 4, 4])
   ffn_out:
tensor([[[-0.009,  0.315,  0.263, -0.325],
         [-0.057,  0.273,  0.287, -0.328],
         [-0.149,  0.221,  0.239, -0.373],
         [-0.133,  0.237,  0.255, -0.364]]])

------------------------- 步骤 5 深度展开: 语言模型头 (LM Head) 预测概率 -------------------------
1. 未归一化打分 logits (Linear(4 -> 6)) 形状: torch.Size([1, 4, 6]) -> [batch, seq_len, vocab_size]
   logits:
tensor([[[ 0.137, -0.143, -0.263, -0.292,  4.814,  0.162],
         [ 0.123, -0.162, -0.260, -0.326,  4.817,  0.201],
         [ 0.103, -0.205, -0.240, -0.371,  4.806,  0.224],
         [ 0.109, -0.194, -0.244, -0.360,  4.809,  0.222]]])

2. 最终归一化概率分布 probs (Softmax 后, 每行求和为 1.0) 形状: torch.Size([1, 4, 6])
   probs:
tensor([[[0.009, 0.007, 0.006, 0.006, 0.963, 0.009],
         [0.009, 0.007, 0.006, 0.006, 0.963, 0.010],
         [0.009, 0.006, 0.006, 0.005, 0.963, 0.010],
         [0.009, 0.006, 0.006, 0.005, 0.963, 0.010]]])

================================================================================
[最终数值对比验证]
================================================================================
前 3 个 Token 的 K 是否 100% 重复重算? True
前 3 个 Token 的 V 是否 100% 重复重算? True
前 3 个 Token 的 Q 是否 100% 重复重算? True

总结提示: 观察上方输出可知, 第 2 轮前 3 个位置的 Q、K、V、raw_scores、ffn 都在机械重复执行.
而第 2 轮为了生成第 5 个字, 真正用到的仅仅是第 2 轮中的 Q[-1] (即'面'的Q) 以及全局拼接的历史 K 和 V!
root@413cb62f96b6:/code/KV_Cache#
"""
