#!/bin/bash

echo ">>>this script sets up ufw firewall"

echo ">>>enabling ufw"
sudo ufw --force enable

echo ">>>denying all incoming traffic"
sudo ufw default deny incoming

echo ">>>allowing ssh"
sudo ufw allow ssh

echo ">>>allowing puppet"
sudo ufw allow 8140

echo ">>>restaring ufw"
sudo ufw reload