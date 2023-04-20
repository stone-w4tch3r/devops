#!/bin/bash

setup_dependencies(){
    echo ">>>setting up dependencies"
    brew install autossh
}

#create function for shell script that reads from config file, echoes it and than sets some global variables from config.
#config items are:
#server-ip, default-user, user, default-passwd, passwd, keyname, passphrase
#config file is in the same directory as the script
#config file is called config
read_config(){
    echo ">>>reading config"
    local config_file
    config_file=$(dirname "$0")/config
    local config_items=(server-ip default-user user default-passwd passwd keyname passphrase)
    local config_item
    for config_item in "${config_items[@]}"; do
        local config_value
        config_value=$(grep "$config_item" "$config_file" | cut -d '=' -f 2)
        echo "$config_item=$config_value"
        eval "$config_item=$config_value"
    done
}

create_keys(){
    if [ $# -ne 2 ]; then
        echo "Usage: $0 keyname passphrase"
        exit 1
    fi
    local keyname=$1
    local passphrase=$2
    echo ">>>creating keys"
    #-t rsa: use rsa algorithm, -b 4096: use 4096 bit key, -C: comment, -f: file, -N: passphrase
    ssh-keygen -t rsa -b 4096 -C "$keyname" -f ~/.ssh/"$keyname" -N "$passphrase"
}

setup_ssh(){
    if [ $# -ne 3 ]; then
        echo "Usage: $0 keyname username ipaddress"
        exit 1
    fi
    local keyname=$1
    local username=$2
    local ipaddress=$3
    echo ">>>setting up ssh"
    #start ssh-agent in the background
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/"$keyname"
    echo "Enter your local sudo password:"
    sudo ssh-copy-id -i ~/.ssh/"$keyname" "$username"@"$ipaddress"
}

undo_ssh(){
    if [ $# -ne 2 ]; then
        echo "Usage: $0 keyname ipaddress"
        exit 1
    fi
    local keyname=$1
    local ipaddress=$2
    echo ">>>restoring ssh"
    eval "$(ssh-agent -k)" #kill ssh-agent
    ssh-keygen -R "$ipaddress"
    rm ~/.ssh/"$keyname"
    rm ~/.ssh/"$keyname".pub
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
    sudo ssh $username@$ipaddress 'bash -s' < remote1.sh
}    

finish_setup(){
    load_to_server remote2.sh
    load_to_server remote3.sh
}

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
