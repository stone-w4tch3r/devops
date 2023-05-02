#!/bin/bash

echo ">>>this interactive script sets up multipass instance"
echo ">>>requires launched multipass instance, allowed password authentication and default user password set"
echo ">>>should be run from host system"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"/../ || exit 1
echo ">>>working directory: $(pwd)"

read -p ">>>continue? (y/n) " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ">>>setting up ssh connection"
sh setup_ssh.command

echo ">>>enter instance ip"
read -r instance_ip

echo ">>>updating instance"
ssh ubuntu@"$instance_ip" "bash -s" < update.sh

echo ">>>waiting for instance to reboot (30s)"
sleep 30

echo ">>>setting up ufw"
ssh ubuntu@"$instance_ip" "bash -s" < setup_ufw.sh