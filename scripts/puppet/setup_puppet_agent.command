#!/bin/bash

echo ">>>this is an interactive script that sets up puppet agent on the target system"
echo ">>>dependencies: macos, bolt"

read -rp "Enter target ip address: " server_ip

read -rp "Enter puppetserver ip address: " agent_ip

ssh ubuntu@"$server_ip" 'bash -s' < setup_puppet_agent.sh "$agent_ip"