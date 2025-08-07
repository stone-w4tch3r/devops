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

sudo mkdir -p /usr/local/bin
sudo tee /usr/local/bin/docker > /dev/null << 'EOF'
#!/bin/bash
# Docker wrapper for distrobox - always uses host Docker
echo "Calling host's docker with distrobox-host-exec"
exec distrobox-host-exec docker "$@"
EOF

sudo chmod +x /usr/local/bin/docker
echo "Docker wrapper installed to /usr/local/bin/docker"

# Create systemd user service to start sshd on first login
echo "Setting up SSH auto-start service..."
mkdir -p $HOME/.config/systemd/user
tee $HOME/.config/systemd/user/sshd-autostart.service > /dev/null << 'EOF'
[Unit]
Description=Start SSH daemon on first login
After=default.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'sudo systemctl start sshd'
RemainAfterExit=yes

[Install]
WantedBy=default.target
EOF
sudo chown user1:user1 -R $HOME/.config/

# Enable the user service (it will start on next proper login)
systemctl --user enable sshd-autostart.service
