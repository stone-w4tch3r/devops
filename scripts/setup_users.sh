#!/bin/bash

echo ">>>this script creates new sudo user and changes root password. should be run within target system"

if [ $# -ne 3 ]; then
  echo "Usage: $0 new_username new_password new_root_password"
  exit 1
fi

new_username=$1
new_password=$2
new_root_password=$3
echo ">>>setting up users and passwords"

echo ">>>changing root password"
echo "root:$new_root_password" | sudo chpasswd

echo ">>>adding user"
sudo useradd "$new_username"
echo "$new_username:$new_password" | sudo chpasswd

echo ">>>creating docker group"
sudo groupadd docker

echo ">>>adding user to sudo and docker group"
#-aG means append to group
sudo usermod -aG sudo "$new_username"
sudo usermod -aG docker "$new_username"
