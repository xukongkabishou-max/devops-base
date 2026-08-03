"""执行低并发长时间稳定性测试，识别错误累积和响应延迟退化。"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from typing import Any

from common import (
    DATA_DIR,
    RESULTS_DIR,
    build_chat_payload,
    build_url,
    classify_exception,
    create_session,
    ensure_runtime_dirs,
    evaluate_answer,
    extract_answer,
    latency_summary,
    load_config,
    monotonic_seconds,
    read_jsonl,
    request_timeout,
    write_json,
    write_jsonl,
)


# 第1部分：从公共题库中选择一道题，执行一次可追踪的模型请求。
def run_once(session, config: dict[str, Any], case: dict[str, Any], sequence: int):
    """执行一次长稳请求，返回带序号、时间、耗时和错误类型的结果。"""
    result = {
        "sequence": sequence,
        "case_id": case["case_id"],
        "category": case["category"],
        "length_bucket": case["length_bucket"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "passed": False,
        "error_type": None,
        "error_message": None,
    }
    started = monotonic_seconds()

    try:
        response = session.post(
            build_url(config["base_url"], config["chat_endpoint"]),
            json=build_chat_payload(config, case),
            timeout=request_timeout(config),
        )
        result["latency_seconds"] = round(monotonic_seconds() - started, 3)
        result["status_code"] = response.status_code
        response.raise_for_status()
        data = response.json()
        answer = extract_answer(data)
        passed, content_error = evaluate_answer(case, answer)
        result.update(
            {
                "passed": passed,
                "error_type": content_error,
                "answer_length": len(answer),
                "usage": data.get("usage"),
            }
        )
    except Exception as error:
        result["latency_seconds"] = round(monotonic_seconds() - started, 3)
        result["error_type"] = classify_exception(error)
        result["error_message"] = str(error)
    return result


# 第2部分：比较测试前段和后段的平均延迟，判断性能是否随时间退化。
def degradation_rate(successful_results: list[dict[str, Any]]) -> float | None:
    """返回后段相对前段的平均延迟变化率；样本不足时返回 None。"""
    if len(successful_results) < 10:
        return None
    window = max(1, len(successful_results) // 5)
    early = successful_results[:window]
    late = successful_results[-window:]
    early_average = sum(item["latency_seconds"] for item in early) / len(early)
    late_average = sum(item["latency_seconds"] for item in late) / len(late)
    if early_average == 0:
        return None
    return round((late_average - early_average) / early_average, 4)


# 第3部分：统计长稳测试成功率、连续失败数、延迟分位数和错误分布。
def summarize(results: list[dict[str, Any]], elapsed_seconds: float) -> dict[str, Any]:
    """汇总长稳请求结果，返回可靠性、延迟和退化指标。"""
    successful = [item for item in results if item["passed"]]
    latencies = [float(item["latency_seconds"]) for item in results]
    error_counts: dict[str, int] = {}
    maximum_consecutive_failures = 0
    current_failures = 0

    for item in results:
        if item["passed"]:
            current_failures = 0
        else:
            current_failures += 1
            maximum_consecutive_failures = max(
                maximum_consecutive_failures, current_failures
            )
        if item.get("error_type"):
            error_counts[item["error_type"]] = error_counts.get(item["error_type"], 0) + 1

    total = len(results)
    return {
        "status": "COMPLETED",
        "elapsed_seconds": round(elapsed_seconds, 3),
        "total": total,
        "passed": len(successful),
        "failed": total - len(successful),
        "success_rate": round(len(successful) / total, 4) if total else 0,
        "maximum_consecutive_failures": maximum_consecutive_failures,
        "latency_degradation_rate": degradation_rate(successful),
        "error_counts": error_counts,
        "latency": latency_summary(latencies),
    }


# 第4部分：处理命令行参数，并循环使用同一份可复现题库直到测试时间结束。
def main() -> None:
    """持续循环请求模型，并生成 soak_details 和 soak_summary。"""
    parser = argparse.ArgumentParser(description="执行大模型接口长时间稳定性测试")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--duration-minutes", type=float)
    parser.add_argument("--interval-seconds", type=float)
    args = parser.parse_args()

    config = load_config(args.config)
    ensure_runtime_dirs()
    cases = read_jsonl(DATA_DIR / "test_cases.jsonl")
    if not cases:
        raise SystemExit("题库不存在，请先执行：python generate_cases.py")

    duration_minutes = (
        args.duration_minutes
        if args.duration_minutes is not None
        else float(config["soak"]["duration_minutes"])
    )
    interval_seconds = (
        args.interval_seconds
        if args.interval_seconds is not None
        else float(config["soak"]["interval_seconds"])
    )
    if duration_minutes <= 0 or interval_seconds < 0:
        raise SystemExit("测试时长必须大于0，请求间隔不能小于0")

    results = []
    test_started = monotonic_seconds()
    deadline = test_started + duration_minutes * 60
    sequence = 0

    with create_session(config) as session:
        while monotonic_seconds() < deadline:
            sequence += 1
            case = cases[(sequence - 1) % len(cases)]
            result = run_once(session, config, case, sequence)
            results.append(result)
            print(
                f"[{sequence}] {case['case_id']} "
                f"{'PASS' if result['passed'] else 'FAIL'} "
                f"{result['latency_seconds']}s"
            )
            if interval_seconds:
                remaining = deadline - monotonic_seconds()
                if remaining > 0:
                    time.sleep(min(interval_seconds, remaining))

    elapsed = monotonic_seconds() - test_started
    # 测试结束后一次性写出逐请求明细和整体汇总。
    details_path = RESULTS_DIR / "soak_details.jsonl"
    summary_path = RESULTS_DIR / "soak_summary.json"
    summary = summarize(results, elapsed)
    write_jsonl(details_path, results)
    write_json(summary_path, summary)
    print(f"明细：{details_path}")
    print(f"汇总：{summary_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
