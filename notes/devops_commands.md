## Install 3x-ui

```bash
git clone https://github.com/MHSanaei/3x-ui.git
cd 3x-ui
git checkout v1.7.8 #maybe later
docker compose up -d #maybe docker-compose
```

## Install docker (full)

#### Ubuntu

```bash
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

#### Debian

```bash
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

#### Install docker (quick)

> !!! Unstable !!!

```bash
bash <(curl -sSL https://get.docker.com)
# dockerd-rootless-setuptool.sh install # danger! may produce bugs
```

## Run Browsh

```bash
docker run -it browsh/browsh
```

## Create, add locally and push ssh keys

```bash
ssh-keygen -t rsa -f /home/user1/.ssh/myhost.ssh-key -q -N ''
ssh-copy-id -i /home/user1/.ssh/myhost.ssh-key.pub knopka@myhost.knopka.int
ssh-add /home/user1/.ssh/myhost.ssh-key
```

## Check commands

Checking the server IP for blocking by foreign services:
`bash <(curl -Ls IP.Check.Place) -l en`

Server parameters and speed check for Russian providers:
`wget -qO- speedtest.artydev.ru | bash`

Server parameters and speed check for foreign providers:
`wget -qO- bench.sh | bash`

Checking audio blocking on Instagram:
`bash <(curl -L -s https://bench.openode.xyz/checker_inst.sh)`