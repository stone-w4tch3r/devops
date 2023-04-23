#!/bin/bash

echo ">>>this script updates the target system and reboots"

echo ">>>updating"
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y dist-upgrade
sudo apt-get -y autoremove
sudo apt-get -y autoclean

echo ">>>rebooting"
sudo reboot