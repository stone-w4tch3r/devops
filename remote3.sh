#!/bin/bash

setup_users(){
    echo ">>>setting up users"
    cd ~
    git clone https://github.com/jasonheecs/ubuntu-server-setup.git
    cd ubuntu-server-setup
    bash setup.sh
}

setup_wg_dashboard(){
    echo ">>>setting up wireguard dashboard"
    cd ~
    git clone https://github.com/ikidd/wgdashboard-dockerized
    cd wgdashboard-dockerized
    sudo docker-compose build  
    sudo docker-compose up -d
}

setup_speedtest(){
    echo ">>>setting up speedtest"
    cd ~
    docker pull adolfintel/speedtest
    echo "Enter password for stats:"
    read statsPassword
    sudo docker run -e MODE=standalone -e TELEMETRY=true -e ENABLE_ID_OBFUSCATION=true -e PASSWORD="$statsPassword" -e WEBPORT=86 -p 86:86 -it adolfintel/speedtest
}

setup_wg_easy(){
    echo ">>>setting up wireguard easy"
    cd ~
    echo "Enter ip address:"
    read ipaddress
    echo "Enter password for admin:"
    read adminPassword
    docker run -d \
  --name=wg-easy \
  -e WG_HOST=$ipaddress \
  -e PASSWORD=$adminPassword \
  -v ~/.wg-easy:/etc/wireguard \
  -p 51920:51920/udp \
  -p 51921:51921/tcp \
  --cap-add=NET_ADMIN \
  --cap-add=SYS_MODULE \
  --sysctl="net.ipv4.conf.all.src_valid_mark=1" \
  --sysctl="net.ipv4.ip_forward=1" \
  --restart unless-stopped \
  weejewel/wg-easy
}

setup_docker(){
    echo ">>>setting up docker"
    cd ~
    sudo systemctl enable docker
}

setup_users
setup_wg_dashboard
setup_speedtest
setup_wg_easy
setup_docker