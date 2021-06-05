from ffplayout.settings.common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '---a-very-important-secret-key-_-generate-it-new---'
DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# REST API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

CORS_ORIGIN_WHITELIST = (
    'http://ffplayout.local',
    'http://127.0.0.1'
)
