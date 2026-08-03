#!/usr/bin/env python3
"""使用 Faker 按指定数量、长度和格式生成用户 Mock 数据。"""

import argparse
import csv
import json
from pathlib import Path

try:
    from faker import Faker
except ImportError:
    raise SystemExit("未安装 Faker，请执行：python3 -m pip install Faker")


FIELDS = [
    "id",
    "username",
    "name",
    "phone",
    "email",
    "company",
    "address",
    "age",
    "created_at",
    "description",
]


def parse_args():
    parser = argparse.ArgumentParser(description="生成用户 Mock 数据")
    parser.add_argument("-n", "--count", type=int, default=10,
                        help="生成数量，默认 10")
    parser.add_argument("-f", "--format",
                        choices=("console", "json", "csv", "sql"),
                        default="console", help="输出格式，默认 console")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--username-length", type=int, default=8,
                        help="用户名固定长度，默认 8")
    parser.add_argument("--phone-length", type=int, default=11,
                        help="手机号固定长度，默认 11")
    parser.add_argument("--text-length", type=int, default=50,
                        help="描述文本最大长度，默认 50")
    parser.add_argument("--seed", type=int, default=1603,
                        help="随机种子，默认 1603")
    parser.add_argument("--table", default="mock_users",
                        help="SQL 表名，默认 mock_users")
    return parser.parse_args()


def validate_args(args):
    if args.count < 1:
        raise SystemExit("--count 必须大于 0")
    if args.username_length < 1:
        raise SystemExit("--username-length 必须大于 0")
    if args.phone_length < 2:
        raise SystemExit("--phone-length 必须至少为 2")
    if args.text_length < 5:
        raise SystemExit("--text-length 必须至少为 5")
    if not args.table.replace("_", "").isalnum():
        raise SystemExit("--table 只能包含字母、数字和下划线")


def create_rows(fake, args):
    """按照参数生成指定数量的字典数据。"""
    rows = []

    for row_id in range(1, args.count + 1):
        # min_chars 与 max_chars 相同时，生成固定长度字符串。
        username = fake.pystr(
            min_chars=args.username_length,
            max_chars=args.username_length,
        ).lower()

        # # 会被替换为 0-9；开头固定为 1。
        phone = "1" + fake.numerify("#" * (args.phone_length - 1))

        rows.append({
            "id": row_id,
            "username": username,
            "name": fake.name(),
            "phone": phone,
            "email": fake.unique.email(),
            "company": fake.company(),
            "address": fake.address().replace("\n", " "),
            "age": fake.random_int(min=18, max=60),
            "created_at": fake.date_time_between(
                start_date="-1y", end_date="now"
            ).strftime("%Y-%m-%d %H:%M:%S"),
            # text() 保证不超过指定长度，但不保证刚好等于该长度。
            "description": fake.text(
                max_nb_chars=args.text_length
            ).replace("\n", " "),
        })

    return rows


def sql_value(value):
    """把 Python 值转换为简单的 MySQL SQL 字面量。"""
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def render_sql(rows, table):
    columns = ", ".join(f"`{field}`" for field in FIELDS)
    statements = []

    for row in rows:
        values = ", ".join(sql_value(row[field]) for field in FIELDS)
        statements.append(
            f"INSERT INTO `{table}` ({columns}) VALUES ({values});"
        )

    return "\n".join(statements) + "\n"


def write_output(rows, args):
    if args.format == "console":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    output = Path(args.output or f"mock_users.{args.format}")

    if args.format == "json":
        output.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    elif args.format == "csv":
        with output.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    elif args.format == "sql":
        output.write_text(render_sql(rows, args.table), encoding="utf-8")

    print(f"已生成 {len(rows)} 条数据：{output.resolve()}")


def main():
    args = parse_args()
    validate_args(args)

    fake = Faker("zh_CN")
    fake.seed_instance(args.seed)

    rows = create_rows(fake, args)
    write_output(rows, args)


if __name__ == "__main__":
    main()
