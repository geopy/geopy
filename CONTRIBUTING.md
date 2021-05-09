# Contributing to geopy

## Reporting issues

If you caught an exception from geopy please try to Google the error first.
There is a great chance that it has already been discussed somewhere
and solutions have been provided (usually on GitHub or on Stack Overflow).

Before reporting an issue please ensure that you have tried
to get the answer from the doc: https://geopy.readthedocs.io/.

Keep in mind that if a specific geocoding service's API is not behaving
correctly then it probably won't be helpful to report that issue
here, see https://geopy.readthedocs.io/en/latest/#geopy-is-not-a-service

The following resources are available for your input:

1. Stack Overflow with [geopy tag](https://stackoverflow.com/questions/tagged/geopy).
   There's a somewhat active community here so you will probably get
   a solution quicker. And also there is a large amount of already
   resolved questions which can help too! Just remember to put the `geopy`
   tag if you'd decide to open a question.
1. [GitHub Discussions](https://github.com/geopy/geopy/discussions) is
   a good place to start if Stack Overflow didn't help or you have
   some idea or a feature request you'd like to bring up, or if you
   just have trouble and not sure you're doing everything right.
   Solutions and helpful snippets/patterns are also very welcome here.
1. [GitHub Issues](https://github.com/geopy/geopy/issues) should only
   be used for definite bug reports and specific tasks. If you're not sure
   whether your issue fits this then please start with Discussions
   first.


## Submitting patches

If you contribute code to geopy, you agree to license your code under the MIT.

The new code should follow [PEP8](https://pep8.org/) coding style (except
the line length limit, which is 90) and adhere to the style of 
the surrounding code.

You must document any functionality using Sphinx-compatible RST, and
implement tests for any functionality in the `test` directory.

In your Pull Requests there's no need to fill the changelog or AUTHORS,
this is a maintainer's responsibility.

For your convenience the contributing-friendly issues are marked with
`help wanted` label, and the beginner-friendly ones with
`good first issue`.

If your PR remains unreviewed for a while, feel free to bug the maintainer.


### Setup

1.  Create a virtualenv
2.  Install `geopy` in editable mode along with dev dependencies:

        pip install -e ".[dev]"

3.  Ensure that tests pass

        make test


### Running tests

To quickly run the test suite without Internet access:

    make test-local

To run the full test suite (makes queries to the geocoding services):

    make test

Or simply:

    pytest

To run a specific test module, pass a path as an argument to pytest.
For example:

    pytest test/geocoders/nominatim.py

Before pushing your code, make sure that linting passes, otherwise a CI
build would fail:

    make lint


### Geocoder credentials

Some geocoders require credentials (like API keys) for testing. They must
remain secret, so if you need to test a code which requires them, you should
obtain your own valid credentials.

Tests in CI from forks and PRs run in `test-local` mode only, i.e. no network
requests are performed. Full test suite with network requests is run only
for pushes to branches by maintainers. This
helps to reduce load on the geocoding services and save some quotas associated
with the credentials used by geopy. It means that PR builds won't actually test
network requests. Code changing a geocoder should be tested locally.
But it's acceptable to not test such code if obtaining the required credentials 
seems problematic: just leave a note
so the maintainers would be aware that the code hasn't been tested.

You may wonder: why not commit captured data and run mocked tests?
Because there are copyright constraints on the data returned by services.
Another reason is that this data goes obsolete quite fast, and maintaining
it is cumbersome.

To ease local testing the credentials can be stored in a json format
in a file called `.test_keys` located at the root of the project
instead of env variables.

Example contents of `.test_keys`:

    {
        "BING_KEY": "...secret key...",
        "OPENCAGE_KEY": "...secret key..."
    }


### Building docs

    make docs

Open `docs/_build/html/index.html` with a browser to see the docs. On macOS you 
can use the following command for that:

    open docs/_build/html/index.html


### Adding a new geocoder

Patches for adding new geocoding services are very welcome! It doesn't matter
how popular the target service is or whether its territorial coverage is
global or local.

A checklist for adding a new geocoder:

1.  Create a new geocoding class in its own Python module in the
    `geopy/geocoders` package. Please look around to make sure that you're
    not reimplementing something that's already there! For example, if you're
    adding a Nominatim-based service, then your new geocoder class should
    probably extend the `geopy.geocoders.Nominatim` class.

2.  Follow the instructions in the `geopy/geocoders/__init__.py` module for
    adding the required imports.

3.  Create a test module in the `test/geocoders` directory. If your geocoder
    class requires credentials, make sure to access them via
    the `test.geocoders.util.env` object
    (see `test/geocoders/what3words.py` for example).
    Refer to the [Geocoder credentials](#geocoder-credentials) section
    above for info on how to work with credentials locally.

4.  Complete your implementation and tests! Give TDD a try if you aren't used
    to it yet! 🎉 Please note that it's possible to run a single test module
    instead of running the full suite, which is much slower. Refer to the
    [Running tests](#running-tests) section above for a command example.

5.  Make sure to document the `geocode` and `reverse` methods with all their
    parameters. The class doc should contain a URI to the Terms of Service.

6.  Add a reference to that class in the `docs/index.rst` file. Please keep
    them ordered alphabetically by their module file names. Build the docs
    ([Building docs](#building-docs) section above) to make sure that you've
    done them right!

7.  If your tests use credentials, add their names to
    the end of the `.github/workflows/ci.yml` file.

That's all!

### Improving a geocoder

If you want to add additional parameters to a `geocode` or `reverse`
method, the additional parameters must be explicitly specified and documented
in the method signature. Validation may be done for type, but values should
probably not be checked against an enumerated list because the service could
change. The additional parameters should go to the end of the method signature.

Please avoid simply passing through arbitrary parameters
(e.g. with `**kwargs`) to the params of a request to the target service.
The target service parameters might change, as well as the service's API,
but the geocoder class's public API should stay the same. It's almost
impossible to achieve that when a pass-through of arbitrary parameters is
allowed.

