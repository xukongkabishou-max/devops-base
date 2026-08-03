"""
Requests 运维与大模型接口测试综合 Demo

安装依赖：
    pip3 install requests

使用方法：
    1. 阅读下面每个函数，按实际接口修改 URL、请求头和请求体。
    2. 在文件最下方 main() 中，取消某个示例前面的注释。
    3. 执行：python3 requests_ops_demo.py

安全说明：
    - 本脚本中的域名、Token、账号和文件名全部是假数据。
    - 默认不会调用任何接口，只会打印使用说明。
    - 自动化发布、配置同步等操作可能改变服务端数据，必须先在测试环境验证。
"""

import json
import time
from pathlib import Path

import requests


# 所有请求统一使用的超时时间：连接超时 3 秒，读取超时 10 秒。
TIMEOUT = (3, 10)


def print_result(title, data):
    """统一打印字典或列表形式的结果。"""
    print(f"\n===== {title} =====")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def health_check(url):
    """健康检查：检查接口是否能连接、状态码是否正常。"""
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()

        result = {
            "healthy": True,
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type"),
        }
        print_result("健康检查", result)
        return result

    except requests.RequestException as error:
        result = {"healthy": False, "error": str(error)}
        print_result("健康检查", result)
        return result


def scheduled_patrol(url, interval=60, count=5):
    """定时巡检：按固定时间间隔重复执行健康检查。"""
    for number in range(1, count + 1):
        print(f"\n第 {number}/{count} 次巡检")
        health_check(url)

        if number < count:
            time.sleep(interval)


def send_alert(webhook_url, message):
    """告警通知：向通用 Webhook 发送 JSON 消息。"""
    payload = {
        "level": "warning",
        "message": message,
        "source": "requests-demo",
    }

    response = requests.post(webhook_url, json=payload, timeout=TIMEOUT)
    response.raise_for_status()

    print_result(
        "告警通知",
        {"sent": True, "status_code": response.status_code},
    )


def collect_api_data(url, output_file):
    """接口数据采集：获取 JSON 数据并保存到本地文件。"""
    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()

    data = response.json()
    Path(output_file).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print_result("接口数据采集", {"saved_to": output_file})
    return data


def sync_config(source_url, target_url):
    """配置同步：从源接口读取配置，再 PUT 到目标接口。"""
    source_response = requests.get(source_url, timeout=TIMEOUT)
    source_response.raise_for_status()
    config = source_response.json()

    target_response = requests.put(
        target_url,
        json=config,
        timeout=TIMEOUT,
    )
    target_response.raise_for_status()

    print_result(
        "配置同步",
        {"success": True, "status_code": target_response.status_code},
    )


def trigger_deployment(deploy_url, application, version, token):
    """自动化发布：携带 Token 调用示例发布接口。"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "application": application,
        "version": version,
        "environment": "test",
    }

    response = requests.post(
        deploy_url,
        headers=headers,
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    print_result(
        "自动化发布",
        {"triggered": True, "status_code": response.status_code},
    )


def upload_file(upload_url, file_path):
    """文件上传：使用 multipart/form-data 上传文件。"""
    path = Path(file_path)

    with path.open("rb") as file_object:
        files = {"file": (path.name, file_object)}
        response = requests.post(
            upload_url,
            files=files,
            timeout=TIMEOUT,
        )

    response.raise_for_status()
    print_result(
        "文件上传",
        {"uploaded": True, "status_code": response.status_code},
    )


def download_file(download_url, output_file):
    """文件下载：使用流式读取，避免大文件一次进入内存。"""
    with requests.get(
        download_url,
        stream=True,
        timeout=TIMEOUT,
    ) as response:
        response.raise_for_status()

        with Path(output_file).open("wb") as file_object:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file_object.write(chunk)

    print_result("文件下载", {"saved_to": output_file})


def call_third_party_api(api_url, api_token, keyword):
    """第三方 API：演示请求头、查询参数和 JSON 响应。"""
    headers = {"Authorization": f"Bearer {api_token}"}
    params = {
        "keyword": keyword,
        "page": 1,
        "page_size": 10,
    }

    response = requests.get(
        api_url,
        headers=headers,
        params=params,
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    print_result("第三方 API", data)
    return data


def test_llm_api(
    api_url,
    api_key,
    model,
    question="请只回答：1 加 1 等于多少？",
    expected_text="2",
    max_response_seconds=10,
):
    """
    测试 OpenAI 兼容的大模型接口，包括：
    1. 接口连通性检查
    2. 模型健康检查
    3. 基本问答功能验证
    4. 返回内容检查
    5. 单次响应时间检查
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": question},
        ],
        "temperature": 0,
        "max_tokens": 100,
    }

    started_at = time.perf_counter()

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=TIMEOUT,
        )
        elapsed_seconds = round(time.perf_counter() - started_at, 3)

        # 能收到 HTTP 响应，说明网络和接口地址基本连通。
        interface_connected = True
        response.raise_for_status()

        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip()

        # 有正常响应结构且回答不为空，可作为最基础的模型健康判断。
        basic_function_ok = bool(answer)
        content_check_ok = expected_text in answer
        response_time_ok = elapsed_seconds <= max_response_seconds

        report = {
            "interface_connected": interface_connected,
            "model_healthy": basic_function_ok,
            "basic_function_ok": basic_function_ok,
            "content_check_ok": content_check_ok,
            "response_time_ok": response_time_ok,
            "status_code": response.status_code,
            "response_time_seconds": elapsed_seconds,
            "question": question,
            "answer": answer,
            "expected_text": expected_text,
        }
        print_result("大模型接口测试", report)
        return report

    except (requests.RequestException, ValueError, KeyError, IndexError) as error:
        elapsed_seconds = round(time.perf_counter() - started_at, 3)
        report = {
            "interface_connected": False,
            "model_healthy": False,
            "basic_function_ok": False,
            "content_check_ok": False,
            "response_time_ok": False,
            "response_time_seconds": elapsed_seconds,
            "error": str(error),
        }
        print_result("大模型接口测试", report)
        return report


def main():
    """
    下面全部是假地址和假密钥。

    需要使用哪个功能，就取消对应代码前面的注释，并替换成测试环境信息。
    默认不执行任何网络请求。
    """

    # 1. 健康检查
    # health_check("https://service.example.com/health")

    # 2. 定时巡检：每隔 60 秒检查一次，共检查 5 次
    # scheduled_patrol(
    #     "https://service.example.com/health",
    #     interval=60,
    #     count=5,
    # )

    # 3. 告警通知
    # send_alert(
    #     "https://webhook.example.com/alert",
    #     "示例服务器 CPU 使用率超过 90%",
    # )

    # 4. 接口数据采集
    # collect_api_data(
    #     "https://service.example.com/api/status",
    #     "collected_data.json",
    # )

    # 5. 配置同步
    # sync_config(
    #     "https://source.example.com/api/config",
    #     "https://target.example.com/api/config",
    # )

    # 6. 自动化发布
    # trigger_deployment(
    #     "https://deploy.example.com/api/releases",
    #     application="demo-service",
    #     version="v1.0.0-example",
    #     token="fake-deploy-token",
    # )

    # 7. 文件上传
    # upload_file(
    #     "https://files.example.com/api/upload",
    #     "example.txt",
    # )

    # 8. 文件下载
    # download_file(
    #     "https://files.example.com/example.zip",
    #     "downloaded-example.zip",
    # )

    # 9. 调用第三方 API
    # call_third_party_api(
    #     "https://api.example.com/v1/search",
    #     api_token="fake-third-party-token",
    #     keyword="example",
    # )

    # 10. 大模型综合测试（OpenAI 兼容接口格式）
    # test_llm_api(
    #     "https://llm.example.com/v1/chat/completions",
    #     api_key="fake-llm-api-key",
    #     model="example-model",
    #     question="请只回答：1 加 1 等于多少？",
    #     expected_text="2",
    #     max_response_seconds=10,
    # )

    print(__doc__)


if __name__ == "__main__":
    main()
