1-155：全局配置
156-331：报警规则设置


383-1193：alertmanager
  385: promtheusalert配置（webhook中转站）定义告警标题、配置发送到飞书机器人的webhook地址、配置发送到飞书邮箱的webhook地址  prometheusalert的账号密码 prometheusalert/prometheusalert
  557：alertmanager的告警规则、告警要发送给promtheusalert的地址
  763：访问类型
  737: nodePort


1194-1470:grafana
  1208:默认仪表盘
  1259:pod时区
  1269-1270：账号密码 admin/prom-operator
  1411:额外数据源  
      1352:
        datasources:
        enabled: true
        defaultDatasourceEnabled: true
        isDefaultDatasource: false
      1487: loki&&jaeger
        - name: Loki
        type: loki
        access: proxy
        url: http://loki-headless:3100
        isDefault: false
        editable: false
        - name: Jaeger
        type: jaeger
        url: http://jaeger-query.observe:16686
        access: proxy
        isDefault: false



1478-1556：kubeapiserver
1557-1793:kubelet
1795-1898 :kubeControllerManager
1901-1980  :coreDns
1982-2076:kubeDns
2080-2187:kubeEtcd
2189-2291:kubeScheduler
2294-2382 :kubeProxy
2386-2466 :kubestatemetrics
2470-2575 :nodeExporter


2578-3347:prometheusOperator
  3290:prometheusConfigReloader
3348-4734:prometheus
  3539: nodePort:30003
  3552: type: NodePort
4735- 4796 :additionalPodMonitors:额外要创建的pod监控
4797-5316   ：thanosruler


5318-5344:要部署的额外清单




