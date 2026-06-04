# KV Load Failure Recovery Test

* https://docs.vllm.ai/en/v0.20.0/examples/offline_inference/kv_load_failure_recovery/#how-it-works


Source https://github.com/vllm-project/vllm/tree/main/examples/offline_inference/kv_load_failure_recovery

This example builds upon the `disaggregated-prefill-v1` example in `examples/offline_inference`.
本示例基于 `examples/offline_inference` 中的 `disaggregated-prefill-v1` 示例.

It demonstrates vLLM's ability to recover from KV load failures in both synchronous and asynchronous loading modes. The goal is to verify that vLLM correctly identifies invalid KV blocks, reschedules the affected requests, and ensures successful and consistent output.
它展示了 vLLM 在同步和异步加载模式下从键值存储 (KV) 负载故障中恢复的能力. 目标是验证 vLLM 是否能够正确识别无效的 KV 块, 重新调度受影响的请求, 并确保成功且一致的输出.

## Files

- `prefill_example.py` – performs the prefill stage and saves KV data (same as in `disaggregated-prefill-v1`).
  `prefill_example.py` – 执行预填充阶段并保存 KV 数据(与 `disaggregated-prefill-v1` 相同).

- `decode_example.py` – performs the decode stage. Accepts:
  `decode_example.py` – 执行解码阶段. 接受以下参数:

  - `--simulate-failure`: simulates KV load failure using a custom connector.
    `--simulate-failure` : 使用自定义连接器模拟 KV 负载故障.

  - `--async-load`: enables asynchronous KV loading mode.
    `--async-load` : 启用异步 KV 加载模式.

- `load_recovery_example_connector.py` – defines `LoadRecoveryExampleConnector`, a subclass of `ExampleConnector`, that simulates missing or corrupted external KV blocks by failing to load blocks for the first decode request.
  `load_recovery_example_connector.py` – 定义了 `LoadRecoveryExampleConnector`, 它是 `ExampleConnector` 的一个子类, 它通过无法加载第一个解码请求的块来模拟丢失或损坏的外部 KV 块.

- `run.sh` – orchestrates the test: runs the prefill stage, then three decode stages:
  `run.sh` – 协调测试: 运行预填充阶段, 然后运行三个解码阶段:

  1. Normal decode (baseline).
     正常解码(基线).

  2. Decode with simulated sync KV load failure.
     使用模拟同步 KV 负载故障进行解码.

  3. Decode with simulated async KV load failure.
     使用模拟异步 KV 负载故障进行解码.

  Finally, it compares the output of the baseline with the recovered outputs to verify correctness.
  最后, 它将基线输出与恢复的输出进行比较, 以验证正确性.

## How It Works

- The test dynamically loads `LoadRecoveryExampleConnector` via `KVTransferConfig.kv_connector_module_path`, enabling controlled simulation of load failures without modifying the original connector.
  该测试通过 `KVTransferConfig.kv_connector_module_path` 动态加载 `LoadRecoveryExampleConnector`, 从而可以在不修改原始连接器的情况下对负载故障进行受控模拟.

- The decode stages that simulate failure are expected to trigger recovery logic in vLLM, resulting in the same output as the baseline decode.
  模拟故障的解码阶段预计会触发 vLLM 中的恢复逻辑, 从而产生与基线解码相同的输出.

- If recovery fails, the script prints a unified diff of the output mismatch and exits with error.
  如果恢复失败, 脚本将打印输出不匹配的统一差异并报错退出.

## Usage

```bash
./run.sh
```

## Example materials
