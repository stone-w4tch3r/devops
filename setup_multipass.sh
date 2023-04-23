#!/bin/bash

#this script sets up multipass instance
#should be run within multipass instance

echo ">>>setting up ubuntu user password"
echo "ubuntu:ubuntu" | sudo chpasswd

echo ">>>allowing password authentication"
sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sudo systemctl restart sshd