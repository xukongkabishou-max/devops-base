# Helm
# 安装步骤
````
export VERSION=2.3.9
helm pull oci://registry-1.docker.io/apache/seatunnel-helm --version ${VERSION}
tar -xvf seatunnel-helm-${VERSION}.tgz
ls
cd seatunnel-helm/
````
修改values.yaml：
````
 image:
   registry: "swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/apache/seatunnel"
   tag: ""
   pullPolicy: "IfNotPresent"
   pullSecret: "
````
修改conf/log4j2.properties,添加如下内容
````
rootLogger.appenderRef.file.ref = routingAppender
appender.file.layout.pattern = %d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%-30.30c{1.}] [%t] - %m%n

````