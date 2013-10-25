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

class GeocoderQueryError(GeocoderError):
    """
    Geocoder threw over the user's input
    """

class GeocoderQuotaExceeded(GeocoderError):
    """
    Too many requests.
    """
