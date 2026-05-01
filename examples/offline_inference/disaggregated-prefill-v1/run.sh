set -x

rm -rf local_storage/

if [ -f "output.txt" ]; then
    rm output.txt
fi

# The directory of current script
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
# +++ readlink -f ./run.sh
# ++ dirname /Users/huzhi/work/code/py_code/vllm/examples/offline_inference/disaggregated-prefill-v1/run.sh
# + SCRIPT_DIR=/Users/huzhi/work/code/py_code/vllm/examples/offline_inference/disaggregated-prefill-v1

VLLM_ENABLE_V1_MULTIPROCESSING=0 CUDA_VISIBLE_DEVICES=0 python3 "$SCRIPT_DIR/prefill_example.py"
VLLM_ENABLE_V1_MULTIPROCESSING=0 CUDA_VISIBLE_DEVICES=0 python3 "$SCRIPT_DIR/decode_example.py"
