#!/bin/bash
set -x
helm upgrade --install doris  -f ./values-dev.yaml -n dev-mw-ecmas .
