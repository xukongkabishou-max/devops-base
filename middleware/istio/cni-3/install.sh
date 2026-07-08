#!/bin/bash
helm install istio-cni -n istio-system -f values.yaml . --wait
