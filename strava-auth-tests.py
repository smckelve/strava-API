import unittest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
import json
from strava_authenticate import StravaAuth
from project import get_athlete_info

class TestStravaAuth(unittest.TestCase):
    def setUp(self) -> None:
        # Mock environment variables
        self.mock_env = patch.dict('os.environ', {
            'STRAVA_CLIENT_ID': 'test_client_id',
            'STRAVA_CLIENT_SECRET': 'test_client_secret'
        })
        self.mock_env.start()

        # Initialize StravaAuth instance
        self.auth = StravaAuth()

    def tearDown(self) -> None:
        self.mock_env.stop()

    @patch("builtins.open", new_callable=mock_open, read_data='{"access_token": "test_access", "refresh_token": "test_refresh", "expires_in": 3600, "timestamp": "2024-12-12T00:00:00"}')
    def test_load_tokens(self, mock_file):
        tokens = self.auth.load_tokens()
        self.assertEqual(tokens['access_token'], "test_access")
        self.assertEqual(tokens['refresh_token'], "test_refresh")

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_tokens(self, mock_json_dump, mock_file):
        token_data = {
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "expires_in": 3600
        }
        self.auth.save_tokens(token_data)

        # Check that the file was opened in write mode
        mock_file.assert_called_once_with('strava_tokens.json', 'w')

        # Check that the correct data was written
        written_data = mock_json_dump.call_args[0][0]
        self.assertIn('access_token', written_data)
        self.assertIn('timestamp', written_data)

    @patch("requests_oauthlib.OAuth2Session.post")
    @patch("strava_authenticate.StravaAuth.load_tokens", return_value = {"refresh_token": "test_refresh"})
    @patch("strava_authenticate.StravaAuth.save_tokens")
    def test_refresh_token(self, mock_save_tokens, mock_load_tokens, mock_post) -> None:
        # Mock the response from the token refresh endpoint
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value = {
                "access_token": "new_access",
                "refresh_token": "new_refresh",
                "expires_in": 3600
            }),
            status_code = 200
        )

        new_token = self.auth.refresh_token()

        # Validate the new token data
        self.assertEqual(new_token['access_token'], "new_access")
        self.assertEqual(new_token['refresh_token'], "new_refresh")

        # Ensure save_tokens was called with the new token
        mock_save_tokens.assert_called_once_with(new_token)

    @patch("strava_authenticate.StravaAuth.is_token_expired", return_value = True)
    @patch("strava_authenticate.StravaAuth.refresh_token")
    @patch("requests_oauthlib.OAuth2Session.get")
    def test_get_athlete_info_refresh(self, mock_get, mock_refresh_token, mock_is_token_expired) -> None:
        # Mock the refreshed token response
        mock_refresh_token.return_value = {"access_token": "new_access"}

        # Mock the athlete API response
        mock_get.return_value = MagicMock(
            status_code = 200,
            reason = "OK",
            text = json.dumps({"firstname": "Test", "lastname": "User"})
        )

        status_code, reason, athlete_info = get_athlete_info(self.auth)

        self.assertEqual(status_code, 200)
        self.assertEqual(reason, "OK")
        self.assertEqual(athlete_info['firstname'], "Test")
        self.assertEqual(athlete_info['lastname'], "User")

    @patch("strava_authenticate.StravaAuth.is_token_expired", return_value=False)
    @patch("requests_oauthlib.OAuth2Session.get")
    def test_get_athlete_info_valid_token(self, mock_get, mock_is_token_expired) -> None:
        # Mock the athlete API response
        mock_get.return_value = MagicMock(
            status_code = 200,
            reason = "OK",
            text = json.dumps({"firstname": "Valid", "lastname": "Token"})
        )

        status_code, reason, athlete_info = get_athlete_info(self.auth)

        self.assertEqual(status_code, 200)
        self.assertEqual(reason, "OK")
        self.assertEqual(athlete_info['firstname'], "Valid")
        self.assertEqual(athlete_info['lastname'], "Token")

    @patch("strava_authenticate.StravaAuth.load_tokens", return_value=None)
    def test_is_token_expired_no_token(self, mock_load_tokens):
        self.assertTrue(self.auth.is_token_expired())

    @patch("strava_authenticate.StravaAuth.load_tokens", return_value={
        "timestamp": (datetime.now() - timedelta(hours = 2)).isoformat(),
        "expires_in": 3600
    })
    def test_is_token_expired_expired_token(self, mock_load_tokens):
        self.assertTrue(self.auth.is_token_expired())

    @patch("strava_authenticate.StravaAuth.load_tokens", return_value={
        "timestamp": (datetime.now() - timedelta(minutes = 30)).isoformat(),
        "expires_in": 3600
    })
    def test_is_token_expired_valid_token(self, mock_load_tokens):
        self.assertFalse(self.auth.is_token_expired())

if __name__ == "__main__":
    unittest.main()
