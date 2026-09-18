#!/usr/bin/env bash
#===============================================================================
# 05-set-apt-tsinghua.sh - Ubuntu 系统源直接 set 为清华源(写死)
#   针对 Ubuntu 22.04 (jammy); 其他 Ubuntu 版本自动探测 codename, 失败回退 jammy
#   不做备份/恢复: 不管系统原来源是什么, 一律直接覆盖为清华源
# 可重复执行(幂等)
#===============================================================================
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "错误: 请以 root 运行" >&2; exit 1; }

APT_LIST="/etc/apt/sources.list"
TSINGHUA_MIRROR="https://mirrors.tuna.tsinghua.edu.cn/ubuntu"   # 清华源(写死)

codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-jammy}")"

echo "== 1. 系统源直接 set 为清华镜像(${codename}) =="
tee "$APT_LIST" > /dev/null <<EOF
# 清华镜像源(写死)
deb ${TSINGHUA_MIRROR}/ ${codename} main restricted universe multiverse
deb ${TSINGHUA_MIRROR}/ ${codename}-updates main restricted universe multiverse
deb ${TSINGHUA_MIRROR}/ ${codename}-backports main restricted universe multiverse
deb ${TSINGHUA_MIRROR}/ ${codename}-security main restricted universe multiverse
EOF

echo "== 2. 刷新 apt 索引 =="
apt-get update -y

echo "== 完成 =="
echo "  系统源: $APT_LIST -> 清华源(${codename})"
