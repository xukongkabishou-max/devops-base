#!/bin/bash

###############################################################################
# 
#   将 app 目录下面的 helm chart 文件渲染成 yaml 文件并存放在 app-yaml 目录下
# 
###############################################################################

set -eu

function log {
    echo -e "[$(date +'%F %T')] $@"
}

# 包含 Helm Chart 的目录，这个目录下存放着多个应用的 Chart
APP_CHARTS_DIR="./app"
# 存放生成的 K8S Yaml 文件的目录
APP_PURE_YAML_DIR="./app-yaml"

# 如果不需要将某些chart目录渲染成 K8S Yaml 文件，可以将目录写到下面的数组内，使用空格分隔
EXCLUDE_APP=(app-helm-tpl xinference archive)
FIND_EXCLUDE_OPTS="$(for app in ${EXCLUDE_APP[@]}; do echo -n "! -path ${APP_CHARTS_DIR}/$app "; done)"
echo "Find exclude opts: ${FIND_EXCLUDE_OPTS}"

HELM_CHARTS=($(find ${APP_CHARTS_DIR} -mindepth 1 -maxdepth 1 -type d ${FIND_EXCLUDE_OPTS}))

for APP_CHART in ${HELM_CHARTS[@]}; do
    APP_NAME="$(echo ${APP_CHART} | awk -F'/' '{print $NF}')"
    log "*** Generate yaml for [ ${APP_NAME} ]"
    rm -rf ${APP_PURE_YAML_DIR}/${APP_NAME}
    mkdir -p ${APP_PURE_YAML_DIR}/${APP_NAME}

    # 为每个 values-xxx.yaml 生成对应的 K8S Yaml 文件，xxx 代表环境
    VALUES_FILE=($(find ${APP_CHART} -mindepth 1 -maxdepth 1 -type f -name "values-*.yaml"))
    for VALUE in ${VALUES_FILE[@]}; do
        # VALUE_ENV="$(echo ${VALUE##*/} | awk -F'[-.]' '{print $2}')"
        VALUE_ENV="$(echo ${VALUE##*/} | sed 's/^values-//;s/.yaml$//')"
        PURE_YAML_PATH="${APP_PURE_YAML_DIR}/${APP_NAME}/${APP_NAME}-${VALUE_ENV}.yaml"
        log "--- K8s manifests yaml: ${PURE_YAML_PATH}"
        helm template -n ${VALUE_ENV} ${APP_NAME} -f ${VALUE} ${APP_CHART} > ${PURE_YAML_PATH}
    done
    
    # 如果 Chart 目录下有 values.yaml 文件，也会基于这个 values.yaml 文件生成对应的 K8S Yaml 文件
    if [ -f "${APP_CHART}/values.yaml" ]; then
        PURE_YAML_PATH="${APP_PURE_YAML_DIR}/${APP_NAME}/${APP_NAME}.yaml"
        log "--- K8s manifests yaml: ${PURE_YAML_PATH}"
        helm template ${APP_NAME} -f ${APP_CHART}/values.yaml ${APP_CHART} > ${PURE_YAML_PATH}
    fi
done

echo '该目录中的文件均为使用`helm2yaml-generator.sh`脚本自动生成，非必要请勿手动修改' > ${APP_PURE_YAML_DIR}/README.md
