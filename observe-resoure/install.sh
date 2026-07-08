#!/bin/bash
helm upgrade -i -n observe kube-prom-stack . -f values-explain.yaml
