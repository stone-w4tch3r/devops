#!/bin/bash

update(){
    echo ">>>updating"
    cd ~
    sudo apt-get -y update
    sudo apt-get -y upgrade
    sudo apt-get -y dist-upgrade
    sudo apt-get -y autoremove
    sudo apt-get -y autoclean
}

update