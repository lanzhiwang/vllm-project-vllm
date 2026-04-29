# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

import argparse

from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"


def parse_args():
    parser = argparse.ArgumentParser(description="Client for vLLM API server")
    """
    action="store_true" 的作用是将该参数定义为一个"开关"(Switch)或"布尔标志"(Boolean Flag).
    当你设置了 action="store_true" 时:
    如果用户在命令行中输入了该参数(例如 `python app.py --stream`): 变量 `args.stream` 的值将被自动设为 `True`.
    如果用户没有输入该参数: 变量 `args.stream` 的值将默认为 `False`.

    高级开发者的进阶理解

    无需指定类型: 使用 `store_true` 时, 你不需要指定 `type=bool`. 实际上, 如果在 `argparse` 中对这种标志位使用 `type=bool` 往往会产生非预期的结果.

    反向操作: 如果你需要默认开启, 而通过参数关闭, 可以使用 `action="store_false"`.

    默认值: 当 `action="store_true"` 时, 该参数的默认 `default` 值为 `False`.
    如果你显式设置 `default=True`, 那么无论用户加不加参数, 它都将是 `True`(这就失去了开关的意义), 所以通常保持默认即可.

    短参数配合: 在高级实践中, 我们通常会配合短参数一起使用, 增强用户体验:
    parser.add_argument("-s", "--stream", action="store_true")
    """
    parser.add_argument(
        "--stream", action="store_true", help="Enable streaming response"
    )
    return parser.parse_args()


def main(args):
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=openai_api_key,
        base_url=openai_api_base,
    )

    models = client.models.list()
    model = models.data[0].id

    # Completion API
    completion = client.completions.create(
        model=model,
        prompt="A robot may not injure a human being",
        echo=False,
        n=2,
        stream=args.stream,
        logprobs=3,
    )

    print("-" * 50)
    print("Completion results:")
    if args.stream:
        for c in completion:
            print(c)
    else:
        print(completion)
    print("-" * 50)


if __name__ == "__main__":
    args = parse_args()
    main(args)
