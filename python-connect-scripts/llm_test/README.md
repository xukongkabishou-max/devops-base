# LLM API 通用测试框架

本框架使用 `requests`、`Faker`、`Locust` 和 `tiktoken`，对兼容 OpenAI Chat Completions 格式的大模型接口进行以下验证：

- 接口连通性和响应格式验证
- 固定答案、JSON 输出和非空回答验证
- 普通响应和流式响应验证
- 长时间稳定性验证
- 阶梯并发和突发流量验证
- 测试结果汇总及验收判定

框架中的地址、模型名称和密钥均为虚构默认值。修改配置之前，不应执行会请求模型的测试脚本。

## 一、目录中每个文件的职责

| 文件 | 是否直接执行 | 读取什么 | 执行后生成什么 |
|---|---:|---|---|
| `config.json` | 否 | 无 | 无，用于保存模型地址、模型名称、超时和验收阈值 |
| `common.py` | 否 | `config.json` | 无，向其他脚本提供公共函数 |
| `generate_cases.py` | 是 | `config.json` | `data/test_cases.jsonl` 测试题库 |
| `functional_test.py` | 是 | 配置和测试题库 | 功能测试明细及汇总文件 |
| `soak_test.py` | 是 | 配置和测试题库 | 长稳测试明细及汇总文件 |
| `locustfile.py` | 由 Locust 加载 | 配置和测试题库 | Locust 并发测试 CSV 文件 |
| `build_report.py` | 是 | 前面各项测试结果 | `final_report.json` 和 `final_report.md` |
| `requirements.txt` | 否 | 无 | 无，用于声明 Python 依赖 |

`common.py` 不是一个需要单独执行的测试程序。其他 Python 脚本通过 `import common` 使用其中的配置读取、请求构造、Token 估算、响应校验和结果写入函数。

## 二、明确的执行流程

### 第一步：修改配置

人工编辑 `config.json`，填写实际模型地址、接口路径、模型名称和鉴权信息。

这一步不会生成任何文件。

### 第二步：生成测试题库

执行：

```bash
python3 generate_cases.py
```

该脚本读取：

```text
config.json
```

该脚本生成：

```text
data/test_cases.jsonl
```

`test_cases.jsonl` 是后续三种测试共用的题库。每一行是一条 JSON 测试用例，包括问题、测试分类、预期内容和估算 Token 数。

### 第三步：执行功能测试

执行 `functional_test.py`。该脚本读取 `test_cases.jsonl`，逐条请求模型并验证状态码、JSON 结构、回答内容和响应时间。

生成：

```text
results/functional_details.jsonl
results/functional_summary.json
```

### 第四步：执行长稳测试

执行 `soak_test.py`。该脚本循环读取 `test_cases.jsonl` 中的问题，在指定时间内持续请求模型。

生成：

```text
results/soak_details.jsonl
results/soak_summary.json
```

### 第五步：执行 Locust 并发测试

Locust 加载 `locustfile.py`。该文件从 `test_cases.jsonl` 中选择问题，模拟多个用户并发请求模型。

生成：

```text
results/load_stats.csv
results/load_stats_history.csv
results/load_failures.csv
results/load_exceptions.csv
```

### 第六步：生成综合报告

执行：

```bash
python3 build_report.py
```

该脚本不请求模型。它只读取已经生成的功能测试、长稳测试和 Locust 测试结果，然后生成：

```text
results/final_report.json
results/final_report.md
```

因此，完整关系可以直接理解为：

1. `generate_cases.py` 负责出题。
2. `functional_test.py`、`soak_test.py` 和 `locustfile.py` 分别使用同一份题库完成三类测试。
3. 三类测试把结果写入 `results/`。
4. `build_report.py` 读取 `results/` 中的结果，生成最终报告。

## 三、初始目录和运行后目录

刚拿到框架时，必须存在的是：

```text
llm_test/
├── README.md
├── requirements.txt
├── config.json
├── common.py
├── generate_cases.py
├── functional_test.py
├── soak_test.py
├── locustfile.py
└── build_report.py
```

`data/` 和 `results/` 一开始可以不存在，程序会在需要时自动创建。

执行全部测试后，目录大致变为：

```text
llm_test/
├── README.md
├── requirements.txt
├── config.json
├── common.py
├── generate_cases.py
├── functional_test.py
├── soak_test.py
├── locustfile.py
├── build_report.py
├── data/
│   └── test_cases.jsonl
└── results/
    ├── functional_details.jsonl
    ├── functional_summary.json
    ├── soak_details.jsonl
    ├── soak_summary.json
    ├── load_stats.csv
    ├── load_stats_history.csv
    ├── load_failures.csv
    ├── load_exceptions.csv
    ├── final_report.json
    └── final_report.md
```

## 四、Linux 环境准备

进入框架目录：

```bash
cd /实际存放路径/llm_test
```

创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

查看 Python 版本：

```bash
python3 --version
```

建议使用 Python 3.10 或更高版本。

## 五、使用前必须修改的配置

编辑：

```bash
vim config.json
```

至少修改：

```json
{
  "base_url": "http://实际模型地址:端口",
  "chat_endpoint": "/v1/chat/completions",
  "models_endpoint": "/v1/models",
  "model": "实际模型名称",
  "api_key": "实际密钥；没有鉴权时填写空字符串"
}
```

其他重要配置：

| 配置项 | 作用 |
|---|---|
| `connect_timeout_seconds` | 建立连接允许等待的最长时间 |
| `read_timeout_seconds` | 等待模型完整响应的最长时间 |
| `default_max_output_tokens` | 默认最大输出 Token 数 |
| `dataset.case_count` | 生成多少条测试题目 |
| `soak.duration_minutes` | 长稳测试持续多少分钟 |
| `soak.interval_seconds` | 长稳测试每次请求之间等待多久 |
| `locust.stages` | 阶梯负载的持续时间、用户数和启动速率 |
| `thresholds` | 最终报告使用的验收阈值 |

`tiktoken` 在本框架中只用于统一估算文本长度和划分短、中、长请求。报告中的字段使用 `estimated_tokens`，不应当作目标模型的精确 Token 数；实际用量以接口返回的 `usage` 为准。

## 六、完整运行命令

### 1. 生成 60 条默认测试题目

```bash
python3 generate_cases.py
```

临时指定生成 120 条：

```bash
python3 generate_cases.py --count 120
```

### 2. 先执行 5 条功能测试

```bash
python3 functional_test.py --limit 5
```

确认模型接口配置正确后，执行完整功能测试：

```bash
python3 functional_test.py
```

### 3. 执行 5 分钟长稳 Demo

```bash
python3 soak_test.py --duration-minutes 5 --interval-seconds 3
```

按照 `config.json` 的正式配置执行：

```bash
python3 soak_test.py
```

### 4. 执行固定并发 Locust Demo

下面表示模拟 4 个并发用户，每秒启动 1 个用户，持续 5 分钟：

```bash
python3 -m locust \
  -f locustfile.py \
  --host http://实际模型地址:端口 \
  --headless \
  -u 4 \
  -r 1 \
  -t 5m \
  --csv results/load
```

参数含义：

| 参数 | 含义 |
|---|---|
| `-f locustfile.py` | 指定 Locust 测试文件 |
| `--host` | 临时指定模型服务地址，覆盖 `config.json` 的地址 |
| `--headless` | 不启动 Web 页面，直接在终端运行 |
| `-u 4` | 最大并发用户数为 4 |
| `-r 1` | 每秒启动 1 个用户 |
| `-t 5m` | 持续运行 5 分钟 |
| `--csv results/load` | 将结果写入以 `results/load` 开头的 CSV 文件 |

使用 `config.json` 中的阶梯负载：

```bash
python3 -m locust \
  -f locustfile.py \
  --headless \
  --csv results/load
```

### 5. 生成最终报告

```bash
python3 build_report.py
```

## 七、每类测试具体检查什么

### 功能测试

- `/v1/models` 是否可访问
- `/v1/chat/completions` 是否返回成功状态码
- 返回内容是否为合法 JSON
- 是否存在 `choices[0].message.content`
- 模型回答是否为空
- 固定答案是否包含预期内容
- 要求 JSON 输出时，回答能否再次解析为 JSON
- 普通响应是否正常
- 流式 SSE 响应是否正常
- 不存在的模型是否被拒绝
- 缺少 `messages` 参数是否被拒绝
- 单次完整响应时间
- 流式响应首次收到正文的时间
- 接口 `usage` 与 tiktoken 估算值

### 长稳测试

- 累计请求成功率
- 错误类型及出现次数
- 最大连续失败次数
- P50、P95、P99 响应时间
- 测试前 20% 和后 20% 的平均延迟变化
- 长时间运行后是否出现空回答和结构错误

### Locust 并发测试

- 短、中、长输入分别统计
- 预热、逐步增加并发、高压和恢复阶段
- 总请求数、失败数和每秒请求数
- 平均响应时间以及 P50、P95、P99
- HTTP 成功但回答为空时记为失败
- HTTP 成功但响应结构错误时记为失败
- 固定答案不符合预期时记为失败

## 八、结果文件分别表示什么

`functional_details.jsonl`：每一次功能检查的详细结果，一行代表一次检查。

`functional_summary.json`：功能测试总数、成功率、错误分类和延迟分位数。

`soak_details.jsonl`：长稳测试每一次请求的详细结果。

`soak_summary.json`：长稳成功率、连续失败数和延迟退化率。

`load_stats.csv`：Locust 汇总统计。

`load_stats_history.csv`：Locust 在测试过程中的时间序列统计。

`load_failures.csv`：Locust 记录的失败原因。

`load_exceptions.csv`：Locust 运行代码本身出现的异常。

`final_report.json`：方便其他程序继续处理的综合报告。

`final_report.md`：方便人工阅读的综合报告。

## 九、验收阈值

验收阈值用于规定“什么样的测试结果算合格”。它们不是模型启动参数，不会影响模型生成内容，只会被 `build_report.py` 用来判断最终结果是 `PASS` 还是 `FAIL`。

当前 `config.json` 中的默认配置为：

```json
"thresholds": {
  "minimum_success_rate": 0.99,
  "maximum_p95_latency_seconds": 30,
  "maximum_empty_answer_rate": 0.0,
  "maximum_content_failure_rate": 0.01,
  "maximum_latency_degradation_rate": 0.2
}
```

### 1. minimum_success_rate

最低成功率，默认值：

```json
"minimum_success_rate": 0.99
```

`0.99` 表示所有请求的成功率必须大于或等于 `99%`。

计算公式：

```text
成功率 = 成功请求数 / 总请求数
```

例如执行 1000 次请求，其中 995 次成功：

```text
995 / 1000 = 99.5%
```

`99.5%` 高于 `99%`，该项通过。如果只有 980 次成功，成功率为 `98%`，该项失败。

这里的失败不仅包括 HTTP 请求失败，也可能包括响应结构错误、空回答或固定内容断言失败。

### 2. maximum_p95_latency_seconds

允许的最大 P95 响应时间，默认值：

```json
"maximum_p95_latency_seconds": 30
```

表示至少 95% 的请求应当在 30 秒内完成。

P95 的计算方法是把所有请求耗时从小到大排列，取第 95 百分位对应的响应时间。它比平均响应时间更容易发现少量明显变慢的请求。

例如：

```text
实际P95 = 18.6秒，小于30秒，测试通过。
实际P95 = 42秒，大于30秒，测试失败。
```

大模型响应时间受输入 Token、输出 Token、GPU 数量、并发数和量化方式影响。正式阈值应根据业务 SLO 和基准测试结果设置。

### 3. maximum_empty_answer_rate

允许的最大空回答率，默认值：

```json
"maximum_empty_answer_rate": 0.0
```

`0.0` 表示不允许出现空回答。空回答是指 HTTP 请求成功、JSON 结构也存在，但模型返回的正文是空字符串，例如：

```json
{
  "choices": [
    {
      "message": {
        "content": ""
      }
    }
  ]
}
```

计算公式：

```text
空回答率 = 空回答数量 / 总测试数量
```

例如执行 100 次测试，其中出现 1 次空回答，空回答率为 `1%`。因为默认允许值是 `0%`，所以该项失败。

### 4. maximum_content_failure_rate

允许的最大内容断言失败率，默认值：

```json
"maximum_content_failure_rate": 0.01
```

`0.01` 表示最多允许 `1%` 的测试发生内容校验失败。

例如题库中定义：

```json
{
  "prompt": "请只回答：1加1等于多少？",
  "expected_contains": "2"
}
```

模型回答中包含 `2` 时，内容断言通过；回答为“我不知道”时，记录为 `content_check_failed`。要求模型返回 JSON 但回答无法解析时，记录为 `json_content_invalid`。这两种情况都会计入内容失败数量。

计算公式：

```text
内容失败率 = 内容断言失败数量 / 总测试数量
```

例如 100 次测试中有 1 次内容失败，失败率为 `1%`，没有超过默认阈值；如果有 2 次失败，失败率为 `2%`，该项失败。

### 5. maximum_latency_degradation_rate

长稳测试允许的最大延迟退化率，默认值：

```json
"maximum_latency_degradation_rate": 0.2
```

`0.2` 表示长时间运行后，后段平均响应时间相对于前段最多允许增加 `20%`。

`soak_test.py` 会取成功请求中的前 20% 和后 20%，分别计算平均响应时间：

```text
延迟退化率 =
（后段平均响应时间 - 前段平均响应时间）
/ 前段平均响应时间
```

例如：

```text
前段平均响应时间：10秒
后段平均响应时间：11秒
退化率：(11 - 10) / 10 = 10%
```

`10%` 小于允许的 `20%`，该项通过。

如果后段平均响应时间增加到 14 秒：

```text
退化率：(14 - 10) / 10 = 40%
```

`40%` 超过阈值，该项失败。持续变慢可能与请求排队、缓存压力、资源没有释放或服务内部队列积压有关。

### 6. 最终判定规则

`build_report.py` 分别判断功能测试、长稳测试和并发测试。

示例：

```text
成功率：99.8%             通过
P95响应时间：24秒         通过
空回答率：0%              通过
内容失败率：0.5%          通过
延迟退化率：12%           通过
```

所有已执行测试均满足阈值时，最终状态为：

```text
PASS
```

任意一项超过阈值时，最终状态为：

```text
FAIL
```

报告中会同时写出失败原因，例如：

```text
成功率低于阈值
并发测试P95响应时间超过阈值
后段平均延迟退化超过阈值
```

某类测试尚未执行时显示：

```text
NOT_RUN
```

`NOT_RUN` 不代表测试通过，只表示缺少对应结果文件。

以上默认值只是演示值，不代表所有模型部署都必须满足。正式测试前，应根据 GPU 数量、模型量化方式、输入长度、输出长度、目标并发以及实际业务 SLO 重新设置。

## 十、常见问题

连接失败：检查 `base_url`、端口、防火墙和模型服务监听地址。

返回 `404`：检查 `chat_endpoint` 和 `models_endpoint` 是否与实际服务一致。

返回 `401` 或 `403`：检查 `api_key` 和服务端鉴权配置。

返回结构错误：确认服务是否真正兼容 `choices[0].message.content`。

大量读取超时：先降低 Locust 并发数、输入长度和 `max_tokens`，再检查模型服务排队情况。

Token 估算与 `usage` 不一致：这是正常情况。本框架的 `tiktoken` 结果用于统一比较，实际 Token 用量以服务端返回值为准。

随机问题回答不为空，不代表回答一定正确。需要验证业务准确率时，应在 `generate_cases.py` 的固定题目中增加明确的 `expected_contains`。
