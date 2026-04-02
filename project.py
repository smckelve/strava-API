import json
from typing import Dict, Tuple, Any
from strava_authenticate import StravaAuth

def get_athlete_info(strava: StravaAuth) -> Tuple[int, str, Dict[str, Any]]:
    """Fetch authenticated athlete's information."""
    try:
        # Check if token needs refresh
        if strava.is_token_expired():
            strava.refresh_token()
                
        response = strava.session.get("https://www.strava.com/api/v3/athlete")
        return (
            response.status_code,
            response.reason,
            json.loads(response.text) if response.status_code == 200 else {}
        )
    except Exception as e:
        raise Exception(f"Failed to fetch athlete info: {str(e)}")

def display_token_info(token: Dict[str, Any]) -> None:
    """Display token information in a clear, formatted way."""
    print("\n=== Token Information ===")
    print(f"Access Token: {token.get('access_token')}")
    print(f"Refresh Token: {token.get('refresh_token')}")
    print(f"Token Type: {token.get('token_type')}")
    print(f"Expires In: {token.get('expires_in')} seconds")

def main():
    """Main program execution flow."""
    try:
        # Initialize authentication
        strava = StravaAuth()
        
        # Check for existing valid tokens
        if strava.token and not strava.is_token_expired():
            print("\nExisting valid token found!")
            display_token_info(strava.token)
            
            # Ask if user wants to refresh anyway
            if input("\nWould you like to refresh the token anyway? (y/n): ").lower() == 'y':
                new_token = strava.refresh_token()
                display_token_info(new_token)
        else:
            # Get and display authorization link
            auth_link = strava.get_authorization_link()
            print("\nAuthorize your Strava account:")
            print(f"Click Here: {auth_link}\n")
            
            # Get redirect URL from user
            print("After authorizing, you'll be redirected to a URL that starts with 'http://localhost'")
            print("Copy the ENTIRE URL from your browser's address bar")
            redirect_response = input("Paste the complete redirect URL here: ")
            
            # Complete authentication
            token = strava.authenticate(redirect_response)
            display_token_info(token)
        
        # Fetch athlete information
        status_code, reason, athlete_info = get_athlete_info(strava)
        
        # Display results
        print("\nAPI Response:")
        print(f"Status Code: {status_code}")
        print(f"Status: {reason}")
        
        if status_code == 200:
            print("\nAthlete Information:")
            print(f"Name: {athlete_info.get('firstname', '')} {athlete_info.get('lastname', '')}")
            print(f"City: {athlete_info.get('city', 'N/A')}")
            print(f"Country: {athlete_info.get('country', 'N/A')}")
            print(f"Profile: {athlete_info.get('profile', 'N/A')}")
        else:
            print(f"\nError retrieving athlete information: {athlete_info}")

    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()