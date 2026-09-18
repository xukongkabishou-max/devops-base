#!/usr/bin/env bash
#===============================================================================
# 03-k8s-completion.sh - K8S kubectl 命令补全(含 k 别名)
#   安装 bash-completion 前直接 set 清华源(不做恢复)
# 未安装 kubectl 时自动跳过, 安装 kubectl 后重新执行即可
#===============================================================================
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "错误: 请以 root 运行" >&2; exit 1; }

if ! command -v kubectl >/dev/null 2>&1; then
  echo "⚠️  未检测到 kubectl, 跳过命令补全安装(安装 kubectl 后重新执行本脚本)"
  exit 0
fi
echo "kubectl: $(command -v kubectl)"

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

echo "== 1. 确保 bash-completion 已安装 =="
if [ ! -f /usr/share/bash-completion/bash_completion ] && [ ! -f /etc/bash_completion ]; then
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt_use_tsinghua
    apt-get update -y
    apt-get install -y bash-completion
  else
    echo "错误: 缺少 bash-completion 且未找到 apt-get" >&2
    exit 1
  fi
fi

echo "== 2. 生成 kubectl 补全脚本 =="
mkdir -p /etc/bash_completion.d
kubectl completion bash > /etc/bash_completion.d/kubectl

echo "== 3. 写入 /etc/profile.d/kubectl-alias.sh (k 别名+补全) =="
tee /etc/profile.d/kubectl-alias.sh > /dev/null <<'EOF'
# kubectl 命令补全与 k 别名
if command -v kubectl >/dev/null 2>&1; then
  if ! declare -F __start_kubectl >/dev/null 2>&1; then
    # shellcheck disable=SC1090
    source /etc/bash_completion.d/kubectl 2>/dev/null || true
  fi
  alias k=kubectl
  complete -o default -F __start_kubectl k 2>/dev/null || true
fi
EOF

echo "== 完成 =="
echo "  kubectl 补全: /etc/bash_completion.d/kubectl"
echo "  k 别名      : /etc/profile.d/kubectl-alias.sh (重新登录后生效)"
