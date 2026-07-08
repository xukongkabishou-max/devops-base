#!/bin/bash

set -ex

helm upgrade -i -n observe -f values.yaml grafana .
