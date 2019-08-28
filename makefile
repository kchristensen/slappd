SHELL = /bin/bash
VIRTUALENV_DIR = ${HOME}/.virtualenv

.PHONY: dev
dev: ${VIRTUALENV_DIR}/slappd
	source ${VIRTUALENV_DIR}/slappd/bin/activate && \
		pip install -U bandit flake8 pip pylint && \
		pip install --editable .

.PHONY: docker-build
docker-build:
	docker build -t slappd .

.PHONY: docker-run
docker-run: docker-build
	docker run -v ${HOME}/.config/slappd:/home/slappd/.config/slappd slappd

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
	-bandit -r .
	-flake8

.DEFAULT_GOAL := install