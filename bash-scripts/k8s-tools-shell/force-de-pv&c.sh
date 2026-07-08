#!/bin/bash
NS="mw-ecmas"

echo "=== 强制删除命名空间 [$NS] 下的 PVC ==="
for pvc in $(kubectl get pvc -n $NS -o jsonpath='{.items[*].metadata.name}'); do
  echo "-> 删除 PVC: $pvc"
  kubectl patch pvc $pvc -n $NS -p '{"metadata":{"finalizers":null}}' --type=merge
  kubectl delete pvc $pvc -n $NS --force --grace-period=0
done

echo "=== 强制删除与 [$NS] 相关联的 PV ==="
for pv in $(kubectl get pv -o jsonpath='{.items[*].metadata.name}'); do
  ns=$(kubectl get pv $pv -o jsonpath='{.spec.claimRef.namespace}' 2>/dev/null || echo "")
  if [ "$ns" = "$NS" ]; then
    echo "-> 删除 PV: $pv"
    kubectl patch pv $pv -p '{"metadata":{"finalizers":null}}' --type=merge
    kubectl delete pv $pv --force --grace-period=0
  fi
done

echo "=== 已完成 PVC/PV 强制删除 ==="
