# k8s运行使用GPU资源的Pod

> https://github.com/NVIDIA/k8s-device-plugin

通过 k8s-device-plugin 在 K8S 中运行使用 GPU 资源的服务


## 1. 安装 nvidia-container-toolkit 
> https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html


### 1.1 安装 nvidia-container-toolkit
```bash

1. 配置 apt 源
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sed -i -e '/experimental/ s/^#//g' /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update


# 2. 安装 nvidia-container-toolkit
sudo apt-get install -y nvidia-container-toolkit
```

### 1.2 配置容器运行时

```bash
nvidia-ctk runtime configure --runtime=containerd

systemctl restart containerd
```

## 2. 安装 k8s-device-plugin

### 2.1 安装 k8s-device-plugin
```bash
kubectl apply -f nvidia-device-plugin.yaml


kubectl get pods -n kube-system -l name=nvidia-device-plugin-ds

```

### 2.2 验证 Pod 使用 GPU 资源

```bash
1. 查看节点 GPU 资源
kubectl describe nodes prod-gpu-rtx4090-8-01 | grep -E "Capacity:|Allocatable:|nvidia.com/gpu:"
Capacity:
  nvidia.com/gpu:     8
Allocatable:
  nvidia.com/gpu:     8


2. 运行 GPU Pod
$ cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  restartPolicy: Never
  containers:
    - name: cuda-container
      image: nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda10.2
      resources:
        limits:
          nvidia.com/gpu: 1 # requesting 1 GPU
  tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
EOF

# 正常情况下 Pod 可以正常运行并由如下日志输出
$ kubectl logs gpu-pod
[Vector addition of 50000 elements]
Copy input data from the host memory to the CUDA device
CUDA kernel launch with 196 blocks of 256 threads
Copy output data from the CUDA device to the host memory
Test PASSED
Done

```
