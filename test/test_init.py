from distutils.version import LooseVersion

from geopy import __version__, __version_info__, get_version


def test_version():
    assert isinstance(__version__, str) and __version__


def test_version_info():
    expected_version_info = tuple(LooseVersion(__version__).version)
    assert expected_version_info == __version_info__


def test_get_version():
    version = get_version()
    assert isinstance(version, str) and version == __version__
