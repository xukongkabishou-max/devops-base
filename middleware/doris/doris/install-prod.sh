#!/bin/bash
set -x
helm upgrade --install doris  -f ./values-prod.yaml -n mw-ecmas .
