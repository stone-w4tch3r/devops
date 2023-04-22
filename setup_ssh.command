#!/bin/bash

validate(){
  #check if ip is reachable
  if ! ping -c 1 "$ipaddress" &>/dev/null; then
    echo ">>>ipaddress is not reachable"
    exit 1
  fi
}

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
sh setup_ssh.sh "$keyname" "$username" "$ipaddress" "$password" "$passphrase"