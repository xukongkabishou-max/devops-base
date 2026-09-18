#!/usr/bin/env bash
#===============================================================================
# 02-setup-trashbox.sh - 全局垃圾箱
#   1. 安装 trash-cli (apt 安装前直接 set 清华源, 不做恢复)
#   2. 创建全局回收站 /data/trashbox (所有用户共用)
#   3. /etc/profile.d/trash.sh: 自定义 rm, 禁止删除系统关键目录, 其余移入回收站
#   4. /usr/local/bin/clean-trashbox.sh + cron 每周日凌晨自动清空
# 可重复执行(幂等)
#===============================================================================
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "错误: 请以 root 运行" >&2; exit 1; }

TRASH_ROOT="/data/trashbox"

APT_LIST="/etc/apt/sources.list"
TSINGHUA_MIRROR="https://mirrors.tuna.tsinghua.edu.cn/ubuntu"   # 清华源(写死)

# 不管系统原来源是什么, 直接 set 为清华源(不做备份/恢复)
apt_use_tsinghua() {
  local codename
  codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-jammy}")"
  tee "$APT_LIST" > /dev/null <<EOF
# 清华镜像源(脚本安装时写死)
deb ${TSINGHUA_MIRROR}/ ${codename} main restricted universe multiverse
deb ${TSINGHUA_MIRROR}/ ${codename}-updates main restricted universe multiverse
deb ${TSINGHUA_MIRROR}/ ${codename}-backports main restricted universe multiverse
deb ${TSINGHUA_MIRROR}/ ${codename}-security main restricted universe multiverse
EOF
  echo "apt 源已直接 set 为清华镜像(${codename})"
}

echo "== 1. 安装 trash-cli =="
if ! command -v trash >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt_use_tsinghua
    apt-get update -y
    apt-get install -y trash-cli
  else
    echo "错误: 未找到 apt-get, 请手动安装 trash-cli" >&2
    exit 1
  fi
fi
echo "trash-cli: $(command -v trash)"

echo "== 2. 创建全局回收站目录 $TRASH_ROOT =="
mkdir -p "$TRASH_ROOT"
chmod 1777 "$TRASH_ROOT"   # 所有用户可写, 粘滞位防互删

echo "== 3. 写入 /etc/profile.d/trash.sh (安全 rm 函数) =="
tee /etc/profile.d/trash.sh > /dev/null <<'EOF'
# 全局回收站路径(所有用户共用)
export XDG_DATA_HOME=/data/trashbox

# 自定义 rm 函数: 禁止删除关键系统目录, 其余一律移入回收站
rm() {
  # 提前解析非选项参数(跳过以 - 开头的选项)
  local args=()
  local arg
  for arg in "$@"; do
    [[ "$arg" =~ ^- ]] && continue
    args+=("$arg")
  done

  # 无有效参数时, 提前退出
  if [ ${#args[@]} -eq 0 ]; then
    echo "⚠️  无删除目标, 未执行操作" >&2
    return 1
  fi

  # 受保护的顶级目录(解析为绝对真实路径)
  local protected_paths=(
    / /etc /root /home /proc /usr /usr/local /bin /sbin /boot /dev /run /var /lib /lib64 /opt /srv /tmp /data
  )
  local protected_resolved=()
  local p resolved
  for p in "${protected_paths[@]}"; do
    if [ -e "$p" ]; then
      resolved=$(realpath "$p" 2>/dev/null)
      [[ -n "$resolved" ]] && protected_resolved+=("$resolved")
    fi
  done

  # 检查每个目标是否为受保护目录
  local target abs_path
  for target in "${args[@]}"; do
    abs_path=$(realpath "$target" 2>/dev/null)
    if [ -z "$abs_path" ]; then
      # realpath 失败(如目标不存在), 尝试构造路径; 仍失败则交给 trash 处理
      if [ -e "$target" ] || [ -L "$target" ]; then
        abs_path=$(cd "$(dirname "$target")" && pwd -P)/$(basename "$target")
      else
        continue
      fi
    fi
    abs_path="${abs_path%/}"   # 去除尾部斜杠
    [ -z "$abs_path" ] && abs_path="/"   # 根目录特殊处理(全斜杠会被上一行清空)
    for p in "${protected_resolved[@]}"; do
      if [[ "$abs_path" == "$p" ]]; then
        echo "❌ 禁止删除系统关键目录: $abs_path" >&2
        return 1
      fi
    done
  done

  # 直接调用 trash, 不再询问
  trash "${args[@]}"
}
EOF

echo "== 4. 写入清理脚本 /usr/local/bin/clean-trashbox.sh =="
tee /usr/local/bin/clean-trashbox.sh > /dev/null <<'EOF'
#!/bin/bash
# 清空全局回收站(/data/trashbox/Trash)
if [ -d /data/trashbox/Trash/files ]; then
  find /data/trashbox/Trash/files -mindepth 1 -delete 2>/dev/null || true
fi
if [ -d /data/trashbox/Trash/info ]; then
  find /data/trashbox/Trash/info -mindepth 1 -delete 2>/dev/null || true
fi
EOF
chmod +x /usr/local/bin/clean-trashbox.sh

echo "== 5. 配置 cron: 每周日凌晨 00:00 自动清空 =="
echo "0 0 * * 0 root /usr/local/bin/clean-trashbox.sh" > /etc/cron.d/clean-trashbox
chmod 644 /etc/cron.d/clean-trashbox
systemctl enable --now cron >/dev/null 2>&1 || service cron start >/dev/null 2>&1 || true

echo "== 完成 =="
echo "  回收站目录 : $TRASH_ROOT"
echo "  rm 函数    : /etc/profile.d/trash.sh (重新登录后生效)"
echo "  自动清理   : 每周周日 00:00 (/etc/cron.d/clean-trashbox)"
