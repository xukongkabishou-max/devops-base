## 现有 K8S 集群中部署 KubeSphere
> https://kubesphere.io/zh/docs/v3.4/installing-on-kubernetes/introduction/overview/

> kubectl apply -f https://github.com/kubesphere/ks-installer/releases/download/v3.4.1/kubesphere-installer.yaml

> kubectl apply -f https://github.com/kubesphere/ks-installer/releases/download/v3.4.1/cluster-configuration.yaml



```bash
kubectl apply -f kubesphere-installer.yaml
kubectl apply -f cluster-configuration.yaml
```


## 多集群管理
### 代理集群
> https://kubesphere.io/zh/docs/v3.4/multicluster-management/enable-multicluster/agent-connection/


