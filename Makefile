.PHONY: lint
.PHONY: test
.PHONY: clean
.PHONY: docs
.PHONY: dist
.PHONY: release

develop:
	virtualenv .venv --distribute
	. .venv/bin/activate && python setup.py develop && python setup.py test

lint:
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
	pandoc -f markdown -t rst README.markdown > README
	python setup.py sdist --format=gztar
	rm README
	rm -rf *.egg-info

release:
	make dist
	git tag -a release-$(version) -m "Release $(version)"
