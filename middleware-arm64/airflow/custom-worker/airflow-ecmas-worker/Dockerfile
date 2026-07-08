FROM harbor.aliyun.com/middleware/apache/airflow:2.9.1

COPY . .

USER root
RUN apt update && apt install -y gcc
RUN pip3 install -r requirement.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
