import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class GoogleAuthHandler:
    def __init__(self, client_secrets_file='auth/client_secrets.json', token_file='auth/token.pickle'):
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self.scopes = ['https://www.googleapis.com/auth/photoslibrary',
                      'https://www.googleapis.com/auth/photoslibrary.readonly']
        
    def get_credentials(self):
        """Get valid credentials for Google Photos API."""
        credentials = None

        # Try to load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                credentials = pickle.load(token)

        # If there are no valid credentials available, authenticate
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    credentials = self._authenticate()
            else:
                credentials = self._authenticate()

            # Save the credentials for future use
            with open(self.token_file, 'wb') as token:
                pickle.dump(credentials, token)

        return credentials

    def _authenticate(self):
        """Authenticate using OAuth 2.0."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file, self.scopes)
            credentials = flow.run_local_server(port=0)
            return credentials
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

    def revoke_credentials(self):
        """Revoke the current credentials."""
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            return True
        return False 