#!/bin/bash

sudo echo ">>>this is a script that recreates the multipass instance and sets /etc/hosts"

multipass stop primary1
multipass delete primary1
multipass purge 
echo ">>>multipass instances stopped and deleted"

script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
multipass launch -d 15G -n primary1 --cloud-init "$script_path"/vm-cloud-init.yml

primary_ip="$(multipass list | grep primary | awk -F' +' '{print $3}')"
sudo sed -i "s|.*primary.*|$primary_ip primary.multipass|g" /etc/hosts