#!/bin/bash

echo ">>>this interactive script sets up puppet server on target system"
echo ">>>dependencies: ssh access to target system"

read -rp "Enter puppet server ip address: " server_ip

ssh ubuntu@"$server_ip" 'bash -s' < setup_puppet_server.sh