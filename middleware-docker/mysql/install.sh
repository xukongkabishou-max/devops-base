#!/usr/bin/env bash
set -Eeuo pipefail
CONTAINER_NAME="mysql8"
ROOT_PASSWORD='zzxy@pszcvvb1184'
DATABASE_NAME="test"
DATA_VOLUME="mysql8-data"
SOURCE_IMAGE="docker.io/wechatpadpro/mysql:8.0"
MIRROR_IMAGE="swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/wechatpadpro/mysql:8.0"
log() {
  printf '[mysql8-install] %s\n' "$*"
}
if ! command -v docker >/dev/null 2>&1; then
  printf 'ERROR: Docker is not installed. Install and start Docker first.\n' >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  printf 'ERROR: Docker is not running or the current user cannot access it.\n' >&2
  exit 1
fi
if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  log "Container ${CONTAINER_NAME} already exists; starting it."
  docker start "$CONTAINER_NAME" >/dev/null
else
  log "Pulling MySQL 8.0 from the Dodo mirror: ${MIRROR_IMAGE}"
  docker pull "$MIRROR_IMAGE"
  docker tag "$MIRROR_IMAGE" "$SOURCE_IMAGE"
  log "Creating the MySQL container in the background."
  docker volume create "$DATA_VOLUME" >/dev/null
  docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --health-cmd="MYSQL_PWD='${ROOT_PASSWORD}' mysqladmin ping -h localhost -uroot --silent" \
    --health-interval=10s \
    --health-timeout=5s \
    --health-retries=10 \
    -p 3306:3306 \
    -e "MYSQL_ROOT_PASSWORD=${ROOT_PASSWORD}" \
    -e "MYSQL_DATABASE=${DATABASE_NAME}" \
    -e "MYSQL_USER=" \
    -e "MYSQL_PASSWORD=" \
    -v "${DATA_VOLUME}:/var/lib/mysql" \
    "$SOURCE_IMAGE" \
    --character-set-server=utf8mb4 \
    --collation-server=utf8mb4_0900_ai_ci >/dev/null
fi
log "Waiting for MySQL to become ready."
for attempt in $(seq 1 60); do
  if docker exec \
    -e "MYSQL_PWD=${ROOT_PASSWORD}" \
    "$CONTAINER_NAME" \
    mysqladmin ping -uroot --silent >/dev/null 2>&1; then
    break
  fi
  if (( attempt == 60 )); then
    printf 'ERROR: MySQL was not ready after 120 seconds. Run: docker logs %s\n' "$CONTAINER_NAME" >&2
    exit 1
  fi
  sleep 2
done
docker exec \
  -e "MYSQL_PWD=${ROOT_PASSWORD}" \
  "$CONTAINER_NAME" \
  mysql -uroot -e "CREATE DATABASE IF NOT EXISTS \`${DATABASE_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
log "Installation completed."
log "Container: ${CONTAINER_NAME}"
log "Port: 3306"
log "Root password: ${ROOT_PASSWORD}"
log "Database: ${DATABASE_NAME}"
