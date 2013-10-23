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
