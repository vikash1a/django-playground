import requests
import json
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.conf import settings
from jose import jwt
import logging

logger = logging.getLogger(__name__)

class OktaBackend(BaseBackend):
    """
    Authentication backend for Okta SSO
    """
    
    def authenticate(self, request, token=None):
        if not token:
            return None
            
        try:
            # Verify the token with Okta
            okta_domain = settings.OKTA_DOMAIN
            jwks_url = f"https://{okta_domain}/oauth2/v1/keys"
            
            # Get the JWKS (JSON Web Key Set) from Okta
            jwks_response = requests.get(jwks_url)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()
            
            # Decode and verify the token
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break
            
            if rsa_key:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=settings.OKTA_CLIENT_ID,
                    issuer=f"https://{okta_domain}/oauth2/default"
                )
                
                # Extract user information from the token
                email = payload.get('email')
                if not email:
                    return None
                
                # Get or create user
                user, created = User.objects.get_or_create(
                    username=email,
                    defaults={
                        'email': email,
                        'first_name': payload.get('given_name', ''),
                        'last_name': payload.get('family_name', ''),
                    }
                )
                
                if created:
                    user.set_unusable_password()
                    user.save()
                
                return user
                
        except Exception as e:
            logger.error(f"Okta authentication error: {str(e)}")
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class GoogleBackend(BaseBackend):
    """
    Authentication backend for Google SSO
    """
    
    def authenticate(self, request, token=None):
        if not token:
            return None
            
        try:
            # Verify the token with Google
            google_verify_url = "https://oauth2.googleapis.com/tokeninfo"
            params = {'id_token': token}
            
            response = requests.get(google_verify_url, params=params)
            response.raise_for_status()
            
            payload = response.json()
            
            # Verify the token is for our application
            if payload.get('aud') != settings.GOOGLE_CLIENT_ID:
                return None
            
            email = payload.get('email')
            if not email:
                return None
            
            # Get or create user
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': payload.get('given_name', ''),
                    'last_name': payload.get('family_name', ''),
                }
            )
            
            if created:
                user.set_unusable_password()
                user.save()
            
            return user
            
        except Exception as e:
            logger.error(f"Google authentication error: {str(e)}")
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None 