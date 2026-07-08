#!/bin/bash
set -x
helm upgrade --install doris  -f ./values-test-op.yaml -n test-mw-ecmas-op .
