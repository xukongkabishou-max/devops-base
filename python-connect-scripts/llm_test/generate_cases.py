"""使用 Faker 和固定模板生成可重复使用、可复现的大模型测试题库。"""

from __future__ import annotations

import argparse
import json
from typing import Any

from faker import Faker

from common import DATA_DIR, ensure_runtime_dirs, estimate_tokens, get_encoding, load_config


# 第1部分：定义具有明确预期结果、可以由程序自动判断对错的固定题目。
FIXED_CASES = [
    {
        "category": "exact_answer",
        "prompt": "请只回答数字：1加1等于多少？",
        "expected_contains": "2",
        "max_output_tokens": 20,
    },
    {
        "category": "exact_answer",
        "prompt": "请只回答英文单词：HTTP状态码200表示成功还是失败？",
        "expected_contains": "成功",
        "max_output_tokens": 30,
    },
    {
        "category": "json_output",
        "prompt": (
            "请只返回合法JSON，不要使用Markdown代码块："
            '{"service":"demo","healthy":true}'
        ),
        "expected_contains": "service",
        "expect_json": True,
        "max_output_tokens": 80,
    },
    {
        "category": "english",
        "prompt": "Reply with the single word OK in uppercase.",
        "expected_contains": "OK",
        "max_output_tokens": 20,
    },
    {
        "category": "special_chars",
        "prompt": "请原样返回字符串：demo_123-测试@example.com",
        "expected_contains": "demo_123-测试@example.com",
        "max_output_tokens": 50,
    },
]


# 第2部分：使用 Faker 生成接近真实业务形式但不包含真实信息的随机题目。
def random_prompt(fake_zh: Faker, fake_en: Faker, index: int) -> dict[str, Any]:
    """根据序号轮换业务、摘要、代码、中英文题型，返回一条随机题目。"""
    category = index % 5

    if category == 0:
        return {
            "category": "random_business",
            "prompt": (
                f"虚构公司：{fake_zh.company()}，虚构内网IP：{fake_zh.ipv4_private()}，"
                f"告警编号：{fake_zh.bothify('ALERT-####-????')}。"
                "请用三句话给出通用故障排查思路。"
            ),
        }
    if category == 1:
        return {
            "category": "summary",
            "prompt": f"请将以下虚构文本总结为三点：{fake_zh.paragraph(nb_sentences=8)}",
        }
    if category == 2:
        return {
            "category": "code",
            "prompt": (
                "请写一个不访问网络的Python函数，对以下虚构服务名去重并排序："
                f"{fake_zh.word()}、{fake_zh.word()}、{fake_zh.word()}。"
            ),
        }
    if category == 3:
        return {
            "category": "chinese",
            "prompt": f"请解释这个虚构运维事件可能的处理步骤：{fake_zh.sentence(nb_words=20)}",
        }
    return {
        "category": "english",
        "prompt": f"Summarize this fictional incident: {fake_en.paragraph(nb_sentences=6)}",
    }


# 第3部分：通过追加虚构文本，将题目扩展到短、中、长三种 Token 目标范围。
def extend_to_target(
    prompt: str,
    target_tokens: int,
    fake: Faker,
    encoding,
) -> str:
    """持续追加虚构段落，直到文本达到目标估算 Token 数。"""
    parts = [prompt]
    while estimate_tokens("\n".join(parts), encoding) < target_tokens:
        parts.append(fake.paragraph(nb_sentences=8))
    return "\n".join(parts)


# 第4部分：生成完整题库，并为每道题增加编号、类型和估算 Token 等元数据。
def generate_cases(config: dict[str, Any], count: int) -> list[dict[str, Any]]:
    """按照配置生成指定数量的测试用例，并返回完整题库列表。"""
    seed = int(config["dataset"]["seed"])
    Faker.seed(seed)
    fake_zh = Faker("zh_CN")
    fake_en = Faker("en_US")
    fake_zh.seed_instance(seed)
    fake_en.seed_instance(seed + 1)
    encoding = get_encoding(config)

    targets = [
        ("short", int(config["dataset"]["short_token_target"])),
        ("medium", int(config["dataset"]["medium_token_target"])),
        ("long", int(config["dataset"]["long_token_target"])),
    ]
    cases: list[dict[str, Any]] = []

    for index in range(count):
        source = (
            dict(FIXED_CASES[index])
            if index < len(FIXED_CASES)
            else random_prompt(fake_zh, fake_en, index)
        )
        bucket, target = targets[index % len(targets)]

        # 固定断言题保持短输入，避免追加文本改变题意和预期答案。
        if index >= len(FIXED_CASES):
            source["prompt"] = extend_to_target(
                source["prompt"], target, fake_zh, encoding
            )
        estimated = estimate_tokens(source["prompt"], encoding)

        cases.append(
            {
                "case_id": f"case-{index + 1:04d}",
                **source,
                "length_bucket": bucket if index >= len(FIXED_CASES) else "short",
                "estimated_input_tokens": estimated,
                "max_output_tokens": source.get(
                    "max_output_tokens", config["default_max_output_tokens"]
                ),
            }
        )
    return cases


# 第5部分：将题库写成 JSONL 文件，并输出数量、长度分布和 Token 范围。
def main() -> None:
    """解析命令参数，生成 data/test_cases.jsonl，并打印题库统计。"""
    parser = argparse.ArgumentParser(description="生成可复现的大模型测试题库")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--count", type=int, help="临时覆盖配置中的题目数量")
    args = parser.parse_args()

    config = load_config(args.config)
    count = args.count or int(config["dataset"]["case_count"])
    if count <= 0:
        raise SystemExit("--count 必须大于0")

    ensure_runtime_dirs()
    cases = generate_cases(config, count)
    output_path = DATA_DIR / "test_cases.jsonl"
    with output_path.open("w", encoding="utf-8") as file_object:
        for case in cases:
            file_object.write(json.dumps(case, ensure_ascii=False) + "\n")

    buckets = {
        name: sum(case["length_bucket"] == name for case in cases)
        for name in ("short", "medium", "long")
    }
    token_values = [case["estimated_input_tokens"] for case in cases]
    print(f"题库已生成：{output_path}")
    print(f"总数量：{len(cases)}")
    print(f"长度分布：{buckets}")
    print(f"估算Token范围：{min(token_values)} - {max(token_values)}")


if __name__ == "__main__":
    main()
