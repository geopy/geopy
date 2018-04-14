# Contributing to geopy

## Reporting issues

- Please note that the issue tracker is not for questions. Use Stack Overflow
  instead. Make sure to tag your question with
  [geopy](https://stackoverflow.com/questions/tagged/geopy) tag.

- If possible, before submitting an issue report try to verify that the issue
  haven't already been fixed and is not a duplicate.

## Submitting patches

If you contribute code to geopy, you agree to license your code under the MIT.

geopy runs on both Python 2 and Python 3 on both the CPython and PyPy
interpreters. You should handle any compatibility in `geopy/compat.py`.

The new code should follow [PEP8](https://pep8.org/) coding style (except
the line length limit) and adhere to the style of the surrounding code.

You must document any functionality using Sphinx-compatible RST, and
implement tests for any functionality in the `test` directory.

In your Pull Requests there's no need to fill the changelog or AUTHORS,
this is a maintainer's responsibility.

For your convenience the contributing-friendly issues are marked with
`help wanted` label, and the beginner-friendly ones with
`good first issue`.

If your PR remains unreviewed for a while, feel free to bug the maintainer.

### Setup

1. Create a virtualenv
2. Install `geopy` in editable mode along with dev dependencies:

        pip install -e ".[dev]"

3. Ensure that the tests pass

        pytest

### Running tests

To run the full test suite:

    pytest

To run a specific test, pass a path as an argument. For example:

    pytest test/geocoders/nominatim.py

### Geocoder credentials

Some geocoders require credentials (like API keys) for testing. They must
remain secret, so if you need to test a code which requires them, you should
obtain your own valid credentials.

Travis CI builds for PRs from forks don't have access to these
credentials to avoid the possibility of leaking the secrets by running
untrusted code. This is a [Travis CI policy][travis_env]. It means that CI
builds for PRs from forks won't test the code which require credentials.
Such code should be tested locally. But it's acceptable to not test such code
if obtaining the required credentials seems problematic: just leave a note
so the maintainer would be aware that the code hasn't been tested.

[travis_env]: https://docs.travis-ci.com/user/environment-variables/#Defining-Variables-in-Repository-Settings

You may wonder: why not commit captured data and run mocked tests?
Because there are copyright constraints on the data returned by services.

The credentials can be stored in a json format in a file called `.test_keys`
located at the root of the project instead of env variables for convenience.

Example contents of `.test_keys`:

    {
        "BING_KEY": "...secret key...",
        "OPENCAGE_KEY": "...secret key..."
    }

### Building docs

    cd docs
    make html

Open `_build/html/index.html` with a browser to see the docs. On macOS you 
can use the following command for that:

    open _build/html/index.html

### Improving a geocoder

If you want to add additional parameters to a `geocode` or `reverse`
method, the additional parameters must be explicitly specified and documented
in the method signature. Validation may be done for type, but values should
probably not be checked against an enumerated list because the service could
change.

