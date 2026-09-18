#!/usr/bin/env bash
#===============================================================================
# 02-setup-trashbox.sh - 全局垃圾箱
#   1. 安装 trash-cli (apt 安装前直接 set 清华源, 不做恢复)
#   2. 创建全局回收站 /data/trashbox (所有用户共用)
#   3. /etc/profile.d/trash.sh: 共享回收站环境(trash-list 等工具使用)
#   4. /usr/local/bin/rm 包装器: 任何用户/任何会话统一保护+回收站(旁路 /usr/bin/rm)
#   4. /usr/local/bin/clean-trashbox.sh + cron 每周日凌晨自动清空
#   7. /etc/bash.bashrc 挂钩: su/图形终端等非登录交互 shell 补全同样生效
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

echo "== 2. 创建全局回收站根目录 $TRASH_ROOT =="
# 根目录 1777: 任意用户首次删除时可在其下创建自己的 <用户>/Trash (trash-cli 要求属主=本人)
mkdir -p "$TRASH_ROOT"
chmod 1777 "$TRASH_ROOT"

echo "== 3. 写入 /etc/profile.d/trash.sh (回收站环境变量, 供 trash-list 等工具使用) =="
tee /etc/profile.d/trash.sh > /dev/null <<'EOF'
# 全局回收站环境(按用户隔离: /data/trashbox/<用户>/Trash)
# trash-cli 要求回收站属主=当前用户, 故按用户分目录; rm 保护由 /usr/local/bin/rm 包装器保证
[ -n "${_TRASH_SH_LOADED:-}" ] && return 0
_TRASH_SH_LOADED=1
_trash_user="$(id -un 2>/dev/null || echo unknown)"
export XDG_DATA_HOME="/data/trashbox/$_trash_user"
EOF

echo "== 4. 安装全局 rm 包装器 /usr/local/bin/rm (任何用户/任何会话生效) =="
tee /usr/local/bin/rm > /dev/null <<'EOF'
#!/bin/bash
# 全局安全 rm: 禁止删除系统关键目录, 其余一律移入回收站(/data/trashbox)
# 生效范围: 所有用户/所有会话(SSH/su/sudo/脚本/任意 shell, PATH 含 /usr/local/bin 即生效)
# 旁路方式: 使用 /usr/bin/rm, 或 export TRASHBOX_DISABLE=1
# 安全兜底: trash-cli 缺失时自动退回真实 rm

trash_user="$(id -un 2>/dev/null || echo unknown)"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/data/trashbox/$trash_user}"
mkdir -p "$XDG_DATA_HOME" 2>/dev/null || true

if [ -n "${TRASHBOX_DISABLE:-}" ] || ! command -v trash-put >/dev/null 2>&1; then
  exec /usr/bin/rm "$@"
fi

# 解析非选项参数(跳过 - 开头的选项)
args=()
for arg in "$@"; do
  case "$arg" in -*) ;; *) args+=("$arg") ;; esac
done

# 无有效参数: 交给真实 rm 输出 usage
if [ ${#args[@]} -eq 0 ]; then
  exec /usr/bin/rm "$@"
fi

# 受保护目录(精确匹配绝对真实路径)
protected_paths="/ /etc /root /home /proc /usr /usr/local /bin /sbin /boot /dev /run /var /lib /lib64 /opt /srv /tmp /data"

for target in "${args[@]}"; do
  abs_path=$(realpath -- "$target" 2>/dev/null)
  if [ -z "$abs_path" ]; then
    if [ -e "$target" ] || [ -L "$target" ]; then
      abs_path=$(cd "$(dirname "$target")" && pwd -P)/$(basename "$target")
    else
      continue
    fi
  fi
  abs_path="${abs_path%/}"
  [ -z "$abs_path" ] && abs_path="/"
  for p in $protected_paths; do
    if [ "$abs_path" = "$p" ]; then
      echo "rm: 禁止删除系统关键目录: $abs_path (旁路请用 /usr/bin/rm)" >&2
      exit 1
    fi
  done
done

trash-put "${args[@]}"
EOF
chmod 755 /usr/local/bin/rm
echo "== 5. 写入清理脚本 /usr/local/bin/clean-trashbox.sh =="
tee /usr/local/bin/clean-trashbox.sh > /dev/null <<'EOF'
#!/bin/bash
# 清空全局回收站: /data/trashbox/<用户>/Trash (按用户隔离, 全部清空)
shopt -s nullglob
for d in /data/trashbox/*/Trash; do
  [ -d "$d/files" ] && find "$d/files" -mindepth 1 -delete 2>/dev/null || true
  [ -d "$d/info" ] && find "$d/info" -mindepth 1 -delete 2>/dev/null || true
done
# 兼容旧版单一共享结构
for sub in files info; do
  [ -d "/data/trashbox/Trash/$sub" ] && find "/data/trashbox/Trash/$sub" -mindepth 1 -delete 2>/dev/null || true
done
EOF
chmod +x /usr/local/bin/clean-trashbox.sh

echo "== 6. 配置 cron: 每周日凌晨 00:00 自动清空 =="
echo "0 0 * * 0 root /usr/local/bin/clean-trashbox.sh" > /etc/cron.d/clean-trashbox
chmod 644 /etc/cron.d/clean-trashbox
systemctl enable --now cron >/dev/null 2>&1 || service cron start >/dev/null 2>&1 || true

echo "== 7. 写入 /etc/bash.bashrc 挂钩(非登录交互 shell 补全加载) =="
if ! grep -q 'trashbox-hooks' /etc/bash.bashrc 2>/dev/null; then
  tee -a /etc/bash.bashrc > /dev/null <<'EOF'

# >>> trashbox-hooks: 非登录交互 shell 也加载 rm 保护与 K8S 补全 >>>
if [ -f /etc/profile.d/trash.sh ]; then
  . /etc/profile.d/trash.sh
fi
if [ -f /etc/profile.d/kubectl-alias.sh ]; then
  . /etc/profile.d/kubectl-alias.sh
fi
if [ -f /etc/bash_completion.d/kdebug ] && ! declare -F _kdebug >/dev/null 2>&1; then
  . /etc/bash_completion.d/kdebug
fi
# <<< trashbox-hooks <<<
EOF
fi

echo "== 8. 停用用户 rc 文件中的旧版 rm 函数(统一走包装器) =="
for rc in /root/.bashrc /home/*/.bashrc; do
  [ -f "$rc" ] || continue
  grep -q 'trashbox-hooks-unset-v2' "$rc" 2>/dev/null && continue
  tee -a "$rc" > /dev/null <<'EOF'

# >>> trashbox-hooks-unset-v2: 停用旧版 rm 函数并统一回收站环境, rm 走 /usr/local/bin/rm 包装器 >>>
declare -F rm >/dev/null 2>&1 && unset -f rm
_trash_user="$(id -un 2>/dev/null || echo unknown)"
export XDG_DATA_HOME="/data/trashbox/$_trash_user"
# <<< trashbox-hooks-unset-v2 <<<
EOF
done

echo "== 完成 =="
echo "  回收站目录 : $TRASH_ROOT"
echo "  全局 rm    : /usr/local/bin/rm (任何用户/任何会话生效; 旁路: /usr/bin/rm)"
echo "  回收站环境 : /etc/profile.d/trash.sh + /etc/bash.bashrc 挂钩"
echo "  自动清理   : 每周周日 00:00 (/etc/cron.d/clean-trashbox)"
