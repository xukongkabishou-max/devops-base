#!/bin/bash

# 将 Airflow 使用的镜像同步到自定义仓库

DEST_REGISTRY="harbor.aliyun.com"
DEST_PROJECT="middleware"

images=(
docker.io/bitnami/postgresql:16.1.0-debian-11-r15
docker.io/apache/airflow:2.9.3
quay.io/prometheus/statsd-exporter:v0.26.1
docker.io/redis:7.2-bookworm
docker.io/apache/airflow:airflow-pgbouncer-2024.01.19-1.21.0
docker.io/apache/airflow:airflow-pgbouncer-exporter-2024.06.18-0.17.0
docker.io/registry.k8s.io/git-sync/git-sync:v4.1.0
docker.io/bitnami/postgresql:16.1.0-debian-11-r15
)

for img in ${images[@]}; do
    dst_img=${img#*/}
    skopeo copy docker://${img} docker://${CUSTOM_REGISTRY}/${DEST_PROJECT}/${dst_img}
done


