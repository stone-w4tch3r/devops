#!/bin/bash
set -e

# Install packages
sudo dnf install openssh-server micro nodejs-npm the_silver_searcher wl-clipboard jq -y

# Setup SSH
sudo systemctl enable sshd
sudo mkdir -p $HOME/.ssh
sudo chmod 700 $HOME/.ssh
sudo chown user1:user1 $HOME/.ssh # TODO hardcoded user

if [ -f "/tmp/host-ssh-key/${SSH_KEY_NAME}.pub" ]; then
    sudo cp "/tmp/host-ssh-key/${SSH_KEY_NAME}.pub" $HOME/.ssh/authorized_keys
    sudo chmod 600 $HOME/.ssh/authorized_keys
    sudo chown user1:user1 $HOME/.ssh/authorized_keys # TODO hardcoded user
    echo "SSH key installed successfully"
else
    echo "Warning: SSH key not found"
fi

# # Add host docker wrapper
# sudo mkdir -p /usr/local/bin
# sudo tee /usr/local/bin/docker > /dev/null << 'EOF'
# #!/bin/bash
# # Docker wrapper for distrobox - always uses host Docker
# echo "Calling host's docker with distrobox-host-exec"
# exec distrobox-host-exec docker "$@"
# EOF
# 
# sudo chmod +x /usr/local/bin/docker
# echo "Docker wrapper installed to /usr/local/bin/docker"
# 
# # Add host gh wrapper
# sudo tee /usr/local/bin/gh > /dev/null << 'EOF'
# #!/bin/bash
# # gh wrapper for distrobox - always uses host gh
# echo "Calling host's gh with distrobox-host-exec"
# exec distrobox-host-exec gh "$@"
# EOF
# 
# sudo chmod +x /usr/local/bin/gh
# echo "Docker wrapper installed to /usr/local/bin/gh"

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

# Alias claude from ~/.claude/local
# alias='alias claude="~/.claude/local/claude"'
# if [ ! -f $HOME/.bashrc ]; then
    # echo "$alias" >> $HOME/.bashrc
# else
    # if ! grep -qxF "$alias" $HOME/.bashrc; then
        # sed -i "/alias claude=/d" $HOME/.bashrc
        # echo "$alias" >> $HOME/.bashrc
    # fi
# fi
# if [ ! -f $HOME/.profile ]; then
    # echo "$alias" >> $HOME/.profile
# else
    # if ! grep -qxF "$alias" $HOME/.profile; then
        # sed -i "/alias claude=/d" $HOME/.profile
        # echo "$alias" >> $HOME/.profile
    # fi
# fi
# 
# # chown .profile and .bashrc
# sudo chown user1:user1 $HOME/.bashrc
# sudo chown user1:user1 $HOME/.profile
# 
# # Setup micro
# mkdir -p $HOME/.config/micro
# cat > $HOME/.config/micro/settings.json << 'EOF'
# {
    # "clipboard": "terminal",
    # "mkparents": true
# }
# 
# EOF
# sudo chown -R user1:user1 $HOME/.config/micro
# 
# # Setup broot
# sudo curl -s https://dystroy.org/broot/download/x86_64-linux/broot --output /usr/local/bin/broot
# sudo chmod ugo+x /usr/local/bin/broot
# /usr/local/bin/broot --install
# sudo chown -R user1:user1 $HOME/.local
sudo chown -R user1:user1 $HOME/.ssh
