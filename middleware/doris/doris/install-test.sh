#!/bin/bash
set -x
helm upgrade --install doris  -f ./values-test.yaml -n mw-ecmas . 
