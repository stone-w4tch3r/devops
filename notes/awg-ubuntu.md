To install and enable amnezia wg globally on ubuntu:
1. Ensure deb-src is enabled in `sources.list`  
   - **Ubuntu 22 or lower:**
     1. Open /etc/apt/sources.list
     2. Ensure lines starting with "deb-src" are present (idk how many are needed)
     3. If not, duplicate lines starting with "deb" and replace "deb" with "deb-src"
     4. Optionally, move those lines into /etc/apt/sources.list.d/deb-src.list
   - **Ubuntu 24:**
     1. Go to /etc/apt/sources.list.d
     2. Ensure a file with `Type: deb-src` start exists
     3. If not, copy /etc/apt/sources.list.d/ubuntu.sources and replace `Type: deb` with `Type: deb-src`
2. `sudo apt install -y software-properties-common python3-launchpadlib gnupg2 linux-headers-$(uname -r)`
3. `sudo add-apt-repository ppa:amnezia/ppa -y`
4. `sudo apt update`
5. `sudo apt install -y amneziawg`
6. Install awg-quick etc
```shell
git clone https://github.com/amnezia-vpn/amneziawg-tools
cd amneziawg-tools/src
make
sudo make install
```
7. Add systemd service to `/etc/systemd/system/wg-quick-wg0.service`:
```ini
[Unit]
Description=AmneziaWG via awg-quick for wg0
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
# Adjust the path to config file
ExecStart=/usr/bin/awg-quick up /root/wg0.conf 
ExecStop=/usr/bin/awg-quick down /root/wg0.conf

[Install]
WantedBy=multi-user.target
```
8. Run and autostart: `sudo systemctl enable --now wg-quick-wg0.service`
9. Ensure wg0 network appeared: `ip a | grep wg0`

**Note: to prevent DNS issues, comment out DNS line in wg0.conf**