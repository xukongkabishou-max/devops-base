#!/bin/bash
kubectl create ns argo-rollouts
helm upgrade -i -n argo-rollouts argo-rollouts . -f values.yaml
