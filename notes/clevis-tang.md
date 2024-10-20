# Clevis and tang with https and multiple network devices
There are multiple guides about auto unlocking luks encrypted drives with clevis + tang.
But my specific setup caused me a lot of pain, so I want to share final solution.

## My constraints
- Ubuntu server 20.04
- 2+ network devices on encrypted server
- Tang should be provided via https

## General info
If you are not familiar with clevis and tang, I recommend first reading one of those guides:
- https://i.am.eddmil.es/posts/clevistang/
- https://habr.com/ru/articles/525706/ [RU]

## Run tang container on server
For sanity we can use containerized version provided by wonderful 
padhihomelab [here](https://hub.docker.com/r/padhihomelab/tang).

If you prefer docker compose:
```yaml
services:
  tang:
    image: padhihomelab/tang
    ports:
      - "${TANG_PORT}:8080"
    volumes:
      - ./db:/db
    tty: true
```

Since we are talking about https, you need to configure reverse proxy. I won't cover this here.

## Setup clevis client
Install packages:
```shell
sudo apt install clevis clevis-luks clevis-initramfs -y
```

Find encrypted drive
- `lsblk` shows your drives, find one with / partition
- `sudo cryptsetup luksDump /dev/sda3` # verify it's encrypted 

Check connection to tang: `curl https://tang.domain.com/adv`

Bind clevis to tang: `sudo clevis luks bind -d /dev/sda3 tang '{"url":"https://tang.domain.com"}'`

## Enable networking in early boot stage
AFAIK in basic scenarios on ubuntu 20.04 clevis will handle this automatically.
But if you want to use https, or you have more than one network device, some configuration is needed.

For https support refer to this awesome repo: [clevis-HTTPS](https://github.com/francsw/clevis-HTTPS).
Remember to make hook script executable with `chmod +x`.

For multiple network devices, you need to specify which one to use. 
For this we can set `ip` kernel parameter in GRUB config.

You may want to use your router's default settings (dhcp), or hardcode static IP. 
In first case use `ip=:::::<network_interface>:dhcp:`, in second 
`ip=<ip>::<gateway>:<netmask>:<hostname>:<network_interface>`.
See [documentation](https://www.kernel.org/doc/Documentation/filesystems/nfs/nfsroot.txt).

So:
1. `sudo nano /etc/default/grub`
2. Append `ip=XXX` to `GRUB_CMDLINE_LINUX_DEFAULT`
3. `sudo update-grub`
4. `sudo update-initramfs -u -k all`

Reboot and try!   
If something is not working, feel free to comment. I am not professional linux admin,
but maybe will be able to help. 

## Useful links:
- https://github.com/latchset/clevis/issues/243