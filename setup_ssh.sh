create_keys(){
    if [ $# -ne 2 ]; then
        echo "Usage: $0 keyname passphrase"
        exit 1
    fi
    local keyname=$1
    local passphrase=$2
    echo ">>>creating keys"
    rm ~/.ssh/"$keyname"
    rm ~/.ssh/"$keyname".pub
    #-t rsa: use rsa algorithm, -b 4096: use 4096 bit key, -C: comment, -f: file, -N: passphrase
    ssh-keygen -t rsa -b 4096 -C "$keyname" -f ~/.ssh/"$keyname" -N "$passphrase"
    cat ~/.ssh/"$keyname".pub
}

add_ssh_with_pass(){

}

setup_ssh(){
    if [ $# -ne 4 ]; then
        echo "Usage: $0 keyname username ipaddress passphrase"
        exit 1
    fi
    local keyname=$1
    local username=$2
    local ipaddress=$3
    local passphrase=$4
    echo ">>>setting up ssh"
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/"$keyname"
    sudo ssh-copy-id -i ~/.ssh/"$keyname" "$username"@"$ipaddress" <<< "$(yes)"
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

if [ $# -ne 4 ]; then
    echo "Usage: $0 keyname username ipaddress passphrase"
    exit 1
fi

sudo echo "sudo password accepted"
create_keys "$1" "$4"
setup_ssh "$1" "$2" "$3" "$4"