# 1.charts下面包含所有监控的chart包
## 1.1 charts目录
### 1.1.1 kube-prom-stack
部署了

`grafana、alertmanager、kube-state-metrics、
prom-operator、promethus\node-exporter、pushgateway、alert-center `

### 1.1.2 grafana-charts
`分布式日志收集loki-distributed`
子charts安装了收集器alloy（代替了promtail）和日志存储minio
