#!/bin/bash

echo ">>>this interactive script sets up ubuntu instance"
echo ">>>requires launched instance, allowed password authentication and user password set"
echo ">>>should be run from host system"

if [ $# -ne 5 ]; then
    echo "Usage: $0 keyname username ipaddress password passphrase"
    exit 1
fi

keyname=$1
username=$2
ipaddress=$3
password=$4
passphrase=$5

echo ">>>setting up ssh connection"
sh "$(dirname "$0")"/../setup_ssh.sh "$keyname" "$username" "$ipaddress" "$password" "$passphrase"

echo ">>>updating instance"
ssh "$username"@"$ipaddress" "bash -s" < update.sh

echo ">>>waiting for instance to reboot (30s)"
sleep 30

echo ">>>setting up ufw"
ssh "$username"@"$ipaddress" "bash -s" < setup_ufw.sh