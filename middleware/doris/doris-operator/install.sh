#!/bin/bash
set -x 
#kubectl apply -f ./crds.yaml  执行会有报错，yaml文件太大了，可以使用kubectl create -f https://raw.githubusercontent.com/apache/doris-operator/master/config/crd/bases/crds.yaml 代替
#kubectl create -f https://raw.githubusercontent.com/apache/doris-operator/master/config/crd/bases/crds.yaml
kubectl create ns doris
helm upgrade --install doris-operator  -f ./values.yaml -n doris . 
