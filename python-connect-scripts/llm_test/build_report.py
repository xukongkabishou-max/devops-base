"""汇总功能、长稳和 Locust 测试结果，生成最终 JSON 与 Markdown 报告。"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import RESULTS_DIR, ensure_runtime_dirs, load_config, write_json


# 第1部分：读取可选结果文件；某项测试未执行时返回空值而不是直接报错。
def read_optional_json(path: Path) -> dict[str, Any] | None:
    """读取测试汇总 JSON；文件尚未生成时返回 None。"""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# 第2部分：从 Locust 统计 CSV 中读取 Aggregated 汇总行并统一单位。
def read_locust_summary(path: Path) -> dict[str, Any] | None:
    """读取 Locust 聚合统计，并返回秒为单位的统一汇总字段。"""
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8-sig", newline="") as file_object:
        rows = list(csv.DictReader(file_object))
    if not rows:
        return None

    aggregate = next(
        (row for row in rows if row.get("Name") == "Aggregated"), rows[-1]
    )

    def number(name: str, default: float = 0) -> float:
        raw = aggregate.get(name, "")
        try:
            return float(raw) if raw not in (None, "") else default
        except ValueError:
            return default

    request_count = int(number("Request Count"))
    failure_count = int(number("Failure Count"))
    success_rate = (
        round((request_count - failure_count) / request_count, 4)
        if request_count
        else 0
    )
    return {
        "status": "COMPLETED",
        "request_count": request_count,
        "failure_count": failure_count,
        "success_rate": success_rate,
        "requests_per_second": number("Requests/s"),
        "average_latency_seconds": round(number("Average Response Time") / 1000, 3),
        "p50_latency_seconds": round(number("50%") / 1000, 3),
        "p95_latency_seconds": round(number("95%") / 1000, 3),
        "p99_latency_seconds": round(number("99%") / 1000, 3),
        "maximum_latency_seconds": round(number("Max Response Time") / 1000, 3),
    }


# 第3部分：使用配置中的统一验收阈值，分别判断每一类测试是否通过。
def evaluate_functional(
    summary: dict[str, Any] | None, thresholds: dict[str, Any]
) -> dict[str, Any]:
    """依据成功率、P95、空回答和内容失败阈值判定功能测试。"""
    if summary is None:
        return {"status": "NOT_RUN", "passed": None, "reasons": []}

    total = max(1, int(summary.get("total", 0)))
    empty_rate = summary.get("empty_answer_count", 0) / total
    content_rate = summary.get("content_failure_count", 0) / total
    p95 = summary.get("latency", {}).get("p95_seconds")
    reasons = []
    if summary.get("success_rate", 0) < thresholds["minimum_success_rate"]:
        reasons.append("成功率低于阈值")
    if p95 is not None and p95 > thresholds["maximum_p95_latency_seconds"]:
        reasons.append("P95响应时间超过阈值")
    if empty_rate > thresholds["maximum_empty_answer_rate"]:
        reasons.append("空回答率超过阈值")
    if content_rate > thresholds["maximum_content_failure_rate"]:
        reasons.append("内容断言失败率超过阈值")
    return {"status": "PASS" if not reasons else "FAIL", "passed": not reasons, "reasons": reasons}


def evaluate_soak(
    summary: dict[str, Any] | None, thresholds: dict[str, Any]
) -> dict[str, Any]:
    """依据成功率、P95 和延迟退化率阈值判定长稳测试。"""
    if summary is None:
        return {"status": "NOT_RUN", "passed": None, "reasons": []}

    reasons = []
    p95 = summary.get("latency", {}).get("p95_seconds")
    degradation = summary.get("latency_degradation_rate")
    if summary.get("success_rate", 0) < thresholds["minimum_success_rate"]:
        reasons.append("长稳成功率低于阈值")
    if p95 is not None and p95 > thresholds["maximum_p95_latency_seconds"]:
        reasons.append("长稳P95响应时间超过阈值")
    if degradation is not None and degradation > thresholds["maximum_latency_degradation_rate"]:
        reasons.append("后段平均延迟退化超过阈值")
    return {"status": "PASS" if not reasons else "FAIL", "passed": not reasons, "reasons": reasons}


def evaluate_load(
    summary: dict[str, Any] | None, thresholds: dict[str, Any]
) -> dict[str, Any]:
    """依据成功率和 P95 阈值判定 Locust 并发测试。"""
    if summary is None:
        return {"status": "NOT_RUN", "passed": None, "reasons": []}

    reasons = []
    if summary.get("success_rate", 0) < thresholds["minimum_success_rate"]:
        reasons.append("并发测试成功率低于阈值")
    if summary.get("p95_latency_seconds", 0) > thresholds["maximum_p95_latency_seconds"]:
        reasons.append("并发测试P95响应时间超过阈值")
    return {"status": "PASS" if not reasons else "FAIL", "passed": not reasons, "reasons": reasons}


# 第4部分：使用同一份汇总数据生成方便人工阅读的 Markdown 报告。
def render_markdown(report: dict[str, Any]) -> str:
    """把综合报告字典转换成便于人工阅读的 Markdown 文本。"""
    functional = report["tests"]["functional"]
    soak = report["tests"]["soak"]
    load = report["tests"]["load"]

    def value(data: dict[str, Any] | None, *keys, default="-"):
        current: Any = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current if current is not None else default

    lines = [
        "# LLM API测试报告",
        "",
        f"生成时间：`{report['generated_at']}`",
        "",
        "## 综合结论",
        "",
        f"**{report['overall_status']}**",
        "",
        "| 测试类型 | 状态 | 成功率 | P95响应时间 |",
        "|---|---:|---:|---:|",
        f"| 功能测试 | {functional['evaluation']['status']} | {value(functional['summary'], 'success_rate')} | {value(functional['summary'], 'latency', 'p95_seconds')} 秒 |",
        f"| 长稳测试 | {soak['evaluation']['status']} | {value(soak['summary'], 'success_rate')} | {value(soak['summary'], 'latency', 'p95_seconds')} 秒 |",
        f"| 并发测试 | {load['evaluation']['status']} | {value(load['summary'], 'success_rate')} | {value(load['summary'], 'p95_latency_seconds')} 秒 |",
        "",
        "## 功能测试",
        "",
        f"- 总检查数：{value(functional['summary'], 'total')}",
        f"- 失败数：{value(functional['summary'], 'failed')}",
        f"- 空回答数：{value(functional['summary'], 'empty_answer_count')}",
        f"- 内容断言失败数：{value(functional['summary'], 'content_failure_count')}",
        f"- 失败原因：{', '.join(functional['evaluation']['reasons']) or '无'}",
        "",
        "## 长稳测试",
        "",
        f"- 总请求数：{value(soak['summary'], 'total')}",
        f"- 最大连续失败：{value(soak['summary'], 'maximum_consecutive_failures')}",
        f"- 延迟退化率：{value(soak['summary'], 'latency_degradation_rate')}",
        f"- 失败原因：{', '.join(soak['evaluation']['reasons']) or '无'}",
        "",
        "## Locust并发测试",
        "",
        f"- 总请求数：{value(load['summary'], 'request_count')}",
        f"- 失败数：{value(load['summary'], 'failure_count')}",
        f"- RPS：{value(load['summary'], 'requests_per_second')}",
        f"- P99响应时间：{value(load['summary'], 'p99_latency_seconds')} 秒",
        f"- 失败原因：{', '.join(load['evaluation']['reasons']) or '无'}",
        "",
        "## 说明",
        "",
        "- `tiktoken` 结果是统一估算值，不代表目标模型的精确Token数量。",
        "- 未运行的测试显示为 `NOT_RUN`，不参与综合PASS/FAIL计算。",
        "- 随机问题的非空回答验证不等于模型准确率。",
    ]
    return "\n".join(lines) + "\n"


# 第5部分：合并所有测试结果，计算综合状态，并写出两种格式的最终报告。
def main() -> None:
    """读取已有结果，生成 results/final_report.json 和 final_report.md。"""
    parser = argparse.ArgumentParser(description="生成大模型综合测试报告")
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()

    config = load_config(args.config)
    ensure_runtime_dirs()
    thresholds = config["thresholds"]
    functional = read_optional_json(RESULTS_DIR / "functional_summary.json")
    soak = read_optional_json(RESULTS_DIR / "soak_summary.json")
    load = read_locust_summary(RESULTS_DIR / "load_stats.csv")

    evaluations = {
        "functional": evaluate_functional(functional, thresholds),
        "soak": evaluate_soak(soak, thresholds),
        "load": evaluate_load(load, thresholds),
    }
    completed = [item for item in evaluations.values() if item["passed"] is not None]
    overall_status = (
        "NOT_RUN"
        if not completed
        else "PASS"
        if all(item["passed"] for item in completed)
        else "FAIL"
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "model": config["model"],
        "base_url": config["base_url"],
        "encoding_note": "tiktoken estimates only; server usage is authoritative",
        "thresholds": thresholds,
        "tests": {
            "functional": {"summary": functional, "evaluation": evaluations["functional"]},
            "soak": {"summary": soak, "evaluation": evaluations["soak"]},
            "load": {"summary": load, "evaluation": evaluations["load"]},
        },
    }

    # JSON 便于程序处理，Markdown 便于测试人员直接阅读。
    json_path = RESULTS_DIR / "final_report.json"
    markdown_path = RESULTS_DIR / "final_report.md"
    write_json(json_path, report)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"JSON报告：{json_path}")
    print(f"Markdown报告：{markdown_path}")
    print(f"综合结论：{overall_status}")


if __name__ == "__main__":
    main()
