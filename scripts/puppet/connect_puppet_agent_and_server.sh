#!/bin/bash

echo ">>>this script connects puppet agent to puppet server"
echo ">>>should be run within puppet server system"
echo ">>>dependencies: puppetserver, puppet-agent"

if [ $# -ne 2 ]; then
    echo ">>>usage: connect_puppet_agent_and_server.sh <puppet_agent_name> <agent_ip>"
    exit 1
fi

agent_name=$1
agent_ip=$2

#add server = puppetserver to /etc/puppetlabs/puppet/puppet.conf
sudo /opt/puppetlabs/bin/puppet config set server 'puppetserver' --section main

#add dns_alt_names = puppetserver to /etc/puppetlabs/puppet/puppet.conf
sudo /opt/puppetlabs/bin/puppet config set --section main dns_alt_names 'puppetserver'

#add puppet agent to /etc/puppetlabs/puppet/puppet.conf (certname = puppet_agent_name)
sudo /opt/puppetlabs/bin/puppet config set certname "$agent_name" --section main

#add puppet agent to /etc/hosts
if grep -q "$agent_name" /etc/hosts; then
    echo ">>>/etc/hosts already contains $agent_name"
else
    echo ">>>adding $agent_name to /etc/hosts"
    echo "$agent_ip $agent_name" | sudo tee -a /etc/hosts
fi

#disable /etc/hosts clean on reboot
if grep -q "clean /etc/hosts" /etc/cloud/cloud.cfg; then
    echo ">>>clean /etc/hosts already disabled"
else
    echo ">>>disabling clean /etc/hosts"
    sudo sed -i 's/^manage_etc_hosts.*/manage_etc_hosts: false/g' /etc/cloud/cloud.cfg
fi