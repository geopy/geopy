.PHONY: develop
.PHONY: lint
.PHONY: test
.PHONY: clean
.PHONY: docs
.PHONY: authors
.PHONY: dist
.PHONY: pypi-release
.PHONY: release

version := $(shell python -c 'from geopy import __version__; print(__version__)')

develop:
	[ -d .venv ] || virtualenv .venv --python=python3
	. .venv/bin/activate
	pip install -e '.[dev]'

lint:
	flake8

test:
	coverage run -m py.test
	coverage report

clean:
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	rm -Rf dist
	rm -Rf *.egg-info

docs:
	touch docs/_build/html/index.rst
	cd docs && make html

authors:
	git log --format='%aN <%aE>' `git describe --abbrev=0 --tags`..@ | sort | uniq >> AUTHORS
	cat AUTHORS | sort --ignore-case | uniq >> AUTHORS_
	mv AUTHORS_ AUTHORS

dist:
	make clean
	./setup.py sdist --format=gztar bdist_wheel

pypi-release:
	twine --version
	twine upload -s dist/*

release:
	make dist
	git tag -s $(version)
	git push origin $(version)
	make pypi-release

