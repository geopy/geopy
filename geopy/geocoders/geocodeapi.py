from geopy.geocoders.base import Geocoder


__all__ = ('GeocodeAPI',)


class GeocodeAPI(Geocoder):
    """Geocoder using the Geocode API.

    Documentation at:
        https://geocodeapi.io/documentation/

    """
    base_api_url = 'https://app.geocodeapi.io/api/v1/'
    geocode_path = 'search'
    reverse_path = 'reverse'
