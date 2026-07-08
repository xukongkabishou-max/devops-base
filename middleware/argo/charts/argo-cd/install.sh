#!/bin/bash
kubectl create ns argo-cd
helm upgrade -i -n argo-cd argo-cd . -f values.yaml
