#!/bin/bash
set -x
helm upgrade --install tenant  -f ./values-dev-ecs.yaml -n dev-mw-ecmas .
kubectl apply -f myminio-console-NodePort.yaml -n dev-mw-ecmas
kubectl apply -f myminio-hl-NodePort.yaml -n dev-mw-ecmas
