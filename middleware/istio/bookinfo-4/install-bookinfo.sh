#!/bin/bash
kubectl create ns bookinfo
kubectl apply -f bookinfo.yaml -n bookinfo
