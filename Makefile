build/base:
	sudo docker build -t app_base . -f base.dockerfile

build/app:
	sudo docker build -t app_app .

build/client:
	eval `ssh-agent -s`
	ssh-add
	sudo docker build --ssh default=${SSH_AUTH_SOCK} -t app_client:latest . -f nginx.dockerfile --no-cache

build: build/base build/app build/client
