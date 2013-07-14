#!/usr/bin/env make

install: install_submodules

install_submodules:
	git submodule init
	git submodule update

