#!/bin/bash
set -euo pipefail

keys_dir="$HOME/.ssh/keys"
vm_name="todo"
vm_ip="todo"

# update /etc/hosts
sudo sed -i "|$vm_name|d" /etc/hosts  #|PATTERN|d - delete line with PATTERN
echo "$vm_ip $vm_name" | sudo tee -a /etc/hosts > /dev/null

# remove identity from known_hosts
ssh-keygen -f "$HOME/.ssh/known_host" -R "$vm_ip" > /dev/null 2>&1  #2>&1 - redirect stderr to stdout
ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$vm_name" > /dev/null 2>&1

# add identity to known_hosts
ssh-keyscan "$vm_name" | tee -a "$HOME"/.ssh/known_hosts > /dev/null 2>&1

# remove old keys
for key in "$keys_dir"/*; do
  if [[ -f "$key" ]]; then # -f - file exists
    rm -f "$key"
  fi
done
