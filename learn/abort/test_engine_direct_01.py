import asyncio
import time
from vllm import AsyncEngineArgs, AsyncLLMEngine, SamplingParams


async def main():
    print(f"[{time.strftime('%X')}] 正在初始化 vLLM 引擎核心...")
    engine_args = AsyncEngineArgs(
        model="/model/Qwen2.5-7B-Instruct",
        trust_remote_code=True,
        gpu_memory_utilization=0.95,
        max_model_len=4096,
        enable_log_requests=True,
    )
    engine = AsyncLLMEngine.from_engine_args(engine_args)

    prompt = "请详细写一篇关于人类探索宇宙历史的万字长文, 越详细越好."
    sampling_params = SamplingParams(max_tokens=4096, temperature=0.7)
    request_id = "test-direct-abort-001"

    print(f"[{time.strftime('%X')}] 发起直接引擎推理请求...")
    results_generator = engine.generate(prompt, sampling_params, request_id)

    count = 0
    async for request_output in results_generator:
        count += 1
        # 获取最新生成的 token 片段
        text = request_output.outputs[0].text
        print(f"[{time.strftime('%X')}] 生成 Step {count}, 当前文本长度: {len(text)}")

        # 当生成 10 个 step 时, 直接显式调用底层 abort()
        if count >= 10:
            print(
                f"\n[{time.strftime('%X')}] >>> 显式触发 engine.abort('{request_id}') <<<"
            )
            await engine.abort(request_id)
            break

    print(f"[{time.strftime('%X')}] 已调用 abort, 进入 15 秒观察期...")
    print(">>> 观察显卡负载 (nvidia-smi) 是否瞬间归 0 <<<")
    await asyncio.sleep(15)
    print(f"[{time.strftime('%X')}] 测试结束.")


if __name__ == "__main__":
    asyncio.run(main())

"""
root@0f094faa723f:/model# python3 test_engine_direct.py
[03:38:43] 正在初始化 vLLM 引擎核心...
WARNING 09-03 03:38:43 [envs.py:2057] Unknown vLLM environment variable detected: VLLM_BUILD_URL
WARNING 09-03 03:38:43 [envs.py:2057] Unknown vLLM environment variable detected: VLLM_IMAGE_TAG
WARNING 09-03 03:38:43 [envs.py:2057] Unknown vLLM environment variable detected: VLLM_BUILD_PIPELINE
WARNING 09-03 03:38:43 [envs.py:2057] Unknown vLLM environment variable detected: VLLM_BUILD_COMMIT
INFO 09-03 03:38:43 [model.py:617] Resolved architecture: Qwen2ForCausalLM
INFO 09-03 03:38:43 [model.py:1752] Using max model len 4096
INFO 09-03 03:38:43 [scheduler.py:239] Chunked prefill is enabled with max_num_batched_tokens=2048.
INFO 09-03 03:38:43 [vllm.py:977] Asynchronous scheduling is enabled.
INFO 09-03 03:38:43 [kernel.py:270] Final IR op priority after setting platform defaults: IrOpPriorityConfig(rms_norm=['native'], fused_add_rms_norm=['native'])
(EngineCore pid=1073) INFO 09-03 03:38:47 [core.py:112] Initializing a V1 LLM engine (v0.22.0) with config: model='/model/Qwen2.5-7B-Instruct', speculative_config=None, tokenizer='/model/Qwen2.5-7B-Instruct', skip_tokenizer_init=False, tokenizer_mode=auto, revision=None, tokenizer_revision=None, trust_remote_code=True, dtype=torch.bfloat16, max_seq_len=4096, download_dir=None, load_format=auto, tensor_parallel_size=1, pipeline_parallel_size=1, data_parallel_size=1, decode_context_parallel_size=1, dcp_comm_backend=ag_rs, disable_custom_all_reduce=False, quantization=None, quantization_config=None, enforce_eager=False, enable_return_routed_experts=False, kv_cache_dtype=auto, device_config=cuda, structured_outputs_config=StructuredOutputsConfig(backend='auto', disable_any_whitespace=False, disable_additional_properties=False, reasoning_parser='', reasoning_parser_plugin='', enable_in_reasoning=False), observability_config=ObservabilityConfig(show_hidden_metrics_for_version=None, otlp_traces_endpoint=None, collect_detailed_traces=None, kv_cache_metrics=False, kv_cache_metrics_sample=0.01, cudagraph_metrics=False, enable_layerwise_nvtx_tracing=False, enable_mfu_metrics=False, enable_mm_processor_stats=False, enable_logging_iteration_details=False), seed=0, served_model_name=/model/Qwen2.5-7B-Instruct, enable_prefix_caching=True, enable_chunked_prefill=True, pooler_config=None, compilation_config={'mode': <CompilationMode.VLLM_COMPILE: 3>, 'debug_dump_path': None, 'cache_dir': '', 'compile_cache_save_format': 'binary', 'backend': 'inductor', 'custom_ops': ['none'], 'ir_enable_torch_wrap': True, 'splitting_ops': ['vllm::unified_attention_with_output', 'vllm::unified_mla_attention_with_output', 'vllm::mamba_mixer2', 'vllm::mamba_mixer', 'vllm::short_conv', 'vllm::linear_attention', 'vllm::plamo2_mamba_mixer', 'vllm::qwen_gdn_attention_core', 'vllm::gdn_attention_core_xpu', 'vllm::olmo_hybrid_gdn_full_forward', 'vllm::kda_attention', 'vllm::sparse_attn_indexer', 'vllm::rocm_aiter_sparse_attn_indexer', 'vllm::deepseek_v4_attention', 'vllm::unified_kv_cache_update', 'vllm::unified_mla_kv_cache_update'], 'compile_mm_encoder': False, 'cudagraph_mm_encoder': False, 'encoder_cudagraph_token_budgets': [], 'encoder_cudagraph_max_vision_items_per_batch': 0, 'encoder_cudagraph_max_frames_per_batch': None, 'compile_sizes': [], 'compile_ranges_endpoints': [2048], 'inductor_compile_config': {'enable_auto_functionalized_v2': False, 'size_asserts': False, 'alignment_asserts': False, 'scalar_asserts': False, 'combo_kernels': True, 'benchmark_combo_kernel': True}, 'inductor_passes': {}, 'cudagraph_mode': <CUDAGraphMode.FULL_AND_PIECEWISE: (2, 1)>, 'cudagraph_num_of_warmups': 1, 'cudagraph_capture_sizes': [1, 2, 4, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, 152, 160, 168, 176, 184, 192, 200, 208, 216, 224, 232, 240, 248, 256], 'cudagraph_copy_inputs': False, 'cudagraph_specialize_lora': True, 'use_inductor_graph_partition': False, 'pass_config': {'fuse_norm_quant': False, 'fuse_act_quant': False, 'fuse_attn_quant': False, 'enable_sp': False, 'fuse_gemm_comms': False, 'fuse_allreduce_rms': False, 'fuse_rope_kvcache_cat_mla': False, 'fuse_act_padding': False}, 'max_cudagraph_capture_size': 256, 'dynamic_shapes_config': {'type': <DynamicShapesType.BACKED: 'backed'>, 'evaluate_guards': False, 'assume_32_bit_indexing': False}, 'local_cache_dir': None, 'fast_moe_cold_start': False, 'static_all_moe_layers': []}, kernel_config=KernelConfig(ir_op_priority=IrOpPriorityConfig(rms_norm=['native'], fused_add_rms_norm=['native']), enable_flashinfer_autotune=True, moe_backend='auto', linear_backend='auto')
(EngineCore pid=1073) <frozen importlib._bootstrap_external>:1297: FutureWarning: The cuda.cudart module is deprecated and will be removed in a future release, please switch to use the cuda.bindings.runtime module instead.
(EngineCore pid=1073) <frozen importlib._bootstrap_external>:1297: FutureWarning: The cuda.nvrtc module is deprecated and will be removed in a future release, please switch to use the cuda.bindings.nvrtc module instead.
(EngineCore pid=1073) INFO 09-03 03:38:50 [parallel_state.py:1422] world_size=1 rank=0 local_rank=0 distributed_init_method=tcp://10.41.0.4:55097 backend=nccl
(EngineCore pid=1073) INFO 09-03 03:38:50 [parallel_state.py:1735] rank 0 in world size 1 is assigned as DP rank 0, PP rank 0, PCP rank 0, TP rank 0, EP rank N/A, EPLB rank N/A
(EngineCore pid=1073) INFO 09-03 03:38:51 [topk_topp_sampler.py:45] Using FlashInfer for top-p & top-k sampling.
(EngineCore pid=1073) INFO 09-03 03:38:51 [gpu_model_runner.py:5037] Starting to load model /model/Qwen2.5-7B-Instruct...
(EngineCore pid=1073) INFO 09-03 03:38:52 [cuda.py:378] Using FLASH_ATTN attention backend out of potential backends: ['FLASH_ATTN', 'FLASHINFER', 'TRITON_ATTN', 'FLEX_ATTENTION'].
(EngineCore pid=1073) INFO 09-03 03:38:52 [flash_attn.py:636] Using FlashAttention version 2
(EngineCore pid=1073) INFO 09-03 03:38:52 [weight_utils.py:922] Filesystem type for checkpoints: XFS. Checkpoint size: 14.19 GiB. Available RAM: 163.21 GiB.
(EngineCore pid=1073) INFO 09-03 03:38:52 [weight_utils.py:945] Auto-prefetch is disabled because the filesystem (XFS) is not a recognized network FS (NFS/Lustre). If you want to force prefetching, start vLLM with --safetensors-load-strategy=prefetch.
Loading safetensors checkpoint shards:   0% Completed | 0/4 [00:00<?, ?it/s]
Loading safetensors checkpoint shards:  25% Completed | 1/4 [00:00<00:02,  1.23it/s]
Loading safetensors checkpoint shards:  50% Completed | 2/4 [00:01<00:01,  1.06it/s]
Loading safetensors checkpoint shards:  75% Completed | 3/4 [00:03<00:01,  1.05s/it]
Loading safetensors checkpoint shards: 100% Completed | 4/4 [00:04<00:00,  1.03s/it]
Loading safetensors checkpoint shards: 100% Completed | 4/4 [00:04<00:00,  1.00s/it]
(EngineCore pid=1073)
(EngineCore pid=1073) INFO 09-03 03:38:56 [default_loader.py:397] Loading weights took 4.18 seconds
(EngineCore pid=1073) INFO 09-03 03:38:57 [gpu_model_runner.py:5132] Model loading took 14.29 GiB memory and 4.660599 seconds
(EngineCore pid=1073) INFO 09-03 03:39:03 [backends.py:1089] Using cache directory: /root/.cache/vllm/torch_compile_cache/0c3e38ec09/rank_0_0/backbone for vLLM's torch.compile
(EngineCore pid=1073) INFO 09-03 03:39:03 [backends.py:1148] Dynamo bytecode transform time: 5.56 s
(EngineCore pid=1073) INFO 09-03 03:39:07 [backends.py:378] Cache the graph of compile range (1, 2048) for later use
(EngineCore pid=1073) INFO 09-03 03:39:12 [backends.py:393] Compiling a graph for compile range (1, 2048) takes 9.43 s
(EngineCore pid=1073) INFO 09-03 03:39:16 [decorators.py:708] saved AOT compiled function to /root/.cache/vllm/torch_compile_cache/torch_aot_compile/57744f895bc4fd8466d3c8be8640a15963d6f137420755b41f6c3c3f814d38d3/rank_0_0/model
(EngineCore pid=1073) INFO 09-03 03:39:16 [monitor.py:53] torch.compile took 19.20 s in total
(EngineCore pid=1073) INFO 09-03 03:39:17 [monitor.py:81] Initial profiling/warmup run took 0.64 s
(EngineCore pid=1073) INFO 09-03 03:39:27 [gpu_model_runner.py:6279] Profiling CUDA graph memory: PIECEWISE=35 (largest=256), FULL=19 (largest=128)
(EngineCore pid=1073) INFO 09-03 03:39:28 [gpu_model_runner.py:6365] Estimated CUDA graph memory: 0.37 GiB total
(EngineCore pid=1073) INFO 09-03 03:39:29 [gpu_worker.py:466] Available KV cache memory: 26.32 GiB
(EngineCore pid=1073) INFO 09-03 03:39:29 [gpu_worker.py:481] CUDA graph memory profiling is enabled (default since v0.21.0). The current --gpu-memory-utilization=0.9500 is equivalent to --gpu-memory-utilization=0.9417 without CUDA graph memory profiling. To maintain the same effective KV cache size as before, increase --gpu-memory-utilization to 0.9583. To disable, set VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0.
(EngineCore pid=1073) INFO 09-03 03:39:29 [kv_cache_utils.py:1733] GPU KV cache size: 492,912 tokens
(EngineCore pid=1073) INFO 09-03 03:39:29 [kv_cache_utils.py:1734] Maximum concurrency for 4,096 tokens per request: 120.34x
Capturing CUDA graphs (mixed prefill-decode, PIECEWISE): 100%|███████████████████████████████████████████████████████████████████████████████████| 35/35 [00:02<00:00, 17.15it/s]
Capturing CUDA graphs (decode, FULL): 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 19/19 [00:00<00:00, 22.23it/s]
(EngineCore pid=1073) INFO 09-03 03:39:33 [gpu_model_runner.py:6456] Graph capturing finished in 4 secs, took 0.31 GiB
(EngineCore pid=1073) INFO 09-03 03:39:33 [gpu_worker.py:619] CUDA graph pool memory: 0.31 GiB (actual), 0.37 GiB (estimated), difference: 0.05 GiB (17.4%).
(EngineCore pid=1073) INFO 09-03 03:39:33 [jit_monitor.py:54] Kernel JIT monitor activated — Triton JIT compilations during inference will be logged as warnings.
(EngineCore pid=1073) INFO 09-03 03:39:33 [core.py:302] init engine (profile, create kv cache, warmup model) took 36.07 s (compilation: 19.20 s)
(EngineCore pid=1073) INFO 09-03 03:39:33 [kernel.py:270] Final IR op priority after setting platform defaults: IrOpPriorityConfig(rms_norm=['native'], fused_add_rms_norm=['native'])
[03:39:33] 发起直接引擎推理请求...
WARNING 09-03 03:39:33 [input_processor.py:274] Passing raw prompts to InputProcessor is deprecated and will be removed in v0.18. You should instead pass the outputs of Renderer.render_cmpl() or Renderer.render_chat().
INFO 09-03 03:39:33 [async_llm.py:415] Added request test-direct-abort-001-8181cd7c.
(EngineCore pid=1073) WARNING 09-03 03:39:33 [jit_monitor.py:103] Triton kernel JIT compilation during inference: _compute_slot_mapping_kernel. This causes a latency spike; consider extending warmup to cover this shape/config.
[03:39:34] 生成 Step 1, 当前文本长度: 1
[03:39:34] 生成 Step 2, 当前文本长度: 3
[03:39:34] 生成 Step 3, 当前文本长度: 5
[03:39:34] 生成 Step 4, 当前文本长度: 7
[03:39:34] 生成 Step 5, 当前文本长度: 10
[03:39:34] 生成 Step 6, 当前文本长度: 11
[03:39:34] 生成 Step 7, 当前文本长度: 13
[03:39:34] 生成 Step 8, 当前文本长度: 15
[03:39:34] 生成 Step 9, 当前文本长度: 17
[03:39:34] 生成 Step 10, 当前文本长度: 19

[03:39:34] >>> 显式触发 engine.abort('test-direct-abort-001') <<<
INFO 09-03 03:39:34 [async_llm.py:721] Aborted request(s) test-direct-abort-001.
[03:39:34] 已调用 abort, 进入 15 秒观察期...
>>> 观察显卡负载 (nvidia-smi) 是否瞬间归 0 <<<
[03:39:49] 测试结束.
INFO 09-03 03:39:49 [async_llm.py:721] Aborted request(s) test-direct-abort-001-8181cd7c.
INFO 09-03 03:39:49 [async_llm.py:595] Request test-direct-abort-001 aborted.
(EngineCore pid=1073) INFO 09-03 03:39:49 [core.py:1266] Shutdown initiated (timeout=0)
(EngineCore pid=1073) INFO 09-03 03:39:49 [core.py:1289] Shutdown complete
root@0f094faa723f:/model#
"""
