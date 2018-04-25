SHELL = /bin/bash
VIRTUALENV_DIR = ${HOME}/.virtualenv
CFG_DIR = ${HOME}/.config/slappd

.PHONY: config
config:
	mkdir -p ${CFG_DIR}
	test -f ${CFG_DIR}/slappd.cfg || cp -p slappd.cfg.dist ${CFG_DIR}/slappd.cfg

.PHONY: dev
dev: ${VIRTUALENV_DIR}/slappd
	source ${VIRTUALENV_DIR}/slappd/bin/activate && \
		pip install -U flake8 pip && \
		pip install --editable .

.PHONY: install
install: ${VIRTUALENV_DIR}/slappd
	source ${VIRTUALENV_DIR}/slappd/bin/activate && \
		pip install -U pip && \
		pip install --upgrade .

${VIRTUALENV_DIR}/slappd:
	mkdir -p ${VIRTUALENV_DIR}
	cd ${VIRTUALENV_DIR} && python3 -m venv slappd

.PHONY: lint
lint:
	-flake8

.DEFAULT_GOAL := install