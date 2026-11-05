import torch
import torch.nn as nn

# 1. 模拟文本输入的 Token IDs(对应 2 个句子, 每句 3 个 token)
# batch_size = 2, seq_len = 3
input_ids = torch.tensor(
    [[101, 205, 308], [102, 205, 309]]  # "我 喜欢 猫"  # "你 喜欢 狗"
)

vocab_size = 500  # 词表总大小
d_model = 4  # 每个词映射成 4 维特征向量

# 2. 定义 Embedding 层(相当于字典查表映射)
embedding_layer = nn.Embedding(num_embeddings=vocab_size, embedding_dim=d_model)

# 3. 前向查表
embeddings = embedding_layer(input_ids)

print("原始 input_ids 的形状 [batch_size, seq_len]:", input_ids.shape)
print("转成数值向量后的形状 [batch_size, seq_len, d_model]:", embeddings.shape)
print("\n查看具体嵌入矩阵:\n", embeddings)
print("\n查看'我 喜欢 猫'对应的具体嵌入矩阵:\n", embeddings[0])

"""
root@c80c6635b325:/code/KV_Cache# python3 kv_02.py
原始 input_ids 的形状 [batch_size, seq_len]: torch.Size([2, 3])
转成数值向量后的形状 [batch_size, seq_len, d_model]: torch.Size([2, 3, 4])

查看具体嵌入矩阵:
 tensor([[[ 0.3910, -0.3586, -0.3067, -0.9551],
         [-1.3485,  0.4886, -0.7512,  1.1522],
         [-1.1318,  0.2457, -0.1834,  0.1854]],

        [[-1.1426, -0.3183,  0.8585,  0.9974],
         [-1.3485,  0.4886, -0.7512,  1.1522],
         [ 0.1699, -0.4245,  0.9355,  1.2780]]], grad_fn=<EmbeddingBackward0>)

查看'我 喜欢 猫'对应的具体嵌入矩阵:
 tensor([[ 0.3910, -0.3586, -0.3067, -0.9551],
        [-1.3485,  0.4886, -0.7512,  1.1522],
        [-1.1318,  0.2457, -0.1834,  0.1854]], grad_fn=<SelectBackward0>)
root@c80c6635b325:/code/KV_Cache#
"""
