from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta


def set_jwt_cookies(response, user, secure=False):
    refresh = RefreshToken.for_user(user)
    response.set_cookie(
        key='access_token',
        value=str(refresh.access_token),
        httponly=True,
        secure=secure,
        samesite='Lax',
        max_age=timedelta(minutes=15)  # 15 минут
    )
    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        httponly=True,
        secure=secure,
        samesite='Lax',
        max_age=timedelta(days=1)  # 1 день
    )
    return response
