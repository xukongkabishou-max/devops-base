#!/bin/sh
kubectl create ns argo-workflow
helm upgrade -i -n argo-workflow argo-workflow . -f values.yaml
kubectl -n argo-workflow create secret generic argo-workflows-secret \
  --from-literal=client-id=argo-workflows \
  --from-literal=client-secret=argo-workflows-secret
