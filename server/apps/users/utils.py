from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings


def set_jwt_cookies(response, user, secure=False):
    refresh = RefreshToken.for_user(user)
    response.set_cookie(
        key=settings.SIMPLE_JWT["AUTH_COOKIE"],
        value=str(refresh.access_token),
        domain=settings.SIMPLE_JWT["AUTH_COOKIE_DOMAIN"],
        path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
        expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
        secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
        httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
        samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
    )
    return response
