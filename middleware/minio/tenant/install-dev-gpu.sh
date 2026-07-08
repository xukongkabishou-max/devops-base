#!/bin/bash
set -x
helm upgrade --install tenant  -f ./values-dev-gpu.yaml -n mw-ecmas .
kubectl apply -f myminio-console-NodePort.yaml -n mw-ecmas
kubectl apply -f myminio-hl-NodePort.yaml -n mw-ecmas
