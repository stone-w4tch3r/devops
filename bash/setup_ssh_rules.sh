#!/bin/bash

echo ">>>this script sets up ssh auth rules. should be run within target system"

echo ">>>disabling root login"
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/g' /etc/ssh/sshd_config

echo ">>>disabling password authentication"
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/g' /etc/ssh/sshd_config

echo ">>>restarting ssh service"
sudo systemctl restart ssh