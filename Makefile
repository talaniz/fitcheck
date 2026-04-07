.PHONY: setup install

setup:
	rm -rf .venv
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

install:
	rm -rf .venv
	python3 -m venv .venv
	.venv/bin/pip install -e .
