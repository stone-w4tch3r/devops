#!/bin/bash

echo ">>>this interactive script sets up ubuntu server"
echo ">>>requires launched server, allowed root password authentication and root password set"
echo ">>>should be run from remote system"

DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd "$DIR"/../ || exit 1
echo ">>>working directory (should be 'scripts'): $(pwd)"

read -p ">>>continue? (y/n) " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

read -rp ">>>enter instance ip: " instance_ip
read -s -rp ">>>enter root password: " root_password && echo
read -rp ">>>enter instance new username: " new_username
read -s -rp ">>>enter instance new password: " new_password && echo
read -s -rp ">>>enter instance new root password: " new_root_password && echo
read -rp ">>>enter keyname: " keyname
read -s -rp ">>>enter passphrase: " passphrase && echo

echo ">>>adding to known hosts"
ssh-keyscan "$instance_ip" >> ~/.ssh/known_hosts

echo ">>>setting up users and passwords"
bolt script run setup_users.sh --targets "$instance_ip" --user root --password "$root_password" "$new_username" "$new_password" "$new_root_password"

echo ">>>temporary setting sudo nopasswd"
command="echo '$new_username ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/$new_username"
bolt command run "$command" --targets "$instance_ip" --user root --password "$new_root_password"

echo ">>>setting up ssh connection"
sh setup_ssh.sh "$keyname" "$new_username" "$instance_ip" "$new_password" "$passphrase"

echo ">>>updating instance"
ssh "$new_username"@"$instance_ip" "bash -s" < update.sh

echo ">>>waiting for instance to reboot (30s)"
sleep 30

echo ">>>setting up ssh rules"
ssh "$new_username"@"$instance_ip" "bash -s" < setup_ssh_rules.sh

echo ">>>setting up ufw"
ssh "$new_username"@"$instance_ip" "bash -s" < setup_ufw.sh

echo ">>>disabling sudo nopasswd"
command="sudo rm /etc/sudoers.d/$new_username"
bolt command run "$command" --targets "$instance_ip" --user "$new_username" --password "$new_root_password"
