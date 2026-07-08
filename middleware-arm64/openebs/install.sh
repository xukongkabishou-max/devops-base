#!/bin/bash

set -ex

helm upgrade -i -n kube-system -f values.yaml openebs .
