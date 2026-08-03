cat << 'EOF' > /usr/local/bin/kdebug
#!/bin/bash

# 检查参数
if [ "$#" -lt 2 ]; then
    echo "使用方法: kdebug <namespace> <pod-name>"
    exit 1
fi

NAMESPACE=$1
POD_NAME=$2
IMAGE="swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/nicolaka/netshoot:v0.14"

# 自动获取 Pod 的第一个容器名称 (作为调试 target)
TARGET_CONTAINER=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.containers[0].name}' 2>/dev/null)

if [ -z "$TARGET_CONTAINER" ]; then
    echo "错误: 找不到 Pod $POD_NAME 或无法获取容器名。"
    exit 1
fi

echo "正在为 Pod [$POD_NAME] (容器: $TARGET_CONTAINER) 启动调试容器..."

# 执行调试命令
# 注意：这里去掉了 bash -c "sleep infinity"，直接进入交互式 zsh/bash 体验更好
kubectl debug "$POD_NAME" \
  -n "$NAMESPACE" \
  -it \
  --image="$IMAGE" \
  --target="$TARGET_CONTAINER" \
  -- bash
EOF



#useage kdebug dev-ecmas agent-5547c5ff99-rgtsj  