#!/bin/bash
helm install \
  cert-manager oci://quay.io/jetstack/charts/cert-manager \
  --version v1.18.2 \
  --namespace kube-system \
  --create-namespace \
  --set crds.enabled=true
