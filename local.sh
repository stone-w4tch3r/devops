#!/bin/bash

setup_dependencies(){
    echo ">>>setting up dependencies"
    brew install autossh
}

reload_server(){
    if [ $# -ne 3 ]; then
        echo "Usage: $0 keyname username ipaddress"
        exit 1
    fi
    local keyname=$1
    local username=$2
    local ipaddress=$3
    echo ">>>reloading server"
    ssh "$username"@"$ipaddress" 'nohup sudo shutdown -r now'
    sleep 20
    sudo autossh -M 0 -o "ServerAliveInterval 60" \
      -o "ServerAliveCountMax 3" -o "StrictHostKeyChecking no" \
#      -i ~/.ssh/"$keyname" \
      "$username"@"$ipaddress" 'echo hello'
}

load_to_server(){
    echo ">>>loading to server"
    sudo scp "$1" "$username"@"$ipaddress":~/
    echo "run sh ${1} on remote to continue"
}

update_server(){
    echo ">>>moving to server"
    sudo ssh "$username"@"$ipaddress" 'bash -s' < remote1.sh
}    

finish_setup(){
    load_to_server remote2.sh
    load_to_server remote3.sh
}

source read_config.sh
source setup_ssh.sh "$_keyname" "$_default_user" "$_server_ip" "$_passphrase"

#create_keys
#setup_ssh
#update_server
#reload_server
#finish_setup

#sudo passwd root
#chsh -s /usr/bin/zsh
# sudo apt-get -y install zsh-syntax-highlighting #?
# sudo apt-get -y install zsh-autosuggestions #?

#sudo nano /etc/ssh/sshd_config #password authentication yes
#sudo ssh-copy-id -i ~/.ssh/vps_pq_nl.pub lord@77.91.122.191
#sudo nano /etc/ssh/sshd_config #password authentication no
#sudo systemctl restart sshd

#sudo ssh -i ~/.ssh/vps_pq_nl lord@77.91.122.191
