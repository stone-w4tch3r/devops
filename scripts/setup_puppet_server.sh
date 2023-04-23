#!/bin/bash

echo ">>>this script sets up puppet server on the system"
echo ">>>should be run within target system"
echo ">>>installs puppet7"
echo ">>>dependencies: ubuntu (debian?), wget, amd64 OR aarch64+20.04"

#get and install puppet repo
wget https://apt.puppetlabs.com/puppet7-release-"$(lsb_release -cs)".deb
sudo dpkg -i puppet7-release-"$(lsb_release -cs)".deb

sudo apt-get update
sudo apt-get install puppetserver -y

#install ntp (for time sync)
sudo apt-get -y install ntp
sudo service ntp restart

#run puppet server
sudo /opt/puppetlabs/bin/puppet resource service puppetserver ensure=running enable=true