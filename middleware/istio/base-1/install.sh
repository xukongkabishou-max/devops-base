#!/bin/bash
kubectl create ns istio-system
helm upgrade -i -n istio-system istio-base --set defaultRevision=default . -f values.yaml

