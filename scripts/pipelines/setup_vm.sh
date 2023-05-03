#!/bin/bash

echo ">>>this interactive script sets up ubuntu instance"
echo ">>>requires launched instance, allowed password authentication and user password set"
echo ">>>should be run from host system"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"/../ || exit 1
echo ">>>working directory (should be 'scripts'): $(pwd)"

read -p ">>>continue? (y/n) " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ">>>setting up ssh connection"
sh setup_ssh.command

read -p ">>>enter instance ip: " -r instance_ip
read -p ">>>enter instance username: " -r instance_username

echo ">>>updating instance"
ssh "$instance_username"@"$instance_ip" "bash -s" < update.sh

echo ">>>waiting for instance to reboot (30s)"
sleep 30

echo ">>>setting up ufw"
ssh "$instance_username"@"$instance_ip" "bash -s" < setup_ufw.sh