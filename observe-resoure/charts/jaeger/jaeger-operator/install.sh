#!/bin/bash
helm upgrade -i -n observe jaeger . -f values.yaml
