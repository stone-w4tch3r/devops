#!/bin/bash

echo ">>>this script sets up users and groups for the system"

main(){
    local username=$1
    local password=$2
    local root_password=$3
    echo ">>>setting up users"
    
    echo ">>>changing root password"
    echo "root:$root_password" | sudo chpasswd
    
    echo ">>>adding user"
    #--gecos "" prevents user from being prompted for additional info (like full name), --disabled-password prevents user from logging in with password
    sudo useradd --gecos "" --disabled-password "$username"
    echo "$username:$password" | sudo chpasswd
    
    echo ">>>adding user to sudo and docker group"
    #-aG means append to group
    sudo usermod -aG sudo "$username"
    sudo usermod -aG docker "$username"
}

if [ $# -ne 3 ]; then
    echo "Usage: setup_users.sh username password root_password"
    return 1
fi

main "$1" "$2" "$3"