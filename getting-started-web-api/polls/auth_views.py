import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from oauth2_provider.models import AccessToken
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.views import TokenView
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_token(request):
    """
    Verify SSO token and authenticate user
    """
    token = request.data.get('token')
    provider = request.data.get('provider')  # 'okta' or 'google'
    
    if not token or not provider:
        return Response(
            {'error': 'Token and provider are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Authenticate using the appropriate backend
    if provider == 'okta':
        user = authenticate(request, token=token)
    elif provider == 'google':
        user = authenticate(request, token=token)
    else:
        return Response(
            {'error': 'Invalid provider'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if user:
        # Log the user in
        login(request, user)
        
        # Create or get OAuth2 access token
        application = oauth2_settings.DEFAULT_APPLICATION_MODEL.objects.first()
        if not application:
            # Create a default application if none exists
            from oauth2_provider.models import Application
            application = Application.objects.create(
                name="Default Application",
                client_type="confidential",
                authorization_grant_type="password",
                user=user
            )
        
        # Create access token
        expires = timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        access_token = AccessToken.objects.create(
            user=user,
            application=application,
            expires=expires,
            token=AccessToken.generate_token(),
            scope='read write'
        )
        
        return Response({
            'access_token': access_token.token,
            'token_type': 'Bearer',
            'expires_in': oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })
    else:
        return Response(
            {'error': 'Invalid token'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['POST'])
def logout_view(request):
    """
    Logout user and invalidate token
    """
    logout(request)
    return Response({'message': 'Logged out successfully'})

@api_view(['GET'])
def user_info(request):
    """
    Get current user information
    """
    if request.user.is_authenticated:
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        })
    else:
        return Response(
            {'error': 'Not authenticated'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def sso_config(request):
    """
    Return SSO configuration for frontend
    """
    return Response({
        'okta': {
            'domain': settings.OKTA_DOMAIN,
            'client_id': settings.OKTA_CLIENT_ID,
            'redirect_uri': settings.OKTA_REDIRECT_URI,
        },
        'google': {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        }
    }) 