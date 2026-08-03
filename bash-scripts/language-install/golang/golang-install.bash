#!/usr/bin/env bash
set -euo pipefail

# 要安装并启用的 Go 版本，例如 go1.21.13、go1.22.5
GO_VERSION="${GO_VERSION:-go1.21.13}"

# Go 依赖、工具、缓存、临时文件的统一存储目录，不影响 gvm 管理的 Go 二进制位置
GO_WORKSPACE="${GO_WORKSPACE:-/data/csk/go-workspace}"

# Go 模块依赖下载源，用于 go mod download / go build
GOPROXY_URL="${GOPROXY_URL:-https://mirrors.aliyun.com/goproxy/,direct}"

# gvm 安装 Go 本体时使用的下载源
GVM_GOSRC_MIRROR="${GVM_GOSRC_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/golang/go}"

# 要写入的 shell 配置文件
BASHRC="${BASHRC:-${HOME}/.bashrc}"

# 幂等更新 ~/.bashrc 时使用的配置块标记
BASHRC_MARK_BEGIN="# >>> custom-go-workspace >>>"
BASHRC_MARK_END="# <<< custom-go-workspace <<<"

echo "==> Go version: ${GO_VERSION}"
echo "==> Go workspace: ${GO_WORKSPACE}"
echo "==> GOPROXY: ${GOPROXY_URL}"
echo "==> GVM Go source mirror: ${GVM_GOSRC_MIRROR}"

# 加载 gvm
if [ -s "${HOME}/.gvm/scripts/gvm" ]; then
  # shellcheck disable=SC1090
  source "${HOME}/.gvm/scripts/gvm"
else
  echo "ERROR: gvm not found at ${HOME}/.gvm/scripts/gvm"
  exit 1
fi

export GVM_GOSRC_MIRROR

# 安装 Go，已安装则跳过
if gvm list | grep -qE "(^|[[:space:]])${GO_VERSION}([[:space:]]|$)"; then
  echo "==> ${GO_VERSION} already installed, skip install"
else
  echo "==> Installing ${GO_VERSION}"
  gvm install "${GO_VERSION}" -B || gvm install "${GO_VERSION}" --prefer-binary
fi

# 启用 Go 版本
echo "==> Using ${GO_VERSION}"
gvm use "${GO_VERSION}" --default

# 创建依赖与缓存目录
mkdir -p \
  "${GO_WORKSPACE}/pkg/mod" \
  "${GO_WORKSPACE}/bin" \
  "${GO_WORKSPACE}/build-cache" \
  "${GO_WORKSPACE}/tmp"

# 当前 shell 立即生效，避免 gvm 默认 GOPATH 覆盖 go env -w
export GOPATH="${GO_WORKSPACE}"
export GOBIN="${GO_WORKSPACE}/bin"
export PATH="${GOBIN}:${PATH}"

# 写入 Go 配置
go env -w GO111MODULE=on
go env -w GOPROXY="${GOPROXY_URL}"
go env -w GOPATH="${GO_WORKSPACE}"
go env -w GOMODCACHE="${GO_WORKSPACE}/pkg/mod"
go env -w GOBIN="${GO_WORKSPACE}/bin"
go env -w GOCACHE="${GO_WORKSPACE}/build-cache"
go env -w GOTMPDIR="${GO_WORKSPACE}/tmp"

# 幂等更新 shell 配置文件
if grep -qF "${BASHRC_MARK_BEGIN}" "${BASHRC}" 2>/dev/null; then
  echo "==> Updating existing Go workspace block in ${BASHRC}"
  sed -i "/${BASHRC_MARK_BEGIN}/,/${BASHRC_MARK_END}/d" "${BASHRC}"
fi

cat >> "${BASHRC}" <<EOF

${BASHRC_MARK_BEGIN}
export GOPATH="${GO_WORKSPACE}"
export GOBIN="${GO_WORKSPACE}/bin"
export PATH="${GO_WORKSPACE}/bin:\$PATH"
${BASHRC_MARK_END}
EOF

# 重新加载配置
# shellcheck disable=SC1090
source "${BASHRC}"

# 验证
echo "==> Verification"
echo "go binary: $(command -v go)"
go version

echo
go env GOROOT GOPATH GOMODCACHE GOBIN GOCACHE GOTMPDIR GOPROXY