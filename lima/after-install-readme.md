# Настройка новой dev машины

## Подключение к VPN

...

## Подключение к кластеру

### 1. Yandex

```bash
yc init --federation-id=bpf5bcsir6n5qu0acpru

yc managed-kubernetes cluster get-credentials --id catf9nipallfltblhjo2 --external
kubectl config use-context yc-d-kube
```

