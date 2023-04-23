#!/bin/bash

echo ">>>this script connects puppet agent to puppet server"
echo ">>>should be run within puppet server system"
echo ">>>dependencies: puppetserver, puppet-agent"

insert_certname(){
    echo ">>>inserting certname = $agent_name into /etc/puppetlabs/puppet/puppet.conf"
    #s = substitute, \[main\] = [main] (escaped), \[main\]\ncertname = $agent_name = [main]\ncertname = agent_name, g = global (all instances)
    sudo sed -i "s/\[main\]/\[main\]\ncertname = $agent_name/g" /etc/puppetlabs/puppet/puppet.conf
}

if [ $# -ne 1 ]; then
    echo ">>>usage: connect_puppet_agent_and_server.sh <puppet_agent_name>"
    exit 1
fi

agent_name=$1

if grep -q "server = puppetserver" /etc/puppetlabs/puppet/puppet.conf; then
    echo ">>>puppet.conf already contains server = puppetserver"
else
    echo ">>>puppet.conf does not contain server = puppetserver, adding..."
    echo "[main]" | sudo tee -a /etc/puppetlabs/puppet/puppet.conf
    echo "server = puppetserver" | sudo tee -a /etc/puppetlabs/puppet/puppet.conf
fi

#add puppet agent to /etc/puppetlabs/puppet/puppet.conf (certname = puppet_agent_name)
#certname = agent_name should be inserted after [main] in /etc/puppetlabs/puppet/puppet.conf
if grep -q "certname = $agent_name" /etc/puppetlabs/puppet/puppet.conf; then
    echo ">>>puppet.conf already contains certname = $agent_name"
else
    insert_certname
fi