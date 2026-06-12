# Helm Charts

* https://docs.vllm.ai/en/v0.20.0/examples/online_serving/chart-helm/

Source https://github.com/vllm-project/vllm/tree/main/examples/online_serving/chart-helm.

This directory contains a Helm chart for deploying the vllm application. The chart includes configurations for deployment, autoscaling, resource management, and more.
此目录包含用于部署 vllm 应用程序的 Helm Chart. 该 Chart 包含部署、自动扩缩容、资源管理等方面的配置.

## Files

- Chart.yaml: Defines the chart metadata including name, version, and maintainers.
  Chart.yaml: 定义 chart 元数据, 包括名称、版本和维护者.

- ct.yaml: Configuration for chart testing.
  ct.yaml: chart 测试的配置.

- lintconf.yaml: Linting rules for YAML files.
  lintconf.yaml: YAML 文件的 Linting 规则.

- values.schema.json: JSON schema for validating values.yaml.
  values.schema.json: 用于验证 values.yaml 的 JSON 模式.

- values.yaml: Default values for the Helm chart.
  values.yaml: Helm chart 的默认值.

- templates/_helpers.tpl: Helper templates for defining common configurations.
  templates/_helpers.tpl: 用于定义通用配置的辅助模板.

- templates/configmap.yaml: Template for creating ConfigMaps.
  templates/configmap.yaml: 用于创建 ConfigMap 的模板.

- templates/custom-objects.yaml: Template for custom Kubernetes objects.
  templates/custom-objects.yaml: 自定义 Kubernetes 对象的模板.

- templates/deployment.yaml: Template for creating Deployments.
  templates/deployment.yaml: 用于创建 Deployment 的模板.

- templates/hpa.yaml: Template for Horizontal Pod Autoscaler.
  templates/hpa.yaml: 水平 Pod 自动扩缩器的模板.

- templates/job.yaml: Template for Kubernetes Jobs.
  templates/job.yaml: Kubernetes Job 模板.

- templates/poddisruptionbudget.yaml: Template for Pod Disruption Budget.

- templates/pvc.yaml: Template for Persistent Volume Claims.
  templates/pvc.yaml: 持久卷声明模板.

- templates/secrets.yaml: Template for Kubernetes Secrets.
  templates/secrets.yaml: Kubernetes Secrets 模板.

- templates/service.yaml: Template for creating Services.
  templates/service.yaml: 用于创建服务的模板.

## Running Tests
运行测试

This chart includes unit tests using [helm-unittest](https://github.com/helm-unittest/helm-unittest). Install the plugin and run tests:
此 chart 包含使用 [helm-unittest](https://github.com/helm-unittest/helm-unittest) 的单元测试. 安装插件并运行测试:

```bash
# Install plugin
helm plugin install https://github.com/helm-unittest/helm-unittest

# Run tests
helm unittest .
```

## Example materials
示例材料
