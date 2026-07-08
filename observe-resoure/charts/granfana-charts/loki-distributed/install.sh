#!/bin/bash



kubectl create ns observe 
kubectl create ns test
kubectl apply -f rules/loki-rules.yaml
helm upgrade -i -n observe loki-distributed . -f distributed-values.yaml  
kubectl apply -f test-error.yaml -n test

