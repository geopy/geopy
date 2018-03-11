.PHONY: lint
.PHONY: test
.PHONY: clean
.PHONY: docs
.PHONY: dist
.PHONY: release

develop:
	virtualenv .venv --distribute
	. .venv/bin/activate
	python setup.py develop && python setup.py test

lint:
	./lint.sh

pylint:
	pylint --rcfile .pylintrc geopy

test:
	nosetests --verbose --with-cover --cover-erase --cover-package=geopy

clean:
	find . -name "*.pyc" -print0 | xargs -0 rm -rf

docs:
	touch docs/_build/html/index.rst
	cd docs && make html

dist:
	rm -rf dist
	pandoc -f markdown -t rst README.md > README
	python setup.py sdist --format=gztar
	pip wheel --no-index --no-deps --wheel-dir dist dist/*.tar.gz
	rm README
	rm -rf *.egg-info

release:
	make dist
	git tag -a $(version)

remote-docs:
	curl -X POST http://readthedocs.org/build/geopy
