#!/bin/bash

echo ">>>this is an interactive script that sets up ssh on the target system"
echo ">>>dependencies: macos, bolt, security"

echo ">>>connecting this machine to the remote server"
echo "enter keyname:"
read -r keyname
echo "enter passphrase:"
read -r -s passphrase
echo "enter ipaddress:"
read -r ipaddress
echo "enter username:"
read -r username
echo "enter password:"
read -r -s password

validate

echo ">>>calling setup_ssh.sh"
sh "$(dirname "$0")"/setup_ssh.sh "$keyname" "$username" "$ipaddress" "$password" "$passphrase"