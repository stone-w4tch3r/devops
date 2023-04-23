#!/bin/bash

echo ">>>this interactive script connects puppet agent to puppet server"
echo ">>>should be run on any system with bolt installed"
echo ">>>dependencies: bolt, ssh access to puppet server, puppet agent installed on puppet server"

read -rp "Enter puppet agent name:" agent_name
read -rp "Enter puppet server ip address:" puppetserver_ip
read -rp "Enter puppet server username:" username

bolt script run connect_puppet_agent_and_server.sh "$agent_name" "$puppetserver_ip" --targets "$puppetserver_ip" --user "$username"