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

class GeocoderServiceError(GeocoderError):
    """
    HTTP error code given by the remote service.
    """
    def __init__(self, http_status, message):
        self.http_status = http_status
        super(GeocoderServiceError, self).__init__(message)
