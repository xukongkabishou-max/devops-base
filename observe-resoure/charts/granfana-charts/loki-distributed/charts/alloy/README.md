values的31配置了收集规则以及推送到loki的地址
  
  ```yaml
alloy:
  configMap:
    create: true
    content: |-
      ################################################################
      # 1️⃣ Loki 写入器配置
      # 定义一个名为 "default" 的写入目标，所有日志最终都会发送到这里
      ################################################################
      loki.write "default" {
        endpoint {
          # Loki 分布式集群的 HTTP Push 接口
          url = "http://loki-loki-distributed-distributor.monitoring.svc.cluster.local:3100/loki/api/v1/push"
        }
      }

      ################################################################
      # 2️⃣ Kubernetes Pod 自动发现
      # 发现集群内所有 Pod，并收集元数据（namespace、pod name、container name 等）
      ################################################################
      discovery.kubernetes "pod" {
        role = "pod"
      }

      ################################################################
      # 3️⃣ 重写标签与生成日志路径
      # 将 Kubernetes 元数据转换为 Loki 标签，并生成 __path__ 供读取日志文件
      ################################################################
      discovery.relabel "pod_logs" {
        # 输入来源：上一步发现的 Pod
        targets = discovery.kubernetes.pod.targets

        # ① 将 namespace 元数据映射到 Loki 标签 namespace
        rule {
          source_labels = ["__meta_kubernetes_namespace"]
          action = "replace"
          target_label = "namespace"
        }

        # ② 将 pod 名映射到 Loki 标签 pod
        rule {
          source_labels = ["__meta_kubernetes_pod_name"]
          action = "replace"
          target_label = "pod"
        }

        # ③ 将容器名映射到 Loki 标签 container
        rule {
          source_labels = ["__meta_kubernetes_pod_container_name"]
          action = "replace"
          target_label = "container"
        }

        # ④ 将 app label 映射到 Loki 标签 app
        rule {
          source_labels = ["__meta_kubernetes_pod_label_app_kubernetes_io_name"]
          action = "replace"
          target_label = "app"
        }

        # ⑤ 生成 job 标签（namespace/container）
        rule {
          source_labels = ["__meta_kubernetes_namespace", "__meta_kubernetes_pod_container_name"]
          action = "replace"
          target_label = "job"
          separator = "/"
          replacement = "$1"  # 这里取 namespace 作为 job 的主要值
        }

        # ⑥ 生成日志文件路径 __path__，用于读取 Pod 日志
        rule {
          source_labels = ["__meta_kubernetes_pod_uid", "__meta_kubernetes_pod_container_name"]
          action = "replace"
          target_label = "__path__"
          separator = "/"
          replacement = "/var/log/pods/*$1/*.log"  # Kubernetes 容器日志路径
        }

        # ⑦ 获取容器运行时类型，例如 docker / containerd
        rule {
          source_labels = ["__meta_kubernetes_pod_container_id"]
          action = "replace"
          target_label = "container_runtime"
          regex = "^(\\S+):\\/\\/.+$"
          replacement = "$1"
        }
      }

      ################################################################
      # 4️⃣ Loki source
      # 根据 __path__ 读取 Pod 日志，生成事件流
      ################################################################
      loki.source.kubernetes "pod_logs" {
        targets    = discovery.relabel.pod_logs.output   # 上一步处理后的日志路径和标签
        forward_to = [loki.process.pod_logs.receiver]   # 发送到处理阶段
      }

      ################################################################
      # 5️⃣ Loki 处理器
      # 给日志增加静态标签，例如 cluster
      ################################################################
      loki.process "pod_logs" {
        stage.static_labels {
          values = {
            cluster = sys.env("CLUSTER"),  # 从环境变量获取集群名
          }
        }
        forward_to = [loki.write.default.receiver]  # 处理完发送给写入器
      }
