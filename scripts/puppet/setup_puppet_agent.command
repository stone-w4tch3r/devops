#!/bin/bash

echo ">>>this is an interactive script that sets up puppet agent on the target system"
echo ">>>dependencies: macos, bolt"

read -rp "Enter target ip address: " server_ip

read -rp "Enter target username: " username

read -rp "Enter target password: " -s password

read -rp "Enter puppetserver ip address: " agent_ip

bolt script run setup_puppet_agent.sh "$agent_ip" --targets "$server_ip" --user "$username" --password "$password"