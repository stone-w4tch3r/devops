#!/bin/bash

echo ">>>this script is used to launch wireguard client"
echo ">>>should be run from target system"

if [ -z "$2" ]; then
    echo "usage $0 <wireguard config name> <wireguard config text>"
    exit 1
fi

wg_config_name=$1
wg_config_text=$2

echo ">>>installing wireguard"
sudo apt-get install wireguard -y
sudo apt-get install wireguard-tools -y

echo ">>>installing config"
echo "$wg_config_text" | sudo tee /etc/wireguard/"$wg_config_name".conf

echo ">>>installing resolvconf (dependancy)"
sudo apt-get install resolvconf -y

echo ">>>starting wireguard"
sudo wg-quick up "$wg_config_name"

