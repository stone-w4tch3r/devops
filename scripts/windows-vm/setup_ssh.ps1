# Setups SSH for Ansible
Add-WindowsCapability -Online -Name OpenSSH.Server*
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
Start-Service ssh-agent
Set-Service -Name ssh-agent -StartupType 'Automatic'
netsh advfirewall firewall add rule name="Open SSH Port 22" dir=in action=allow protocol=TCP localport=22 remoteip=any
