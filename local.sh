#!/bin/bash

setup_dependencies(){
    echo ">>>setting up dependencies"
    brew install autossh
}

create_keys(){
    echo ">>>creating keys"
    echo "Enter key name:"
    read keyname
    #-t rsa: use rsa algorithm, -b 4096: use 4096 bit key, -C: comment, -f: file name
    ssh-keygen -t rsa -b 4096 -C "$keyname" -f ~/.ssh/$keyname 
}

setup_ssh(){
    echo ">>>setting up ssh"
    #start ssh-agent in the background
    eval "$(ssh-agent -s)" 
    ssh-add ~/.ssh/$keyname
    echo "Enter ip address:"
    read ipaddress
    echo "Enter username:"
    read username
    echo "Enter your local sudo password:"
    sudo ssh-copy-id -i ~/.ssh/$keyname $username@$ipaddress
}

restore_ssh(){
    echo ">>>restoring ssh"
    eval "$(ssh-agent -k)" #kill ssh-agent
    ssh-keygen -R $ipaddress
    rm ~/.ssh/$keyname
    rm ~/.ssh/$keyname.pub
}

#$1 is the file to be executed on the remote server
reload_server(){
    echo ">>>reloading server"
    ssh $username@$ipaddress 'nohup sudo shutdown -r now'
    sleep 30
    sudo autossh -M 0 -o "ServerAliveInterval 60" -o "ServerAliveCountMax 3" -o "StrictHostKeyChecking no" -i ~/.ssh/$keyname $username@$ipaddress 'exit'
}

load_to_server(){
    echo ">>>loading to server"
    sudo scp $1 $username@$ipaddress:~/
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

create_keys
setup_ssh
update_server
reload_server
finish_setup

#sudo passwd root
#chsh -s /usr/bin/zsh
# sudo apt-get -y install zsh-syntax-highlighting #?
# sudo apt-get -y install zsh-autosuggestions #?

#sudo nano /etc/ssh/sshd_config #password authentication yes
#sudo ssh-copy-id -i ~/.ssh/vps_pq_nl.pub lord@77.91.122.191
#sudo nano /etc/ssh/sshd_config #password authentication no
#sudo systemctl restart sshd

#sudo ssh -i ~/.ssh/vps_pq_nl lord@77.91.122.191
