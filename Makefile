.PHONY: setup install

setup:
	rm -rf .venv
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

install:
	rm -rf .venv
	python3 -m venv .venv
	.venv/bin/pip install -e .
	@# Python 3.14+ on macOS skips .pth files with the hidden flag.
	@# Setuptools editable installs create __editable__*.pth, which macOS
	@# marks hidden because of the leading underscores.
	-chflags nohidden .venv/lib/python*/site-packages/__editable__*.pth 2>/dev/null
