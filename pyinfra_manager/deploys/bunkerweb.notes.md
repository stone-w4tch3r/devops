# Bunkerweb

### Overview

- firewall & reverse proxy for web apps, based on nginx
- used as a set of docker containers
- ipv6 disabled by default
- supports being behind a reverse proxy/load balancer (configuration required)
- supports self-signed certificates
- configurable both via web interface and during deployment
- extensible via plugins

[online settings generator](https://config.bunkerweb.io/v1.5.3)

### Installation (integration in their terms)

>Better to use `autoconf` method, which is based on `docker`
>`autoconf` allows to keep service-based settings as container's labels

Bunkerweb consists of several containers:
- `bunkerweb` - a reverse proxy ?
- `scheduler` - main container, which is responsible for managing other containers
- `docker-proxy` - manages access to docker daemon
- `database` - mysql/mariadb/... database

### Main settings

- `MULTISITE` - multiple sites
- `SERVER_NAME` - list of served web services
- `USE_ANTIBOT` - antibot detection and captcha-like challenges
- `AUTO_LETS_ENCRYPT` - letsencrypt automation
- `USE_BAD_BEHAVIOR` - bad behavior detection (by http headers)
- `USE_BLACKLIST`/`USE_WHITELIST`/`USE_GRAYLIST` - manage access and checks by rules
- `USE_REVERSE_SCAN` - detect proxies/servers by open ports
- `USE_BUNKERNET` - third-party scanning service
- `USE_DNSBL` - dns blacklists (list of malicious ip addresses)
- `USE_LIMIT_CONN` - limit connections per client
- `USE_AUTH_BASIC` - require http basic auth
- `REVERSE_PROXY_AUTH_REQUEST` - complex auth via third-party service

### Useful plugins

- `ClamAV` - scans files for viruses
- `WebHook` - sends notifications to HTTP endpoints