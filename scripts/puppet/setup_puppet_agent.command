#!/bin/bash

echo ">>>this is an interactive script that sets up puppet agent on the target system"
echo ">>>dependencies: macos, bolt"

read -rp "Enter target agent ip address: " agent_ip
read -rp "Enter target agent username: " agent_username
read -rp "Enter puppetserver ip address: " server_ip

ssh "$agent_username"@"$agent_ip" 'bash -s' < setup_puppet_agent.sh "$server_ip"