"""大模型测试框架的公共函数，供其他测试脚本导入使用。"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Iterable

import requests
import tiktoken
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# 第1部分：统一计算框架根目录、题库目录和结果目录。
# 使用脚本自身位置计算路径，避免程序依赖执行命令时所在的目录。
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
RESULTS_DIR = ROOT_DIR / "results"
DEFAULT_CONFIG_PATH = ROOT_DIR / "config.json"


# 第2部分：读取 JSON 配置，并在需要写文件时自动创建运行目录。
def load_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """读取配置文件，返回供其他脚本使用的字典。"""
    path = Path(config_path)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_runtime_dirs() -> None:
    """自动创建 data 和 results 目录，不产生具体测试结果文件。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# 第3部分：拼接接口地址，避免路径中出现重复斜杠或缺少斜杠。
def build_url(base_url: str, endpoint: str) -> str:
    """把服务根地址和接口路径拼成可以直接请求的完整 URL。"""
    return f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"


# 第4部分：创建可复用的 HTTP Session，并配置保守的自动重试策略。
# 只自动重试不会改变服务端数据的 GET 请求，模型 POST 请求不自动重放。
def create_session(config: dict[str, Any]) -> requests.Session:
    """返回带公共请求头和 GET 重试策略的 Requests Session。"""
    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        read=0,
        status=2,
        backoff_factor=0.5,
        status_forcelist=(429, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))

    api_key = config.get("api_key")
    session.headers.update({"Content-Type": "application/json"})
    if api_key:
        session.headers.update({"Authorization": f"Bearer {api_key}"})
    return session


# 第5部分：初始化统一的 tiktoken 编码器，用于可重复的 Token 估算。
def get_encoding(config: dict[str, Any]) -> tiktoken.Encoding:
    """根据 config.json 的 encoding 名称返回 tiktoken 编码器。"""
    return tiktoken.get_encoding(config.get("encoding", "cl100k_base"))


def estimate_tokens(text: str, encoding: tiktoken.Encoding) -> int:
    """返回文本的估算 Token 数；该值不代表服务端精确用量。"""
    return len(encoding.encode(text))


def token_bucket(token_count: int, config: dict[str, Any]) -> str:
    """根据估算 Token 数返回 short、medium 或 long 长度分组。"""
    dataset = config["dataset"]
    if token_count <= dataset["short_token_target"]:
        return "short"
    if token_count <= dataset["medium_token_target"]:
        return "medium"
    return "long"


# 第6部分：根据配置和题库内容构造统一的 Chat Completions 请求体。
def build_chat_payload(config: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    """把一条测试用例转换成 OpenAI Chat Completions 请求体。"""
    return {
        "model": config["model"],
        "messages": [{"role": "user", "content": case["prompt"]}],
        "temperature": case.get("temperature", config["temperature"]),
        "max_tokens": case.get(
            "max_output_tokens", config["default_max_output_tokens"]
        ),
        "stream": False,
    }


# 第7部分：把不同 Python 异常转换成稳定的错误类型，方便报告分类统计。
def classify_exception(error: Exception) -> str:
    """把异常转换成报告使用的固定错误分类字符串。"""
    if isinstance(error, requests.ConnectTimeout):
        return "connect_timeout"
    if isinstance(error, requests.ReadTimeout):
        return "read_timeout"
    if isinstance(error, requests.ConnectionError):
        return "connection_error"
    if isinstance(error, requests.HTTPError):
        response = error.response
        if response is not None and 400 <= response.status_code < 500:
            return "http_4xx"
        return "http_5xx"
    if isinstance(error, (json.JSONDecodeError, requests.JSONDecodeError)):
        return "invalid_json"
    if isinstance(error, (KeyError, IndexError, TypeError)):
        return "invalid_schema"
    return "unknown_error"


# 第8部分：提取并校验 Chat Completions 的标准回答结构。
def extract_answer(data: dict[str, Any]) -> str:
    """从 choices[0].message.content 提取回答，结构不符时抛出异常。"""
    answer = data["choices"][0]["message"]["content"]
    if not isinstance(answer, str):
        raise TypeError("choices[0].message.content must be a string")
    return answer.strip()


def evaluate_answer(case: dict[str, Any], answer: str) -> tuple[bool, str | None]:
    """检查非空、预期文字和 JSON 内容，返回是否通过及失败类型。"""
    if not answer:
        return False, "empty_answer"

    expected = case.get("expected_contains")
    if expected is not None and str(expected) not in answer:
        return False, "content_check_failed"

    if case.get("expect_json"):
        cleaned = answer.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(lines[1:-1]) if len(lines) >= 3 else cleaned
        try:
            json.loads(cleaned)
        except json.JSONDecodeError:
            return False, "json_content_invalid"

    return True, None


# 第9部分：不依赖数据分析库，直接计算 P50、P95、P99 等延迟统计。
def percentile(values: Iterable[float], percent: float) -> float | None:
    """计算指定百分位数；没有输入数据时返回 None。"""
    ordered = sorted(values)
    if not ordered:
        return None
    index = max(0, math.ceil((percent / 100) * len(ordered)) - 1)
    return round(ordered[index], 3)


def latency_summary(values: list[float]) -> dict[str, float | int | None]:
    """返回延迟数量、平均值、P50、P95、P99 和最大值。"""
    return {
        "count": len(values),
        "average_seconds": round(sum(values) / len(values), 3) if values else None,
        "p50_seconds": percentile(values, 50),
        "p95_seconds": percentile(values, 95),
        "p99_seconds": percentile(values, 99),
        "maximum_seconds": round(max(values), 3) if values else None,
    }


# 第10部分：读取和写入 JSON、JSONL 测试数据及结果文件。
def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """逐行读取 JSONL，返回字典列表；文件不存在时返回空列表。"""
    file_path = Path(path)
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8") as file_object:
        return [json.loads(line) for line in file_object if line.strip()]


def write_json(path: str | Path, data: Any) -> None:
    """将字典或列表以易读格式写入一个 JSON 文件。"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    """将多条结果按一行一个 JSON 对象写入 JSONL 文件。"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as file_object:
        for row in rows:
            file_object.write(json.dumps(row, ensure_ascii=False) + "\n")


# 第11部分：向各测试脚本提供统一的连接超时、读取超时和计时函数。
def request_timeout(config: dict[str, Any]) -> tuple[float, float]:
    """返回 Requests 使用的连接超时和读取超时二元组。"""
    return (
        float(config["connect_timeout_seconds"]),
        float(config["read_timeout_seconds"]),
    )


def monotonic_seconds() -> float:
    """返回不受系统时钟调整影响的计时值，用于计算请求耗时。"""
    return time.perf_counter()
