#!/bin/bash

echo ">>>this script sets up puppet on puppet server and/or agent"
echo ">>>should be run from any system"
echo ">>>dependencies: macos, ssh access to puppet server and/or agent"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"/../puppet || exit
echo ">>>current directory (should be 'puppet'): $(pwd)"

read -p ">>>setup puppet server? (y/n) " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ">>>setting up puppet server"
    sh setup_puppet_server.command
fi

read -p ">>>setup puppet agent? (y/n) " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ">>>setting up puppet agent"
    sh setup_puppet_agent.command
fi

read -p ">>>connect puppet agent to puppet server? (y/n) " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ">>>connecting puppet agent to puppet server"
    sh connect_puppet_agent_and_server.command
fi