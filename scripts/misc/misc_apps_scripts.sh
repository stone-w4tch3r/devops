return 0;

#non-executable


####
#speedtest
####

sudo apt-get install -y curl
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt-get install speedtest

####
#SUPER-DOCKER
####

bash <(curl -sSL https://get.docker.com)
