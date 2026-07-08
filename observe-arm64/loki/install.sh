#!/bin/bash

set -ex

helm upgrade -i -n observe loki -f values.yaml -f single-binary-values.yaml .
