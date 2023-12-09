import base64
import requests
import unittest
from geopy.geocoders import Nominatim
from unittest.mock import patch


class GigsJobRecommendation:
    """
    A class used to recommend jobs based on location and other parameters.

    ...

    Attributes
    ----------
    BASE_URL : str
        a formatted string that defines the base URL for the Gigs API
    geolocator : Geolocator object
        a Geolocator object used to geocode addresses
    industries : list
        a list of industries fetched from the Gigs API

    Methods
    -------
    recommend_jobs(address, radius=8047, min_pay=None, industry=None)
        Returns a dictionary containing the geocoded location and a list of nearby jobs.
    """

    def __init__(self, geolocator=None):
        """
        Constructs all the necessary attributes for the GigsJobRecommendation object.

        Parameters
        ----------
        geolocator : Geolocator, optional
            a Geolocator object
            (default is Nominatim with user_agent="gigs_job_recommender")
        """
        self.BASE_URL = "https://getgigs.co/api"
        self.geolocator = geolocator or Nominatim(user_agent="gigs_job_recommender")

        self.industries = self._get_industries()

    def recommend_jobs(self, address, radius=8047, min_pay=None, industry=None):
        """
        Returns a dictionary containing the geocoded location and a list of nearby jobs.

        Parameters
        ----------
        address : str
            the address to geocode and search for jobs around
        radius : int, optional
            the radius around the address to search for jobs (default is 8047)
        min_pay : int, optional
            the minimum pay for the jobs to recommend (default is None)
        industry : str, optional
            the industry of the jobs to recommend (default is None)

        Returns
        -------
        dict
            a dictionary containing the geocoded location and a list of nearby jobs
        """
        location = self.geolocator.geocode(address)
        if not location:
            return None

        encoded_crd = self._encode_coordinates(
            lat=location.latitude, lon=location.longitude
        )

        jobs = self._get_nearby_jobs(encoded_crd, radius, min_pay, industry)
        return {"location": location, "jobs": jobs}

    def _encode_coordinates(self, lat, lon):
        """
        Returns a base64 encoded string of the latitude and longitude.

        Parameters
        ----------
        lat : float
            the latitude to encode
        lon : float
            the longitude to encode

        Returns
        -------
        str
            a base64 encoded string of the latitude and longitude
        """
        crd_str = f"{lat}:{lon}"
        encoded_crd = base64.b64encode(crd_str.encode()).decode()
        return encoded_crd

    def _get_nearby_jobs(self, encoded_crd, radius, min_pay, industry):
        """
        Returns a list of nearby jobs fetched from the Gigs API.

        Parameters
        ----------
        encoded_crd : str
            a base64 encoded string of the latitude and longitude
        radius : int
            the radius around the address to search for jobs
        min_pay : int, optional
            the minimum pay for the jobs to recommend (default is None)
        industry : str, optional
            the industry of the jobs to recommend (default is None)

        Returns
        -------
        list
            a list of nearby jobs fetched from the Gigs API
        """
        gigs_api_url = f"{self.BASE_URL}/search"
        params = {"crd": encoded_crd, "radius": radius}
        if min_pay:
            params["min_pay"] = min_pay
        if industry and industry in self.industries:
            params["industry"] = industry

        response = requests.get(gigs_api_url, params=params)
        if response.status_code == 200:
            return self._parse_job_data(response.json())
        else:
            return "Error fetching job listings"

    def _parse_job_data(self, json_data):
        """
        Returns a list of job information dictionaries parsed from the JSON data.

        Parameters
        ----------
        json_data : dict
            a dictionary containing the JSON data fetched from the Gigs API

        Returns
        -------
        list
            a list of job information dictionaries parsed from the JSON data
        """
        jobs = []
        for job in json_data.get("data", []):
            job_info = {
                "title": job.get("title"),
                "company": job.get("company", {}).get("name"),
                "min_pay": job.get("min_pay"),
                "max_pay": job.get("max_pay"),
                "location": f"{job.get('city')}, {job.get('state')}",
                "zipcode": job.get("zipcode"),
                "posted_date": job.get("posted_date"),
                "application_url": job.get("application_url"),
                "requirements": job.get("requirements"),
            }
            jobs.append(job_info)
        return jobs

    def _get_industries(self):
        """
        Returns a list of industries fetched from the Gigs API.

        Returns
        -------
        list
            a list of industries fetched from the Gigs API
        """
        industries_url = f"{self.BASE_URL}/industries"
        response = requests.get(industries_url)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            return []


# Usage Example
# recommender = GigsJobRecommendation()
# result = recommender.recommend_jobs("1600 Amphitheatre Parkway, Mountain View, CA")
# print(result)


class TestGigsJobRecommendation(unittest.TestCase):
    def setUp(self):
        self.recommender = GigsJobRecommendation()

    @patch("requests.get")
    def test__get_industries(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": ["IT", "Healthcare"]}
        industries = self.recommender._get_industries()
        self.assertEqual(industries, ["IT", "Healthcare"])

    @patch("requests.get")
    def test__get_industries_failure(self, mock_get):
        mock_get.return_value.status_code = 404
        industries = self.recommender._get_industries()
        self.assertEqual(industries, [])

    @patch("requests.get")
    def test_recommend_jobs(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [
                {
                    "title": "Software Engineer",
                    "company": {"name": "Google"},
                    "min_pay": 100000,
                    "max_pay": 150000,
                    "city": "Mountain View",
                    "state": "CA",
                    "zipcode": "94043",
                    "posted_date": "2023-12-09",
                    "application_url": "https://google.com",
                    "requirements": "Python, Java",
                }
            ]
        }

        jobs = self.recommender.recommend_jobs(
            "1600 Amphitheatre Parkway, Mountain View, CA"
        )["jobs"]

        self.assertEqual(
            jobs,
            [
                {
                    "title": "Software Engineer",
                    "company": "Google",
                    "min_pay": 100000,
                    "max_pay": 150000,
                    "location": "Mountain View, CA",
                    "zipcode": "94043",
                    "posted_date": "2023-12-09",
                    "application_url": "https://google.com",
                    "requirements": "Python, Java",
                }
            ],
        )
