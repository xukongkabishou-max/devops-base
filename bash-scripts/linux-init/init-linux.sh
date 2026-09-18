#!/usr/bin/env bash
#===============================================================================
# init-linux.sh - Linux 服务器初始化总控脚本
#
# 包含模块:
#   apt-tsinghua    05-set-apt-tsinghua.sh   系统源直接 set 为清华源(写死)
#   timezone        01-set-timezone.sh       设置时区为中国上海
#   trashbox        02-setup-trashbox.sh     垃圾箱 + 禁删系统目录 + 自动清理
#   k8s-completion  03-k8s-completion.sh     K8S kubectl 命令补全
#   k8s-kdebug      04-k8s-kdebug.sh         K8S Pod 调试工具 kdebug
#
# 清华源策略(所有 apt 安装统一遵守):
#   不做备份/恢复; 不管系统原来是什么源, 一律直接 set 覆盖为清华源(镜像地址写死)。
#
# 用法:
#   bash init-linux.sh                          # 执行所有启用模块(默认全开)
#   bash init-linux.sh --only timezone,trashbox # 只执行指定模块
#   bash init-linux.sh --skip k8s-completion    # 跳过指定模块
#
# 模块开关在下方"模块开关"区域维护, 后续新增模块在此注册即可。
#===============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

#------------------------------- 模块开关 -------------------------------------
# 1=启用 0=禁用, 默认全部开启; 也可用 --only/--skip 临时覆盖
ENABLE_APT_TSINGHUA=1
ENABLE_TIMEZONE=1
ENABLE_TRASHBOX=1
ENABLE_K8S_COMPLETION=1
ENABLE_K8S_KDEBUG=1
#------------------------------------------------------------------------------

# 模块注册表: 模块名 -> 脚本文件
declare -A MODULES=(
  [apt-tsinghua]="05-set-apt-tsinghua.sh"
  [timezone]="01-set-timezone.sh"
  [trashbox]="02-setup-trashbox.sh"
  [k8s-completion]="03-k8s-completion.sh"
  [k8s-kdebug]="04-k8s-kdebug.sh"
)
# 执行顺序: 先固定系统源, 再做其余初始化
ORDER=(apt-tsinghua timezone trashbox k8s-completion k8s-kdebug)

ONLY=""
SKIP=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --only) ONLY="${2:-}"; shift 2 ;;
    --skip) SKIP="${2:-}"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "未知参数: $1 (可用 --only <模块列表> / --skip <模块列表>)" >&2; exit 1 ;;
  esac
done

# 判断模块是否启用: 仅过滤(优先) -> 跳过过滤 -> 总控开关
enabled() {
  local name="$1"
  if [[ -n "$ONLY" ]]; then
    [[ ",${ONLY// /}," == *",${name},"* ]] || return 1
  fi
  if [[ -n "$SKIP" ]]; then
    [[ ",${SKIP// /}," == *",${name},"* ]] && return 1
  fi
  case "$name" in
    apt-tsinghua)   [[ "$ENABLE_APT_TSINGHUA" == "1" ]] ;;
    timezone)       [[ "$ENABLE_TIMEZONE" == "1" ]] ;;
    trashbox)       [[ "$ENABLE_TRASHBOX" == "1" ]] ;;
    k8s-completion) [[ "$ENABLE_K8S_COMPLETION" == "1" ]] ;;
    k8s-kdebug)     [[ "$ENABLE_K8S_KDEBUG" == "1" ]] ;;
    *) return 1 ;;
  esac
}

# 非 root 时自动用 sudo 重跑
if [[ $EUID -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    echo "当前非 root, 自动使用 sudo 重新执行..."
    exec sudo -E bash "$SCRIPT_DIR/init-linux.sh" "$@"
  fi
  echo "错误: 需要 root 权限执行" >&2
  exit 1
fi

echo "=============================================="
echo " Linux 初始化开始: $(date '+%F %T')"
echo "=============================================="

failed=()
for mod in "${ORDER[@]}"; do
  echo ""
  echo "▶▶▶ 模块 [$mod] 开始..."
  if enabled "$mod"; then
    if bash "$SCRIPT_DIR/${MODULES[$mod]}"; then
      echo "✔✔✔ 模块 [$mod] 完成"
    else
      echo "✘✘✘ 模块 [$mod] 失败(继续执行后续模块)" >&2
      failed+=("$mod")
    fi
  else
    echo "⏭ 跳过模块 [$mod] (未启用)"
  fi
done

echo ""
echo "=============================================="
if [[ ${#failed[@]} -eq 0 ]]; then
  echo " 全部完成 ✔  $(date '+%F %T')"
else
  echo " 完成, 但以下模块失败: ${failed[*]} ✘"
fi
echo "=============================================="
[[ ${#failed[@]} -eq 0 ]]
