#!/bin/bash

set -ex

helm upgrade -i -n kube-system -f values.yaml openebs .
kubectl patch storageclass openebs-hostpath \
  -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

