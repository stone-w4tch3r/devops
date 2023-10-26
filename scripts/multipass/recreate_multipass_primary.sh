#!/bin/bash

sudo echo ">>>this is a script that recreates the multipass instance and sets /etc/hosts"

version='jammy'
if [ "$1" != '' ]; then
    version=$1
fi

multipass stop primary1
multipass delete primary1
multipass purge 
echo ">>>multipass instances stopped and deleted"

script_path="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
multipass launch -d 15G -n primary1 --cloud-init "$script_path"/vm-cloud-init.yml "$version"

ssh-keygen -f "/home/user/.ssh/known_hosts" -R "primary.multipass"
primary_ip="$(multipass list | grep primary | awk -F' +' '{print $3}')"
sudo sed -i "s|.*primary.*|$primary_ip primary.multipass|g" /etc/hosts
