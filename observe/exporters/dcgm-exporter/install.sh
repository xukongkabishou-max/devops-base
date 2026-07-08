#!/bin/bash

set -exu

helm upgrade -i -n observe dcgm-exporter -f values.yaml .