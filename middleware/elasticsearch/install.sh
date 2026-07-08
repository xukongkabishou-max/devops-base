#!/bin/bash
kubectl create secret generic elastic-certificates --from-file=elastic-certificates.p12 -n middle
kubectl apply -f secrets-apply.yaml


#helm部署
helm upgrade -i -n middle -f values.yaml elasticsearch .
