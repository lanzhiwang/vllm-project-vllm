# Disaggregated Serving

* https://docs.vllm.ai/en/v0.20.0/examples/online_serving/disaggregated_serving

Source https://github.com/vllm-project/vllm/tree/main/examples/online_serving/disaggregated_serving.

This example contains scripts that demonstrate the disaggregated serving features of vLLM.
本示例包含演示 vLLM 解耦服务功能的脚本.

## Files

- `disagg_proxy_demo.py` - Demonstrates XpYd (X prefill instances, Y decode instances).
  `disagg_proxy_demo.py` - 演示 XpYd(X 预填充实例, Y 解码实例).

- `kv_events.sh` - Demonstrates KV cache event publishing.
  `kv_events.sh` - 演示 KV 缓存事件发布.

- `mooncake_connector` - A proxy demo for MooncakeConnector.
  `mooncake_connector` - MooncakeConnector 的代理演示.

## Example materials
