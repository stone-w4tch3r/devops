#!/bin/bash

echo ">>>this interactive script sets up remote ubuntu instance (ssh, ufw, update)"
echo ">>>requires launched instance, allowed password authentication and user password set"
echo ">>>may be run from any system"

DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd "$DIR"/../ || exit 1
echo ">>>working directory (should be 'scripts'): $(pwd)"

read -p ">>>continue? (y/n) " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ">>>connecting this machine to the remote server"
echo "enter keyname:"
read -r keyname
echo "enter username:"
read -r username
echo "enter ipaddress:"
read -r ipaddress
echo "enter password:"
read -r -s password
echo "enter passphrase:"
read -r -s passphrase

sh "$DIR"/../pipelines/setup_vm.sh "$keyname" "$username" "$ipaddress" "$password" "$passphrase"
