#!/bin/bash
set -x
helm upgrade --install operator  -f ./values-test-gpu.yaml -n mw-ecmas .
