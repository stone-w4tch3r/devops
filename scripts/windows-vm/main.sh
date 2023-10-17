#!/bin/bash

echo ">>> This script will prepare linux for windows vm"
echo ">>> Requires deb-based system"

echo ">>> Installing quickemu"

sudo apt-add-repository ppa:flexiondotorg/quickemu
sudo apt-get update
sudo apt-get install quickemu

echo ">>> You can install quickgui, but for now it works shitty"
echo ">>> Uncomment this lines if you want to install it"
# sudo add-apt-repository ppa:yannick-mauray/quickgui
# sudo apt-get update
# sudo apt-get install quickgui

echo ">>> setting up qemu bridged network"
#https://spad.uk/really-simple-network-bridging-with-qemu/

echo "allow brwin0" | sudo tee -a /etc/qemu/bridge.conf
sudo chmod +s /usr/lib/qemu/qemu-bridge-helper
default_iface=$(ip route | grep default | awk '{print $5}')
sudo brctl addbr brwin0
sudo brctl addif brwin0 "$default_iface" #TODO fix not working with wireless
sudo ip addr add 192.168.13.20/24 dev brwin0
sudo ip link set brwin0 up

echo ">>> Installing spice for file and clipboard sharing"
sudo apt-get install spice-client-gtk

echo ">>> Downloading and running win10"
echo ">>> Deafults: Username=Quickemu, Password=quickemu"

quickget windows 10
quickemu --vm windows-10-22H2.conf --display spice