#!/bin/bash

install_packages(){
    echo ">>>installing packages"
    cd ~
    sudo apt-get -y install git
    sudo apt-get -y install python3-pip
    sudo apt-get -y install python3-venv
    sudo apt-get -y install python3-dev
    sudo apt-get -y install docker-compose
    sudo apt-get -y install curl
    sudo apt-get -y install wget
    sudo apt-get -y install webmin
    sudo apt-get -y install nano

    curl -o setup-repos.sh https://raw.githubusercontent.com/webmin/webmin/master/setup-repos.sh
    sudo sh setup-repos.sh
    curl -sSL https://get.docker.com | sh
    sudo usermod -aG docker $(whoami)
}

install_zsh(){
    echo ">>>installing zsh"
    cd ~
    wget https://raw.github.com/iofu728/zsh.sh/master/zsh.sh
    bash zsh.sh && source ${ZDOTDIR:-$HOME}/.zshrc
    bash zsh.sh && source ${ZDOTDIR:-$HOME}/.zshrc
}

install_packages
install_zsh