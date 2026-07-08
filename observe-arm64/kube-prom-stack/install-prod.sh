#!/bin/bash

set -ex

helm upgrade -i -n observe -f values-prod.yaml kube-prom-stack .


