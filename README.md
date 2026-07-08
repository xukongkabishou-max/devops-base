各个服务使用的部署使用的部署物料，包括 Helm Chart, K8S Yaml(由Helm Chart生成), SQL语句, Shell 脚本等

## app
各个服务使用的helm chart 文件

需要将  应用与需要GPU资源的应用调度到不同节点，需要为k8s节点添加污点
```bash
# 为运行模型服务/RAG服务的 GPU 节点添加污点与标签
kubectl taint node gpu-worker-1 gpu="":NoExecute
kubectl label node gpu-worker-1 gpu=""

# 为运行app应用的节点(一般为CPU节点)添加污点与标签
kubectl taint node worker-1 app="":NoExecute
kubectl label node worker-1 app=""
```

### 运行服务
每个服务(目录)下都有一个 `install.sh` 和  `uninstall.sh` 文件，可以使用该文件进行更新
> `install.sh` 和 `uninstall.sh` 文件通过 `app/gen-install-script.sh` 文件自动生成，如果需要修改命名空间等信息，可以通过修改 `app/gen-install-script.sh` 文件然后执行该脚本来修改。


## app-yaml
基于`app`下的 helm Chart 使用`helm2yaml-generator.sh`生成的纯K8S Yaml文件

## manifests
各应用使用的 SQL 等文件

## middleware
中间件
```bash
kubectl create ns mw-ecmas
```

## ingress
各个环境使用到的 ingress 文件


## k8s-plugins
安装 K8S 之后在 K8S 中安装对应的插件


## manifests
一些服务的配置文件、sql


## middleware
使用的开源中间件的 helm chart 文件


## middleware-arm64
使用的开源中间件的 helm chart 文件，arm64 架构


## middleware-docker
使用docker运行的中间件的运行脚本


## observe
监控组件的 Chart 以及 Grafana dashboard


## observe-arm64
监控组件的 Chart 以及 Grafana dashboard，arm64 架构


## services
自定义 service 文件
