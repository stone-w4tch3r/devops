#!/bin/bash

echo ">>>this script sets up puppet agent on the system"
echo ">>>should be run within target system"
echo ">>>installs puppet6"
echo ">>>dependencies: ubuntu (debian?), wget, amd64 OR aarch64+20.04"

if [ -z "$1" ]; then
    echo "usage $0 <puppetserver ip address>"
    exit 1
fi

server_ip=$1

#get and install puppet repo (based on current system)
wget https://apt.puppetlabs.com/puppet6-release-"$(lsb_release -cs)".deb
sudo dpkg -i puppet6-release-"$(lsb_release -cs)".deb

sudo apt-get update
sudo apt-get install puppet-agent -y

#install ntp (for time sync)
sudo apt-get -y install ntp
sudo service ntp restart

#run puppet agent
sudo /opt/puppetlabs/bin/puppet resource service puppet ensure=running enable=true

#add server to /etc/hosts
echo "$server_ip puppetserver" | sudo tee -a /etc/hosts

#add server to /etc/puppetlabs/puppet/puppet.conf
sudo /opt/puppetlabs/bin/puppet config set server 'puppetserver' --section main