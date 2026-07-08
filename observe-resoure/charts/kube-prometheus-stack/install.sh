#!/bin/bash
set -e

NAMESPACE=observe
RELEASE=kube-prom-stack

kubectl create ns ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install ${RELEASE} . \
  -n ${NAMESPACE} \
  -f values-explain.yaml

kubectl apply -f nginx.yaml -n ${NAMESPACE}

echo "Grafana dashboard ConfigMaps:"
kubectl -n ${NAMESPACE} get cm -l grafana_dashboard=1