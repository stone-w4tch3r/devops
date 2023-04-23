#!/bin/bash

echo ">>>this is an interactive script that sets up puppet agent on the target system"
echo ">>>dependencies: macos, bolt"

#prompt for target ip address
read -rp "Enter target ip address: " ipaddress

#prompt for target username
read -rp "Enter target username: " username

#prompt for target password
read -rp "Enter target password: " -s password

#prompt for puppetserver ip address
read -rp "Enter puppetserver ip address: " server_ip

#run setup_puppet.sh on target system
bolt script run setup_puppet_agent.sh "$server_ip" --targets "$ipaddress" --user "$username" --password "$password"