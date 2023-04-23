#!/bin/bash

echo ">>>this script sets up puppet agent on the system"
echo ">>>should be run within target system"
echo ">>> installs puppet7"
echo ">>>dependencies: ubuntu (debian?), wget, amd64 OR aarch64+20.04"

#get puppet repo (based on current system)
wget https://apt.puppetlabs.com/puppet7-release-"$(lsb_release -cs)".deb

#install puppet repo
sudo dpkg -i puppet7-release-"$(lsb_release -cs)".deb

sudo apt-get update
sudo apt-get install puppet-agent -y

#run puppet agent
sudo /opt/puppetlabs/bin/puppet resource service puppet ensure=running enable=true