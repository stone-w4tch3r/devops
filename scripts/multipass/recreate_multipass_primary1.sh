#!/bin/bash

sudo echo ">>>this is a script that recreates the multipass instance and sets /etc/hosts"
multipass delete primary1 && multipass purge 
multipass launch -d 15G -n primary1 --cloud-init vm-cloud-init.yml
primary_ip="$(multipass list | grep primary | awk -F' +' '{print $3}')" && echo "$primary_ip" | sudo sed -i "s|.*primary.*|$primary_ip primary.multipass|g" /etc/hosts