# Windows Development VM Setup

Simple windows dev vm with basic configuration

## Prerequisites

### For macOS

```bash
brew install --cask virtualbox vagrant
brew install ansible
vagrant plugin install vagrant-parallels
```

### For Linux (Ubuntu/Debian)

```bash
sudo apt update && sudo apt install virtualbox ansible -y
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt update && sudo apt install vagrant -y
```

### For Linux (Fedora/RHEL/CentOS)

```bash
# Install RPMFusion first: https://rpmfusion.org/Howto/VirtualBox
dnf install VirtualBox ansible vagrant
akmods && systemctl restart vboxdrv
```

## Setup Instructions

1. **Clone and navigate to the repo**:

   ```bash
   cd devops/win/vagrant-vm-setup
   ```

2. **Start the VM**: `vagrant up`
   - Auto-selects provider (virtualbox/parallels)
   - Downloads Windows 11 image
   - Configures VM with Ansible

3. **Access**: Login with `vagrant`/`vagrant`

4. **VM Commands**:
   - Suspend: `vagrant suspend`
   - Resume: `vagrant resume`
   - Stop: `vagrant halt`
   - Delete: `vagrant destroy`

## Running Ansible Standalone

1. **Ansible ini files are pre-packed**

2. **Usage examples**:

   ```bash
   # Run all
   ansible-playbook -i ansible/inventory.ini ansible/playbook.yml -e ansible_remote_tmp=/tmp/.ansible-xxx/tmp
   
   # Run specific tags
   ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --tags "winget_packages,powershell"
   
   # Skip tags
   ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --skip-tags "vbox_guestadditions"
   
   # Pass variables
   ansible-playbook -i ansible/inventory.ini ansible/playbook.yml -e "is_vbox=true"
   ```

## Running Ansible on Windows

### Running Ansible from Windows to Itself

1. **Using WSL**:

   a. **Install WSL**:

   ```powershell
   wsl --install
   Restart-Computer
   ```

   b. **Install Ubuntu**:

   ```powershell
   wsl --install ubuntu
   wsl
   ```

   c. **Setup Ansible**:

   ```bash
   sudo apt update && sudo apt install ansible python3-pip -y
   pip install pywinrm
   ```

   d. **Run playbook**:

   ```bash
   ansible-playbook -i ~/ansible/inventory-itself-from-wsl.ini playbook.yml -e ansible_remote_tmp=/tmp/.ansible-xxx/tmp
   ```

### Preparing Windows for WinRM

Run in PowerShell as Administrator:

```powershell
winrm quickconfig -q
winrm set winrm/config/service '@{AllowUnencrypted="true"}'
winrm set winrm/config/service/auth '@{Basic="true"}'
# For testing only (reduces security)
Set-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -Value 1 -Type DWord
```
