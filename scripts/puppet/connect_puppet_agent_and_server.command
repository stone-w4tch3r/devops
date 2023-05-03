#!/bin/bash

echo ">>>this interactive script connects puppet agent to puppet server"
echo ">>>should be run on any system with bolt installed"
echo ">>>dependencies: bolt, ssh access to puppet server, puppet installed on puppet server"

read -rp "Enter puppet agent ip address:" agent_ip
read -rp "Enter puppet agent name:" agent_name
read -rp "Enter puppet server ip address:" server_ip
read -rp "Enter puppet server username:" server_username

ssh "$server_username"@"$server_ip" 'bash -s' < connect_puppet_agent_and_server.sh "$agent_name" "$agent_ip"