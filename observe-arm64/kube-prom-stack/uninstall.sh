#!/bin/bash


NAMESPACE=observe


helm delete -n $NAMESPACE kube-prom-stack


crds=(
alertmanagerconfigs
alertmanagers
podmonitors
probes
prometheusagents
prometheuses
prometheusrules
scrapeconfigs
servicemonitors
thanosrulers
)

for ccrd in ${crds[@]}; do
    # echo ${ccrd}.monitoring.coreos.com
    kubectl delete crd ${ccrd}.monitoring.coreos.com
done


