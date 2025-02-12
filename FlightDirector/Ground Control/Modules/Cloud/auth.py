from google.oauth2 import service_account
import jwt

class AuthManager:
    """
    Handles authentication with GCP.
    Manages credentials and tokens.
    """
    def __init__(self, config: dict):
        self.config = config
        self.credentials = None
        self.token = None
        
    async def initialize(self):
        """Initialize authentication"""
        try:
            # Load service account credentials
            self.credentials = service_account.Credentials.from_service_account_file(
                self.config['credentials_path'],
                scopes=self.config['scopes']
            )
            
            # Get initial token
            await self.refresh_token()
            
        except Exception as e:
            raise AuthError(f"Authentication failed: {str(e)}")
            
    async def refresh_token(self):
        """Refresh authentication token"""
        try:
            if self.credentials.expired:
                self.credentials.refresh()
            self.token = self.credentials.token
            
        except Exception as e:
            raise AuthError(f"Token refresh failed: {str(e)}")
