
## 目录说明
### exporters
暂未使用。包含了监控常见的中间件的exporter。

### fluent-bit
暂未使用。收集 K8S Pod 日志。

### grafana
Grafana

### jaeger
> 安装 kube-prom-stack 时会安装 jaeger，这个目录当中的 yaml 文件只是用来验证使用 K8S 运行 jaeger。
jaeger 服务的 K8S yaml 资源，包含 jaeger 1.x 和 2.x 的。chart 目录当中的 chart 暂时未使用

### kube-prom-stack
包含 prometheus、alertmanager、pushgateway、node-exporter、kube-state-metrics、prometheusAlert、jaeger 等服务

### loki
日志

### PrometheusRules
包含使用到的 Prometheus 告警规则。目前仅包含以下告警范围：
- K8S 集群相关，包括 K8S 节点、Pod
- 服务器相关，包括服务器状态、资源使用
- ecmas 业务服务

## 安装说明
在一套新的环境安装监控服务时，需要安装的服务：
- kube-prom-stack
- grafana
- loki
- promtail

### 安装步骤
> 注意：在实际安装操作之前，需要根据情况修改 values.yaml 中的信息。重点注意 `kube-prom-stack` 服务的告警接收信息相关配置

```bash
kubectl create namespace observe

# 安装 kube-prom-stack
cd kube-prom-stack
bash install.sh

# 配置 Prometheus 告警规则
cd PrometheusRules
bash install.sh

# 安装 grafana
cd grafana 
bash install.sh

# 安装 loki、promtail
cd loki 
bash install.sh

cd promtail
bash install.sh
```





## 参考源
### 告警规则
> https://help.aliyun.com/zh/ack/ack-managed-and-ack-dedicated/user-guide/best-practices-for-configuring-alert-rules-in-prometheus
> https://samber.github.io/awesome-prometheus-alerts/


### 日志
> https://grafana.com/grafana/dashboards/15141-kubernetes-service-logs/
> 


### 基础设施
#### 节点
> https://grafana.com/grafana/dashboards/8919-node-exporter-dashboard-20240520-tensuns/

### K8S
#### K8S 集群整体监控
https://grafana.com/grafana/dashboards/13105-k8s-dashboard-cn-20240513-starsl-cn

#### Pod 监控
> 13787
> https://grafana.com/grafana/dashboards/17684-kubernetes-pod-overview


### 

### 中间件监控
#### MySQL

#### Redis

#### Kafka

#### Nacos

#### 