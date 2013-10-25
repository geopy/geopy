.PHONY: lint
.PHONY: test
.PHONY: clean
.PHONY: docs

develop:
	virtualenv .venv --distribute
	. .venv/bin/activate && python setup.py develop && pip install nose-cov pylint

lint:
	pylint --rcfile .pylintrc geopy

test:
	nosetests --verbose --with-cover --cover-erase --cover-package=geopy

clean:
	find . -name "*.pyc" -print0 | xargs -0 rm -rf

docs:
	touch docs/_build/html/index.rst
	cd docs && make html
