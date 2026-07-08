#!/bin/bash

rule_file=(
ecmas-prod.yaml
kubernetes-cn.yaml
node-exporter-cn.yaml
)


for rf in ${rule_file[@]}; do 
    kubectl apply -n observe -f ${rf}
done
