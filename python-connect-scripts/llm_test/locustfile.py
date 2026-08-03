"""Locust 阶梯负载脚本，用于压测兼容 OpenAI 格式的大模型接口。"""

from __future__ import annotations

import random

from faker import Faker
from locust import HttpUser, LoadTestShape, between, task

from common import (
    DATA_DIR,
    build_chat_payload,
    estimate_tokens,
    extract_answer,
    get_encoding,
    load_config,
    read_jsonl,
    request_timeout,
    token_bucket,
)


# 第1部分：每个 Locust 工作进程启动时，只加载一次公共配置和测试题库。
CONFIG = load_config()
CASES = read_jsonl(DATA_DIR / "test_cases.jsonl")
if not CASES:
    raise RuntimeError("题库不存在，请先执行：python generate_cases.py")
ENCODING = get_encoding(CONFIG)


# 第2部分：为随机题目追加可复现的虚构信息，避免所有请求内容完全相同。
FAKE = Faker("zh_CN")
FAKE.seed_instance(int(CONFIG["dataset"]["seed"]))


def build_load_case() -> dict:
    """返回一条压测用例，并为非固定题追加虚构随机信息。"""
    case = dict(random.choice(CASES))

    # 固定断言题不能修改；没有固定答案的随机题才追加虚构请求标识。
    if case.get("expected_contains") is None and not case.get("expect_json"):
        suffix = (
            f"\n本次虚构请求标识：{FAKE.uuid4()}，"
            f"虚构公司：{FAKE.company()}，虚构IP：{FAKE.ipv4_private()}。"
        )
        case["prompt"] += suffix
        case["estimated_input_tokens"] = estimate_tokens(case["prompt"], ENCODING)
        case["length_bucket"] = token_bucket(
            case["estimated_input_tokens"], CONFIG
        )
    return case


# 第3部分：定义虚拟用户行为，并把空回答、结构错误和内容错误记为业务失败。
class LLMUser(HttpUser):
    # 默认使用配置文件地址；命令行传入 --host 时由 Locust 覆盖该地址。
    host = CONFIG["base_url"]
    wait_time = between(
        float(CONFIG["locust"]["wait_min_seconds"]),
        float(CONFIG["locust"]["wait_max_seconds"]),
    )

    @task
    def chat_completion(self) -> None:
        """发送一次模型请求，并把协议或业务校验失败上报给 Locust。"""
        case = build_load_case()
        request_name = f"chat_{case['length_bucket']}"

        with self.client.post(
            CONFIG["chat_endpoint"],
            json=build_chat_payload(CONFIG, case),
            timeout=request_timeout(CONFIG),
            name=request_name,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code}")
                return

            try:
                data = response.json()
                answer = extract_answer(data)
            except Exception as error:
                response.failure(f"invalid_response: {error}")
                return

            if not answer:
                response.failure("empty_answer")
                return

            expected = case.get("expected_contains")
            if expected is not None and str(expected) not in answer:
                response.failure("content_check_failed")
                return

            response.success()


# 第4部分：读取配置中的阶段，依次执行预热、升压、高压和恢复负载。
class StagedLoadShape(LoadTestShape):
    """根据 config.json 的累计时间节点控制用户数和用户启动速率。"""
    stages = CONFIG["locust"]["stages"]

    def tick(self):
        """返回当前阶段的用户数和启动速率；全部阶段结束后返回 None。"""
        run_time = self.get_run_time()
        elapsed_limit = 0

        for stage in self.stages:
            elapsed_limit = int(stage["duration_seconds"])
            if run_time < elapsed_limit:
                return int(stage["users"]), float(stage["spawn_rate"])
        return None
