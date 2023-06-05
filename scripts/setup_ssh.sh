#!/bin/bash

echo ">>>this script connects to a remote system and sets up ssh keys for passwordless login"
echo ">>>dependencies: macos, bolt, security"

delete_key_on_remote(){
    if [ $# -ne 4 ]; then
        echo "Usage: delete_key_on_remote keyname username ipaddress remote_password"
        return 1
    fi
    
    local keyname=$1
    local username=$2
    local ipaddress=$3
    local remote_password=$4
    echo ">>>deleting key on remote"
    
    local command
    #remove key from authorized_keys, and print authorized_keys
    command="sed -i.bak '\|$(cat ~/.ssh/"$keyname".pub)|d' ~/.ssh/authorized_keys && echo '>>>contents of authorized_keys:' && cat ~/.ssh/authorized_keys"
    bolt command run "$command" --targets "$ipaddress" --user "$username" --password "$remote_password"
}

validate(){
  #check if ip is reachable
  if ! ping -c 1 "$_ipaddress" &>/dev/null; then
    echo ">>>ipaddress is not reachable"
    exit 1
  fi
}

rollback_ssh(){    
    local keyname=$_keyname
    local ipaddress=$_ipaddress
    local username=$_username
    local remote_password=$_remote_password
    echo ">>>restoring ssh"
    
    delete_key_on_remote "$keyname" "$username" "$ipaddress" "$remote_password"
    eval "$(ssh-agent -k)" #kill ssh-agent
    ssh-keygen -R "$ipaddress" #remove ip from known_hosts
    ssh-add -d ~/.ssh/"$keyname" #remove key from ssh-agent
    #remove key from keychain, -a: account, -s: service, -l: label
    security delete-generic-password -a "$USER" -s "$keyname" -l "$keyname" 2>/dev/null
    sed -i '' "/$keyname/d" ~/.ssh/config #remove key $keyname from ssh config
    sed -i '' "/$ipaddress/d" ~/.ssh/config #remove key $ipaddress from ssh config
    rm ~/.ssh/"$keyname"
    rm ~/.ssh/"$keyname".pub
}

create_keys(){
    if [ $# -ne 2 ]; then
        echo "Usage: create_keys keyname passphrase"
        return 1
    fi
    
    local keyname=$1
    local passphrase=$2
    echo ">>>creating keys"
    
    rollback_ssh
    #-t rsa: use rsa algorithm, -b 4096: use 4096 bit key, -C: comment, -f: file, -N: passphrase
    ssh-keygen -t rsa -b 4096 -C "$keyname" -f ~/.ssh/"$keyname" -N "$passphrase"
    cat ~/.ssh/"$keyname".pub
}

modify_ssh_config(){
    if [ $# -ne 1 ]; then
        echo "Usage: modify_ssh_config keyname"
        return 1
    fi
    
    local keyname=$1
    echo ">>>modifying ssh config"
    
    if [ ! -f ~/.ssh/config ]; then
        touch ~/.ssh/config
    fi
    if ! grep -q "Host \*" ~/.ssh/config; then
      echo ">>>adding keychain settings to ssh config"
      {
          echo "Host *"
          echo "  AddKeysToAgent yes"
          echo "  UseKeychain yes"
      } >> ~/.ssh/config
    fi
    echo ">>>ssh config"
    cat ~/.ssh/config
    echo "---"
}

install_key_locally(){
    if [ $# -ne 2 ]; then
        echo "Usage: install_key_locally keyname"
        return 1
    fi
    
    local keyname=$1
    local ipaddress=$2
    echo ">>>installing key locally"
    
    ssh-keyscan "$ipaddress" >> ~/.ssh/known_hosts #add server pub keys to known hosts
    ssh-add --apple-use-keychain ~/.ssh/"$keyname"  #add key to keychain
    {
        echo "Host $ipaddress"
        echo "  HostName $ipaddress"
        echo "  IdentityFile ~/.ssh/$keyname"
    } >> ~/.ssh/config
    modify_ssh_config "$keyname"
}

install_key_on_remote(){
    if [ $# -ne 4 ]; then
        echo "Usage: install_key_on_remote keyname username ipaddress remote_password"
        return 1
    fi
    
    local keyname=$1
    local username=$2
    local ipaddress=$3
    local remote_password=$4
    echo ">>>installing key on remote"
    
    local command
    #create .ssh directory if it doesn't exist, append public key to authorized_keys, and print authorized_keys
    command="mkdir -p ~/.ssh && echo $(cat ~/.ssh/"$keyname".pub) >> ~/.ssh/authorized_keys && echo '>>>contents of authorized_keys:' && cat ~/.ssh/authorized_keys"
    bolt command run "$command" --targets "$ipaddress" --user "$username" --password "$remote_password"
}

main(){
  create_keys "$1" "$5"
  install_key_locally "$1" "$3"
  install_key_on_remote "$1" "$2" "$3" "$4"
}

if [ $# -ne 5 ]; then
    echo "Usage: $0 keyname username ipaddress remote_password passphrase"
    exit 1
fi

_keyname=$1
_username=$2
_ipaddress=$3
_remote_password=$4

# Set up a trap to catch errors and execute the rollback_ssh function
# commented out because it causes multiple rollback_ssh calls on every command in shell
#if ! trap -p ERR | grep -q rollback_ssh; then
#  trap rollback_ssh ERR
#fi

# Set up a trap to catch Ctrl-C and execute the rollback_ssh function
if ! trap -p INT | grep -q rollback_ssh; then
  trap rollback_ssh INT
fi

validate
main "$1" "$2" "$3" "$4" "$5"