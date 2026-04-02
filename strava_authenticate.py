from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import os
import json
from typing import Dict, Tuple, Any
from datetime import datetime, timedelta

class StravaAuth:
    """Handles OAuth2 authentication flow for Strava API."""
    
    def __init__(self):
        """Initialize Strava authentication with environment variables."""
        load_dotenv()
        
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.redirect_url = "https://localhost"
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Missing STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET in environment variables")
        
        self.token_url = "https://www.strava.com/api/v3/oauth/token"
        self.auth_base_url = "https://www.strava.com/oauth/authorize"
        self.scope = "profile:read_all,activity:read_all"
        
        # Load existing tokens if available
        self.token = self.load_tokens()
        
        self.session = OAuth2Session(
            client_id=self.client_id,
            redirect_uri=self.redirect_url,
            scope=self.scope,
            token=self.token
        )

    def load_tokens(self) -> Dict[str, Any]:
        """Load tokens from file if they exist."""
        try:
            with open('strava_tokens.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_tokens(self, token: Dict[str, Any]) -> None:
        """Save tokens to file with timestamp."""
        token_data = {
            **token,
            'timestamp': datetime.now().isoformat()
        }
        with open('strava_tokens.json', 'w') as f:
            json.dump(token_data, f, indent=4)
        print("\nTokens have been saved to 'strava_tokens.json'")

    def refresh_token(self) -> Dict[str, Any]:
        """Refresh the access token using the refresh token."""
        try:
            stored_tokens = self.load_tokens()
            if not stored_tokens or 'refresh_token' not in stored_tokens:
                raise ValueError("No refresh token available. Please re-authenticate.")

            print("\nRefreshing access token...")
            
            refresh_params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': stored_tokens['refresh_token']
            }

            response = self.session.post(self.token_url, data=refresh_params)
            new_tokens = response.json()

            if 'errors' in new_tokens or 'access_token' not in new_tokens:
                raise ValueError(f"Token refresh failed: {new_tokens.get('message', 'Unknown error')}")

            self.save_tokens(new_tokens)
            self.session.token = new_tokens
            
            print("Token refresh successful!")
            return new_tokens

        except Exception as e:
            raise Exception(f"Token refresh failed: {str(e)}")

    def is_token_expired(self) -> bool:
        """Check if the current access token is expired or close to expiring."""
        stored_tokens = self.load_tokens()
        if not stored_tokens:
            return True
            
        # Get token timestamp
        timestamp = datetime.fromisoformat(stored_tokens.get('timestamp', '2000-01-01'))
        expires_in = stored_tokens.get('expires_in', 0)
        
        # Check if token has expired or will expire in next 5 minutes
        expiration_time = timestamp + timedelta(seconds=expires_in)
        return datetime.now() + timedelta(minutes=5) >= expiration_time

    def get_authorization_link(self) -> str:
        """Generate the authorization URL for user authentication."""
        auth_link, _ = self.session.authorization_url(self.auth_base_url)
        return auth_link

    def authenticate(self, redirect_response: str) -> Dict[str, Any]:
        """Complete OAuth flow and return session token."""
        try:
            if not redirect_response.startswith('http'):
                redirect_response = 'http://' + redirect_response.lstrip('/')
            
            token = self.session.fetch_token(
                token_url=self.token_url,
                client_id=self.client_id,
                client_secret=self.client_secret,
                authorization_response=redirect_response,
                include_client_id=True
            )
            self.save_tokens(token)
            return token
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
