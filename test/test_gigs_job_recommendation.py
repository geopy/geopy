import pytest
from unittest.mock import patch
from geopy.gigs_job_recommendation import GigsJobRecommendation


class TestGigsJobRecommendation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.recommender = GigsJobRecommendation()

    @patch("requests.get")
    def test__get_industries(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": ["IT", "Healthcare"]}
        industries = self.recommender._get_industries()
        assert industries == ["IT", "Healthcare"]

    @patch("requests.get")
    def test__get_industries_failure(self, mock_get):
        mock_get.return_value.status_code = 404
        industries = self.recommender._get_industries()
        assert industries == []

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

        assert jobs == [
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
        ]
