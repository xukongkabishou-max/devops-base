#!/bin/bash
set -x
kubectl create ns prod-mw-ecmas
helm upgrade --install tenant  -f ./values-prod-gpu.yaml -n prod-mw-ecmas .
kubectl apply -f myminio-console-NodePort-dev-prod.yaml -n prod-mw-ecmas
kubectl apply -f myminio-hl-NodePort-dev-prod.yaml  -n prod-mw-ecmas
