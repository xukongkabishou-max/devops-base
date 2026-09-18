#!/usr/bin/env bash
#===============================================================================
# 04-k8s-kdebug.sh - 安装 K8S Pod 调试工具 kdebug
#   用法: kdebug <namespace> <pod-name>
#   补全: kdebug <TAB> 补全 namespace, 第2个 <TAB> 补全 pod 名(重新登录生效)
#   基于 kubectl debug + netshoot 镜像(华为云镜像仓库)
# 本脚本仅安装工具文件, 不依赖本机是否存在 kubectl
#===============================================================================
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "错误: 请以 root 运行" >&2; exit 1; }

if ! command -v kubectl >/dev/null 2>&1; then
  echo "⚠️  本机未安装 kubectl, kdebug 已安装但使用时需要 kubectl"
fi

echo "== 写入 /usr/local/bin/kdebug =="
cat << 'EOF' > /usr/local/bin/kdebug
#!/bin/bash

# 检查参数
if [ "$#" -lt 2 ]; then
    echo "使用方法: kdebug <namespace> <pod-name>"
    exit 1
fi

NAMESPACE=$1
POD_NAME=$2
IMAGE="${KDEBUG_IMAGE:-swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/nicolaka/netshoot:v0.14}"   # 可用环境变量 KDEBUG_IMAGE 覆盖

# 自动获取 Pod 的第一个容器名称(作为调试 target)
TARGET_CONTAINER=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.containers[0].name}' 2>/dev/null)

if [ -z "$TARGET_CONTAINER" ]; then
    echo "错误: 找不到 Pod $POD_NAME 或无法获取容器名。"
    exit 1
fi

echo "正在为 Pod [$POD_NAME] (容器: $TARGET_CONTAINER) 启动调试容器..."

# 执行调试命令
kubectl debug "$POD_NAME" \
    -n "$NAMESPACE" \
    -it \
    --image="$IMAGE" \
    --target="$TARGET_CONTAINER" \
    -- bash
EOF

echo "== 写入 kdebug 补全 /etc/bash_completion.d/kdebug =="
cat << 'EOF' > /etc/bash_completion.d/kdebug
# kdebug 补全: 第1个参数补全 namespace, 第2个参数补全 pod 名
_kdebug() {
  local cur ns
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  if [ "$COMP_CWORD" -eq 1 ]; then
    COMPREPLY=( $(compgen -W "$(kubectl get ns -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)" -- "$cur") )
  elif [ "$COMP_CWORD" -eq 2 ]; then
    ns="${COMP_WORDS[1]}"
    COMPREPLY=( $(compgen -W "$(kubectl get pods -n "$ns" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)" -- "$cur") )
  fi
  return 0
}
complete -F _kdebug kdebug
EOF

chmod +x /usr/local/bin/kdebug
chmod +x /etc/bash_completion.d/kdebug

echo "== 完成 =="
echo "  调试工具: /usr/local/bin/kdebug (用法: kdebug <namespace> <pod-name>)"
echo "  命令补全 : /etc/bash_completion.d/kdebug (重新登录后生效)"
