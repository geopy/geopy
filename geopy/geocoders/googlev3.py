import warnings

from geopy.geocoders.google import GoogleV3

__all__ = ("GoogleV3",)

warnings.warn(
    "`geopy.geocoders.googlev3` module is deprecated. "
    "Use `geopy.geocoders.google` instead. "
    "In geopy 3 this module will be removed.",
    DeprecationWarning,
    stacklevel=2,
)
