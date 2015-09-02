If you contribute code to geopy, you agree to license your code under the MIT.

geopy runs on both Python 2 and Python 3 on both the CPython and PyPy
interpreters. You should handle any compatibility in `geopy/compat.py`.

You must document any functionality using Sphinx-compatible RST, and
implement tests for any functionality in the `test` directory.

If you want to add additional parameters to a `geocode` or `reverse`
method, the additional parameters must be explicitly specified and documented
in the method signature. Validation may be done for type, but values should
probably not be checked against an enumerated list because the service could
change.

Full integration tests do not run on geopy's Travis CI build because the build
depends on credentials that must remain secret, and a branch could echo
those secrets. To test your changes, obtain valid credentials for the
service or services affected, and run tests on that section locally. The
maintainer will run tests and may alert you to failures in services you have
not tested. You may wonder: why not commit captured data and run mocked
tests? Because there are copyright constraints on the data returned by
services.
