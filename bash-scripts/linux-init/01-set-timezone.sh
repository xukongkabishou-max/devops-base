#!/usr/bin/env bash
#===============================================================================
# 01-set-timezone.sh - 设置系统时区为中国上海(Asia/Shanghai, UTC+8)
#===============================================================================
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "错误: 请以 root 运行" >&2; exit 1; }

TZ_TARGET="Asia/Shanghai"

echo "== 1. 设置时区为 $TZ_TARGET =="
if command -v timedatectl >/dev/null 2>&1; then
  timedatectl set-timezone "$TZ_TARGET"
else
  # 无 systemd 时的回退方案
  ln -sf "/usr/share/zoneinfo/$TZ_TARGET" /etc/localtime
  echo "$TZ_TARGET" > /etc/timezone
fi

echo "== 2. 校验 =="
cur_tz=$(timedatectl show -p Timezone --value 2>/dev/null || readlink -f /etc/localtime)
echo "当前时区: $cur_tz"
echo "当前时间: $(date '+%F %T %Z')"

if [[ "$cur_tz" == *"$TZ_TARGET"* ]] || [[ "$cur_tz" == *Shanghai* ]]; then
  echo "✔ 时区设置成功"
else
  echo "✘ 时区设置失败" >&2
  exit 1
fi
