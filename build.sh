eval `ssh-agent -s`
ssh-add ~/.ssh/id_rsa

sudo docker build -t edge_auctions_app:latest .
sudo docker build --ssh default=${SSH_AUTH_SOCK} -t edge_auctions_client:latest . -f nginx.dockerfile
