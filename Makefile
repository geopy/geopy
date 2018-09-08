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

venv:
	[ -d .venv ] || virtualenv .venv --python=python3
	. .venv/bin/activate

piplocal:
	pip install -e '.[dev]'

develop: venv piplocal

lint:
	flake8

test:
	coverage run -m py.test
	coverage report

readme_check:
	./setup.py check --restructuredtext --strict

rst_check:
	make readme_check
	# Doesn't generate any output but prints out errors and warnings.
	make -C docs dummy

clean:
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	rm -Rf dist
	rm -Rf *.egg-info

docs:
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

