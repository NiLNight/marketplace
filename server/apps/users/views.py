"""
Views для работы с пользователями:
- Регистрация
- Авторизация
- Выход
- Профиль пользователя
"""

import logging
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer
)
from apps.users.services.utils import set_jwt_cookies
from apps.users.services.users_services import UserService, ConfirmPasswordService, ConfirmCodeService
from apps.wishlists.services.wishlist_services import WishlistService
from config import settings
from apps.carts.services.cart_services import CartService

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRegistrationView(APIView):
    """
    API view для регистрации нового пользователя с установкой JWT в cookies.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.register_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )  # Создаём пользователя

        # Не выдаем токен если пользователь неактивен
        if user.is_active:
            response = Response(status=status.HTTP_201_CREATED)
            return set_jwt_cookies(response, user)

        return Response(
            {"detail": "Требуется активация аккаунта. Код подтверждения отправлен на ваш email."},
            status=status.HTTP_201_CREATED
        )


class UserLoginView(APIView):
    """
    API view для аутентификации пользователя с возвратом JWT в cookies.
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            user = UserService.login_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
            )
            if not user.is_active:
                return Response(
                    {"error": "Требуется активация аккаунта"},
                    status=status.HTTP_403_FORBIDDEN
                )
            response_data = {
                "message": "Login successful",
                "user": {"id": user.id, "username": user.username, "email": user.email}
            }
            response = Response(response_data)
            if request.session.get('cart'):
                CartService.merge_cart_on_login(user, request.session['cart'])
                del request.session['cart']  # Очистка корзины в сессии
            if request.session.get('wishlist'):  # Слияние списка желаний
                WishlistService.merge_wishlist_on_login(user, request.session['wishlist'])
                del request.session['wishlist']  # Очистка списка желаний из сессии
            return set_jwt_cookies(response, user)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"error": "Произошла ошибка при входе"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLogoutView(APIView):
    """
    API view для выхода пользователя с инвалидацией токенов.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        try:
            UserService.logout_user(refresh_token)
            response = Response({"message": "Выход успешно выполнен"}, status=status.HTTP_200_OK)
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])  # Удаляем access_token
            response.delete_cookie(settings.SIMPLE_JWT['REFRESH_COOKIE'])  # Удаляем refresh_token, если используется
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    API view для получения и обновления профиля пользователя.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# Активация аккаунта

class ResendCodeView(APIView):
    """
    API view для повторной отправки кода подтверждения.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            ConfirmCodeService.resend_confirmation_code(email)
            return Response({"message": "Новый код отправлен"})
        except User.DoesNotExist:
            return Response({"error": "Аккаунт не найден или активирован"}, status=status.HTTP_400_BAD_REQUEST)


class ConfirmView(APIView):
    """
    API view для подтверждения регистрации пользователя.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        try:
            ConfirmCodeService.confirm_account(email=email, code=code)
            return Response({'message': 'Аккаунт активирован'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Сброс пароля

class PasswordResetRequestView(APIView):
    """
    API view для отправки запроса на восстановление пароля.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            ConfirmPasswordService.request_password_reset(serializer.validated_data['email'])
            return Response({"detail": "Если указанный email существует, на него отправлено письмо."},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class PasswordResetConfirmView(APIView):
    """
    API view для изменения пароля.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            ConfirmPasswordService.confirm_password_reset(
                uid=serializer.validated_data['uid'],
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password'],
            )
            return Response({"detail": "Пароль успешно изменён."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
