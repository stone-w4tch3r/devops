#!/bin/bash

echo ">>>this is a script that recreates the multipass instance"
echo ">>>dependencies: multipass"
echo ">>>instance specs: 15GB disk, 1GB ram, 1 cpu, ubuntu 20.04"

multipass delete puppetserver
multipass purge
multipass launch --name puppetserver --disk 15G --memory 3G --cpus 2 focal