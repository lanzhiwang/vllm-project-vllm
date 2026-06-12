```bash

docker pull python:3.12.13
docker pull vllm/vllm-openai-cpu:v0.20.0

docker run -ti --rm \
--network host \
-v /Users/huzhi/work/code/py_code/vllm:/vllm \
-w /vllm/examples/online_serving \
--name vllm-client \
python:3.12.13 bash

docker run -ti --rm \
--network host \
--entrypoint /usr/bin/env \
-v /Users/huzhi/work/code/py_code/vllm:/vllm \
-w /vllm/examples/online_serving \
--name vllm-client \
vllm/vllm-openai-cpu:v0.20.0 bash

pip install black==26.5.1 -i https://pypi.tuna.tsinghua.edu.cn/simple

find . -name "*.py" -exec black --target-version py312 {} \;
find ./examples/online_serving -name "*.sh" -exec shfmt -i 4 -w {} \;

```
