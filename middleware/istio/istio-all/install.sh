#!/bin/bash
curl -L https://istio.io/downloadIstio | sh -
echo 'export PATH="$PATH:/usr/local/helm/middleware/istio/book-info/istio-1.27.1/bin"' >> ~/.bashrc
source ~/.bashrc
