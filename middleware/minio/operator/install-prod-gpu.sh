#!/bin/bash
set -x
helm upgrade --install operator  -f ./values-prod-gpu.yaml -n mw-ecmas .
