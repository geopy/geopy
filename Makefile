version := $(shell python -c 'from geopy import __version__; print(__version__)')

.PHONY: venv
venv:
	[ -d .venv ] || python3 -m venv .venv
	# Activate: `. .venv/bin/activate`

.PHONY: develop
develop:
	pip install wheel
	pip install -e '.[dev]'

.PHONY: lint lint-flake8 lint-isort
lint-flake8:
	flake8 geopy test *.py
lint-isort:
	isort --check-only geopy test *.py
lint: lint-flake8 lint-isort

.PHONY: format
format:
	isort geopy test *.py

.PHONY: test-local
test-local:
	@# Run tests without Internet. These are fast and help to avoid
	@# spending geocoders quota for test runs which would fail anyway.
	python -m pytest --skip-tests-requiring-internet

.PHONY: test
test: test-local
	# Run tests with Internet:
	coverage run -m pytest
	coverage report

.PHONY: readme_check
readme_check:
	./setup.py check --restructuredtext --strict

.PHONY: rst_check
rst_check:
	make readme_check
	# Doesn't generate any output but prints out errors and warnings.
	make -C docs dummy

.PHONY: clean
clean:
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	rm -Rf dist
	rm -Rf *.egg-info

.PHONY: docs
docs:
	cd docs && make html

.PHONY: authors
authors:
	git log --format='%aN <%aE>' `git describe --abbrev=0 --tags`..@ | sort | uniq >> AUTHORS
	cat AUTHORS | sort --ignore-case | uniq >> AUTHORS_
	mv AUTHORS_ AUTHORS

.PHONY: dist
dist:
	make clean
	./setup.py sdist --format=gztar bdist_wheel

.PHONY: pypi-release
pypi-release:
	twine --version
	twine upload -s dist/*

.PHONY: release
release:
	make dist
	git tag -s $(version)
	git push origin $(version)
	make pypi-release

