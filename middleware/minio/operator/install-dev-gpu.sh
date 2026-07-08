#!/bin/bash
set -x
helm upgrade --install operator  -f ./values-dev-gpu.yaml -n mw-ecmas .
