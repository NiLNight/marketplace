"""
Views для работы с пользователями:
- Регистрация
- Авторизация
- Выход
- Профиль пользователя
"""

import random
import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import EmailVerified
from apps.users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer
)
from apps.users.utils import set_jwt_cookies
from apps.users.tasks import send_confirmation_email, send_password_reset_email
from django.contrib.auth.tokens import PasswordResetTokenGenerator

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
        user = serializer.save()  # Создаём пользователя
        # Не выдаем токен если пользователь неактивен
        if user.is_active:
            response = Response(status=status.HTTP_201_CREATED)
            return set_jwt_cookies(response, user)

        return Response(
            {"detail": "Требуется активация аккаунта"},
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
        user = serializer.validated_data['user']
        if not user.is_active:
            logger.error(f"User {user.email} неактивен")
            return Response({"error": "Аккаунт не активирован"}, status=403)

        response_data = {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        }
        response = Response(response_data)
        return set_jwt_cookies(response, user)


class UserLogoutView(APIView):
    """
    API view для выхода пользователя с инвалидацией токенов.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({"error": "Refresh token missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response({"error": f"Invalid token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        response = Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


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


class ResendCodeView(APIView):
    """
    API view для повторной отправки кода подтверждения.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email, is_active=False)
            # Генерация нового кода подтверждения
            code = str(random.randint(100000, 999999))
            # Обновляем запись EmailVerified для данного пользователя
            updated_count = EmailVerified.objects.filter(user=user).update(
                confirmation_code=code,
                code_created_at=timezone.now()
            )
            # Если запись не найдена – создаём её
            if not updated_count:
                EmailVerified.objects.create(
                    user=user,
                    confirmation_code=code,
                    code_created_at=timezone.now()
                )
            # Отправляем асинхронное письмо с кодом (передаём user.email)
            send_confirmation_email.delay(user.email, code)
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
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Неверный код или email'}, status=400)

        # Ищем EmailVerified с заданным кодом
        email_verified = EmailVerified.objects.filter(user=user, confirmation_code=code).first()
        if not email_verified:
            return Response({'error': 'Аккаунт активирован или код ещё не отправлен'}, status=400)

        time_diff = (timezone.now() - email_verified.code_created_at).total_seconds()
        if time_diff > 86400:  # 24 часа
            return Response({'error': 'Срок действия кода истек'}, status=400)

        # Подтверждаем аккаунт
        user.is_active = True
        user.save()
        # Очищаем код подтверждения
        email_verified.confirmation_code = None
        email_verified.save()
        return Response({'message': 'Аккаунт активирован'})


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
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = PasswordResetTokenGenerator().make_token(user)
            reset_url = f"http://localhost:8000/reset-password/?token={token}&uid={user.id}"
            # Отправляем асинхронное письмо
            send_password_reset_email.delay(user.email, reset_url)
        except User.DoesNotExist:
            pass
        return Response({"detail": "Если указанный email существует, на него отправлено письмо для сброса пароля."},
                        status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    API view для изменения пароля.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"detail": "Пароль успешно изменён."}, status=status.HTTP_200_OK)
