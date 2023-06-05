#!/bin/bash

echo ">>>this script sets up multipass instance"
echo ">>>should be run within multipass instance"

read -p ">>>continue? (y/n) " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ">>>setting up ubuntu user password"
echo "ubuntu:ubuntu" | sudo chpasswd

echo ">>>allowing password authentication"
sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sudo systemctl restart sshd