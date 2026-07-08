#!/bin/bash
helm upgrade -i -n istio-system istiod . -f values.yaml  --wait

