1. Install on client
  `sudo apt install clevis clevis-luks`
2. Run docker container on server
3. Find encrypted drive
   - `lsblk`
   - `sudo cryptsetup luksDump /dev/sda3` # verify it's encrypted
