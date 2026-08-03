"""执行接口连通性、响应结构、回答内容、流式响应和错误参数测试。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any

import requests

from common import (
    DATA_DIR,
    RESULTS_DIR,
    build_chat_payload,
    build_url,
    classify_exception,
    create_session,
    ensure_runtime_dirs,
    estimate_tokens,
    evaluate_answer,
    extract_answer,
    get_encoding,
    latency_summary,
    load_config,
    monotonic_seconds,
    read_jsonl,
    request_timeout,
    write_json,
    write_jsonl,
)


# 第1部分：为每一种功能检查创建字段一致的基础结果对象。
def base_result(test_id: str, test_type: str) -> dict[str, Any]:
    """创建一条功能测试结果的公共字段，默认状态为未通过。"""
    return {
        "test_id": test_id,
        "test_type": test_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "passed": False,
        "error_type": None,
        "error_message": None,
    }


# 第2部分：在发送问题前，先验证模型列表接口能否访问并返回 JSON。
def test_models_endpoint(
    session: requests.Session, config: dict[str, Any]
) -> dict[str, Any]:
    """请求模型列表接口，返回状态码、耗时和通过状态。"""
    result = base_result("models-endpoint", "connectivity")
    started = monotonic_seconds()
    try:
        response = session.get(
            build_url(config["base_url"], config["models_endpoint"]),
            timeout=request_timeout(config),
        )
        result["latency_seconds"] = round(monotonic_seconds() - started, 3)
        result["status_code"] = response.status_code
        response.raise_for_status()
        response.json()
        result["passed"] = True
    except Exception as error:
        result["latency_seconds"] = round(monotonic_seconds() - started, 3)
        result["error_type"] = classify_exception(error)
        result["error_message"] = str(error)
    return result


# 第3部分：发送一条普通模型请求，校验 HTTP、JSON 结构和回答内容。
def test_case(
    session: requests.Session,
    config: dict[str, Any],
    case: dict[str, Any],
    encoding,
) -> dict[str, Any]:
    """执行一条普通问答测试，返回协议、内容、Token 和耗时结果。"""
    result = base_result(case["case_id"], "normal_chat")
    result.update(
        {
            "category": case["category"],
            "length_bucket": case["length_bucket"],
            "estimated_input_tokens": case["estimated_input_tokens"],
        }
    )
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
                "answer_preview": answer[:300],
                "estimated_output_tokens": estimate_tokens(answer, encoding),
                "usage": data.get("usage"),
            }
        )
    except Exception as error:
        result["latency_seconds"] = round(monotonic_seconds() - started, 3)
        result["error_type"] = classify_exception(error)
        result["error_message"] = str(error)
    return result


# 第4部分：验证 SSE 流式响应，并记录第一次收到正文内容的时间。
def test_streaming(
    session: requests.Session,
    config: dict[str, Any],
    case: dict[str, Any],
    encoding,
) -> dict[str, Any]:
    """执行一次流式测试，返回首段正文时间、总耗时和完整回答摘要。"""
    result = base_result("streaming-chat", "streaming")
    payload = build_chat_payload(config, case)
    payload["stream"] = True
    started = monotonic_seconds()
    first_content_at = None
    answer_parts: list[str] = []

    try:
        with session.post(
            build_url(config["base_url"], config["chat_endpoint"]),
            json=payload,
            timeout=request_timeout(config),
            stream=True,
        ) as response:
            result["status_code"] = response.status_code
            response.raise_for_status()

            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                line = raw_line.removeprefix("data:").strip()
                if line == "[DONE]":
                    break
                event = json.loads(line)
                content = event.get("choices", [{}])[0].get("delta", {}).get("content")
                if content:
                    if first_content_at is None:
                        first_content_at = monotonic_seconds()
                    answer_parts.append(content)

        answer = "".join(answer_parts).strip()
        result.update(
            {
                "latency_seconds": round(monotonic_seconds() - started, 3),
                "time_to_first_content_seconds": (
                    round(first_content_at - started, 3) if first_content_at else None
                ),
                "estimated_output_tokens": estimate_tokens(answer, encoding),
                "answer_preview": answer[:300],
                "passed": bool(answer),
                "error_type": None if answer else "empty_answer",
            }
        )
    except Exception as error:
        result["latency_seconds"] = round(monotonic_seconds() - started, 3)
        result["error_type"] = classify_exception(error)
        result["error_message"] = str(error)
    return result


# 第5部分：发送错误模型名和缺少参数的请求，确认服务能够正确拒绝非法请求。
def test_negative_requests(
    session: requests.Session, config: dict[str, Any]
) -> list[dict[str, Any]]:
    """执行两种非法请求，返回服务是否正确拒绝它们的结果列表。"""
    url = build_url(config["base_url"], config["chat_endpoint"])
    invalid_payloads = [
        (
            "invalid-model",
            {"model": "model-that-must-not-exist", "messages": [{"role": "user", "content": "test"}]},
        ),
        ("missing-messages", {"model": config["model"]}),
    ]
    results = []

    for test_id, payload in invalid_payloads:
        result = base_result(test_id, "negative")
        started = monotonic_seconds()
        try:
            response = session.post(url, json=payload, timeout=request_timeout(config))
            result.update(
                {
                    "latency_seconds": round(monotonic_seconds() - started, 3),
                    "status_code": response.status_code,
                    "passed": 400 <= response.status_code < 500,
                    "error_type": (
                        None if 400 <= response.status_code < 500 else "invalid_request_accepted"
                    ),
                }
            )
        except Exception as error:
            result["latency_seconds"] = round(monotonic_seconds() - started, 3)
            result["error_type"] = classify_exception(error)
            result["error_message"] = str(error)
        results.append(result)
    return results


# 第6部分：统计全部检查结果，生成逐请求明细和整体汇总。
def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """汇总功能测试成功率、错误数量和延迟分位数。"""
    total = len(results)
    passed = sum(bool(item["passed"]) for item in results)
    latencies = [
        float(item["latency_seconds"])
        for item in results
        if item.get("latency_seconds") is not None
    ]
    errors: dict[str, int] = {}
    for item in results:
        if item.get("error_type"):
            errors[item["error_type"]] = errors.get(item["error_type"], 0) + 1
    return {
        "status": "COMPLETED",
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "success_rate": round(passed / total, 4) if total else 0,
        "empty_answer_count": errors.get("empty_answer", 0),
        "content_failure_count": errors.get("content_check_failed", 0)
        + errors.get("json_content_invalid", 0),
        "error_counts": errors,
        "latency": latency_summary(latencies),
    }


# 第7部分：处理命令行参数；支持先限制题目数量进行小范围验证。
def main() -> None:
    """执行功能测试，并生成 functional_details 和 functional_summary。"""
    parser = argparse.ArgumentParser(description="执行大模型接口功能验证")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--limit", type=int, help="只运行题库前N条")
    args = parser.parse_args()

    config = load_config(args.config)
    ensure_runtime_dirs()
    cases = read_jsonl(DATA_DIR / "test_cases.jsonl")
    if not cases:
        raise SystemExit("题库不存在，请先执行：python generate_cases.py")
    if args.limit is not None:
        if args.limit <= 0:
            raise SystemExit("--limit 必须大于0")
        cases = cases[: args.limit]

    encoding = get_encoding(config)
    results: list[dict[str, Any]] = []
    with create_session(config) as session:
        results.append(test_models_endpoint(session, config))
        for index, case in enumerate(cases, start=1):
            result = test_case(session, config, case, encoding)
            results.append(result)
            print(
                f"[{index}/{len(cases)}] {case['case_id']} "
                f"{'PASS' if result['passed'] else 'FAIL'}"
            )

        if config["functional"].get("run_stream_test"):
            results.append(test_streaming(session, config, cases[0], encoding))
        if config["functional"].get("run_negative_tests"):
            results.extend(test_negative_requests(session, config))

    # 两个输出文件分别保存逐项明细和整体汇总。
    details_path = RESULTS_DIR / "functional_details.jsonl"
    summary_path = RESULTS_DIR / "functional_summary.json"
    write_jsonl(details_path, results)
    summary = summarize(results)
    write_json(summary_path, summary)
    print(f"明细：{details_path}")
    print(f"汇总：{summary_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
