#!/bin/bash
set -x
helm upgrade --install operator  -f ./values-dev-ecs.yaml -n dev-mw-ecmas .
