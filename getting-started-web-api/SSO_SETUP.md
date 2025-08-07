# Django SSO Authentication Setup

This guide will help you set up Single Sign-On (SSO) authentication with Okta and Google for your Django application.

## Features

- ✅ Okta SSO integration
- ✅ Google SSO integration  
- ✅ JWT token verification
- ✅ Automatic user creation
- ✅ OAuth2 access tokens
- ✅ CORS support for frontend integration
- ✅ REST API endpoints

## Prerequisites

- Python 3.8+
- Django 4.2+
- Okta Developer Account
- Google Cloud Console Account

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Create a superuser (optional):**
```bash
python manage.py createsuperuser
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Okta Configuration
OKTA_DOMAIN=your-okta-domain.okta.com
OKTA_CLIENT_ID=your-okta-client-id
OKTA_CLIENT_SECRET=your-okta-client-secret
OKTA_REDIRECT_URI=http://localhost:8000/auth/okta/callback/

# Google Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback/
```

### Okta Setup

1. **Create an Okta Developer Account:**
   - Go to [Okta Developer](https://developer.okta.com/)
   - Sign up for a free account

2. **Create an Application:**
   - Navigate to Applications → Applications
   - Click "Create App Integration"
   - Choose "OIDC - OpenID Connect"
   - Choose "Single-page application"
   - Name your application (e.g., "Django SSO App")

3. **Configure the Application:**
   - **Base URIs:** `http://localhost:3000`
   - **Redirect URIs:** `http://localhost:3000/callback`
   - **Logout redirect URIs:** `http://localhost:3000`

4. **Get Credentials:**
   - Copy the Client ID from the application settings
   - Note your Okta domain (e.g., `dev-123456.okta.com`)

### Google Setup

1. **Create a Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Google+ API:**
   - Go to APIs & Services → Library
   - Search for "Google+ API" and enable it

3. **Create OAuth 2.0 Credentials:**
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Add authorized redirect URIs: `http://localhost:3000/callback`

4. **Get Credentials:**
   - Copy the Client ID and Client Secret

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/polls/auth/verify-token/` | POST | Verify SSO token and authenticate user |
| `/polls/auth/logout/` | POST | Logout user and invalidate token |
| `/polls/auth/user-info/` | GET | Get current user information |
| `/polls/auth/sso-config/` | GET | Get SSO configuration for frontend |

### Example Usage

#### Verify Token
```bash
curl -X POST http://localhost:8000/polls/auth/verify-token/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your-jwt-token",
    "provider": "okta"
  }'
```

#### Get User Info
```bash
curl -X GET http://localhost:8000/polls/auth/user-info/ \
  -H "Authorization: Bearer your-access-token"
```

## Frontend Integration

### React Example

```jsx
import React, { useState, useEffect } from 'react';

const SSOLogin = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  const loginWithOkta = () => {
    const oktaAuth = new OktaAuth({
      issuer: `https://${process.env.REACT_APP_OKTA_DOMAIN}/oauth2/default`,
      clientId: process.env.REACT_APP_OKTA_CLIENT_ID,
      redirectUri: window.location.origin + '/callback',
      scopes: ['openid', 'profile', 'email']
    });
    oktaAuth.signInWithRedirect();
  };

  const loginWithGoogle = () => {
    const googleAuthUrl = 'https://accounts.google.com/o/oauth2/v2/auth';
    const params = new URLSearchParams({
      client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID,
      redirect_uri: window.location.origin + '/callback',
      response_type: 'id_token',
      scope: 'openid email profile',
      nonce: Math.random().toString(36).substring(2, 15)
    });
    window.location.href = `${googleAuthUrl}?${params.toString()}`;
  };

  const verifyToken = async (token, provider) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/polls/auth/verify-token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, provider })
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        setUser(data.user);
      }
    } catch (error) {
      console.error('Authentication error:', error);
    }
    setLoading(false);
  };

  const logout = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      await fetch('http://localhost:8000/polls/auth/logout/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    }
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <div>
      {!user ? (
        <div>
          <button onClick={loginWithOkta} disabled={loading}>
            Login with Okta
          </button>
          <button onClick={loginWithGoogle} disabled={loading}>
            Login with Google
          </button>
        </div>
      ) : (
        <div>
          <h2>Welcome, {user.first_name}!</h2>
          <p>Email: {user.email}</p>
          <button onClick={logout}>Logout</button>
        </div>
      )}
    </div>
  );
};

export default SSOLogin;
```

### Vue.js Example

```vue
<template>
  <div>
    <div v-if="!user">
      <button @click="loginWithOkta" :disabled="loading">
        Login with Okta
      </button>
      <button @click="loginWithGoogle" :disabled="loading">
        Login with Google
      </button>
    </div>
    <div v-else>
      <h2>Welcome, {{ user.first_name }}!</h2>
      <p>Email: {{ user.email }}</p>
      <button @click="logout">Logout</button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      user: null,
      loading: false
    }
  },
  methods: {
    loginWithOkta() {
      const oktaAuth = new OktaAuth({
        issuer: `https://${process.env.VUE_APP_OKTA_DOMAIN}/oauth2/default`,
        clientId: process.env.VUE_APP_OKTA_CLIENT_ID,
        redirectUri: window.location.origin + '/callback',
        scopes: ['openid', 'profile', 'email']
      });
      oktaAuth.signInWithRedirect();
    },
    
    loginWithGoogle() {
      const googleAuthUrl = 'https://accounts.google.com/o/oauth2/v2/auth';
      const params = new URLSearchParams({
        client_id: process.env.VUE_APP_GOOGLE_CLIENT_ID,
        redirect_uri: window.location.origin + '/callback',
        response_type: 'id_token',
        scope: 'openid email profile',
        nonce: Math.random().toString(36).substring(2, 15)
      });
      window.location.href = `${googleAuthUrl}?${params.toString()}`;
    },
    
    async verifyToken(token, provider) {
      this.loading = true;
      try {
        const response = await fetch('http://localhost:8000/polls/auth/verify-token/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token, provider })
        });
        const data = await response.json();
        if (response.ok) {
          localStorage.setItem('access_token', data.access_token);
          this.user = data.user;
        }
      } catch (error) {
        console.error('Authentication error:', error);
      }
      this.loading = false;
    },
    
    async logout() {
      const token = localStorage.getItem('access_token');
      if (token) {
        await fetch('http://localhost:8000/polls/auth/logout/', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      }
      localStorage.removeItem('access_token');
      this.user = null;
    }
  }
}
</script>
```

## Security Considerations

1. **Environment Variables:** Never commit sensitive credentials to version control
2. **HTTPS:** Use HTTPS in production for all OAuth redirects
3. **Token Validation:** Always verify tokens on the server side
4. **CORS:** Configure CORS properly for your frontend domains
5. **Session Management:** Implement proper session timeout and cleanup

## Troubleshooting

### Common Issues

1. **CORS Errors:**
   - Ensure your frontend domain is in `CORS_ALLOWED_ORIGINS`
   - Check that `CORS_ALLOW_CREDENTIALS = True`

2. **Token Verification Fails:**
   - Verify your OAuth provider credentials
   - Check that redirect URIs match exactly
   - Ensure JWT tokens are properly formatted

3. **User Not Created:**
   - Check Django logs for authentication errors
   - Verify email field is present in JWT token
   - Ensure authentication backends are properly configured

### Debug Mode

Enable debug logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'polls.auth_backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Production Deployment

1. **Update Settings:**
   - Set `DEBUG = False`
   - Configure proper `ALLOWED_HOSTS`
   - Use environment variables for all secrets

2. **HTTPS:**
   - Configure SSL certificates
   - Update redirect URIs to use HTTPS

3. **Database:**
   - Use PostgreSQL or MySQL instead of SQLite
   - Configure proper database credentials

4. **Static Files:**
   - Configure static file serving
   - Use CDN for better performance

## Support

For issues and questions:
- Check Django logs for detailed error messages
- Verify OAuth provider configuration
- Test with the provided frontend example
- Review security best practices for OAuth implementation 