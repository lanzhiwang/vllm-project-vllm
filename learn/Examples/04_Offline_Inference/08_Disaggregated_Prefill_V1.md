# Disaggregated Prefill V1
分散式预填充 V1

* https://docs.vllm.ai/en/v0.20.0/examples/offline_inference/disaggregated-prefill-v1/

Source https://github.com/vllm-project/vllm/tree/main/examples/offline_inference/disaggregated-prefill-v1

This example contains scripts that demonstrate disaggregated prefill in the offline setting of vLLM.
此示例包含演示 vLLM 离线设置中的分解预填充的脚本.

## Files

- `run.sh` - A helper script that will run `prefill_example.py` and `decode_example.py` sequentially.
  `run.sh` - 一个辅助脚本, 将按顺序运行 `prefill_example.py` 和 `decode_example.py`.

  - Make sure you are in the `examples/offline_inference/disaggregated-prefill-v1` directory before running `run.sh`.
    在运行 `run.sh` 之前, 请确保您位于 `examples/offline_inference/disaggregated-prefill-v1` 目录中.


- `prefill_example.py` - A script which performs prefill only, saving the KV state to the `local_storage` directory and the prompts to `output.txt`.
  `prefill_example.py` - 仅执行预填充的脚本, 将 KV 状态保存到 `local_storage` 目录并将提示保存到 `output.txt`.

- `decode_example.py` - A script which performs decode only, loading the KV state from the `local_storage` directory and the prompts from `output.txt`.
  `decode_example.py` - 仅执行解码的脚本, 从 `local_storage` 目录加载 KV 状态并从 `output.txt` 中加载提示.

## Example materials
示例材料

* decode_example.py

* prefill_example.py

* run.sh
