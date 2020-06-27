import warnings

from geopy.geocoders.nominatim import Nominatim

__all__ = ("Nominatim",)

warnings.warn(
    "`geopy.geocoders.osm` module is deprecated. "
    "Use `geopy.geocoders.nominatim` instead. "
    "In geopy 3 this module will be removed.",
    DeprecationWarning,
    stacklevel=2,
)
