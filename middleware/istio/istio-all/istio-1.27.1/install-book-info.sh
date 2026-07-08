#!/bin/bash
kubectl label namespace default istio-injection=enabled
kubectl apply -f samples/bookinfo/platform/kube/bookinfo.yaml
kubectl apply -f samples/bookinfo/gateway-api/bookinfo-gateway.yaml
kubectl apply -f samples/addons/
kubectl annotate gateway bookinfo-gateway networking.istio.io/service-type=NodePort --namespace=default
kubectl get gateway

echo "使用http://<your-node-ip>:<your-node-port>/productpage 访问"
