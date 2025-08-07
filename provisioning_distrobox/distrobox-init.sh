#!/bin/bash
set -e

# Setup SSH
sudo systemctl enable sshd
sudo mkdir -p $HOME/.ssh
sudo chmod 700 $HOME/.ssh
sudo chown user1:user1 $HOME/.ssh # TODO hardcoded user

# Copy only the specific public key
if [ -f "/tmp/host-ssh-key/${SSH_KEY_NAME}.pub" ]; then
    sudo cp "/tmp/host-ssh-key/${SSH_KEY_NAME}.pub" $HOME/.ssh/authorized_keys
    sudo chmod 600 $HOME/.ssh/authorized_keys
    sudo chown user1:user1 $HOME/.ssh/authorized_keys # TODO hardcoded user
    echo "SSH key installed successfully"
else
    echo "Warning: SSH key not found"
fi
