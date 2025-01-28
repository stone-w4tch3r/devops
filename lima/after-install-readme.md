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

# TODO

- [dev connection docs](https://www.notion.so/dodobrands/Your-workstation-software-7499e8f07fad49c4adad06ca1d5ad876#e271fe808d484c50b6332cdea18256bb)
- Find how to connect yandex without browser in ubuntu server
