#!/bin/bash

echo ">>>this script continues puppet server setup"
echo ">>>it should be run within puppet server system"
echo ">>>it should be run after connecting pupput agent to server"
echo ">>>dependencies: puppetserver, puppet-agent"

#check input
if [ $# -ne 3 ]; then
    echo ">>>usage: continue_setup_puppet_server.sh <puppet_agent_hostname> <puppet_agent_username> <puppet_agent_password>"
    exit 1
fi

puppet_agent_hostname=$1
puppet_agent_username=$2
puppet_agent_password=$3

echo ">>>setting up ca-s (certificate authority)"
sudo /opt/puppetlabs/bin/puppetserver ca setup

echo ">>>certs in /etc/puppetlabs/puppet/ssl/certs/"
ls /etc/puppetlabs/puppet/ssl/certs/

echo ">>>deleting all certs (but why??? idk)"
sudo systemctl stop puppetserver
sudo /opt/puppetlabs/bin/puppetserver ca delete --all
sudo systemctl start puppetserver

echo ">>>signing certs"
sudo /opt/puppetlabs/bin/puppetserver ca sign --certname "$puppet_agent_hostname"

#than agent must request certs again