ifeq ($(OS), Windows_NT)
	SUDO :=
else
	SUDO := sudo
endif

build/base:
	$(SUDO) docker build -t app_base . -f base.dockerfile

build/app:
	$(SUDO) docker build -t app_app .

build: build/base build/app
