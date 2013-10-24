"""
Exceptions raised by geopy.
"""

class GeocoderError(Exception):
    """
    Catch-all
    """

class GeocoderAuthenticationFailure(GeocoderError):
    """
    Geocoder has rejected API key or such.
    """

class GeocoderInsufficientPrivileges(GeocoderError):
    """
    Geocoder recognizes us, doesn't agree with requested permissions.
    """

class ConfigurationError(GeocoderError):
    """
    Error in configuring a geocoder
    """

class QueryError(GeocoderError):
    """
    Bad input to a geocoder method cannot be handled.
    """
