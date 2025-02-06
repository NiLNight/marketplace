"""
Views для работы с пользователями:
- Регистрация
- Авторизация
- Выход
- Профиль пользователя
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import UserProfile
from apps.users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer
)
from apps.users.utils import set_jwt_cookies

User = get_user_model()


class UserRegistrationView(APIView):
    """
    API view для регистрации нового пользователя с установкой JWT в cookies.

    Этот класс предоставляет метод POST для выполнения регистрации нового пользователя.
    В процессе регистрации выполняется валидация данных, создание пользователя и установка JWT токенов в cookies.

    Attributes:
        serializer_class (class): Класс сериализатора, используемый для валидации данных регистрации.
    """

    serializer_class = UserRegistrationSerializer

    def post(self, request):
        """
        Регистрация нового пользователя.

        Этот метод выполняет следующие шаги:
        1. Валидация данных регистрации.
        2. Создание нового пользователя.
        3. Установка JWT токенов в cookies.

        Args:
            request (Request): Объект запроса Django.

        Returns:
            Response: Объект ответа Django Rest Framework с данными нового пользователя и статусом 201 Created.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()  # Используем метод save() сериализатора для создания пользователя
        response_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }

        response = Response(response_data, status=status.HTTP_201_CREATED)
        return set_jwt_cookies(response, user)


class UserLoginView(APIView):
    """
    API view для аутентификации пользователя с возвратом JWT в cookies.

    Этот класс предоставляет метод POST для выполнения аутентификации пользователя.
    В процессе аутентификации проверяются учетные данные, генерируются новые токены и обновляются cookies.

    Attributes:
        serializer_class (class): Класс сериализатора, используемый для валидации данных аутентификации.
    """

    serializer_class = UserLoginSerializer

    def post(self, request):
        """
        Аутентификация пользователя.

        Этот метод выполняет следующие шаги:
        1. Проверка учетных данных пользователя.
        2. Генерация новых JWT токенов.
        3. Обновление cookies с новыми токенами.

        Args:
            request (Request): Объект запроса Django.

        Returns:
            Response: Объект ответа Django Rest Framework с сообщением об успешной аутентификации и данными пользователя.
        """
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        response_data = {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }

        response = Response(response_data)
        return set_jwt_cookies(response, user)


class UserLogoutView(APIView):
    """
    API view для выхода пользователя с инвалидацией токенов.

    Этот класс предоставляет метод POST для выполнения выхода пользователя из системы.
    В процессе выхода refresh токен добавляется в черный список, а cookies очищаются.

    Attributes:
        permission_classes (list): Список классов разрешений, требуемых для доступа к этому представлению.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Выход пользователя из системы.

        Этот метод выполняет следующие шаги:
        1. Извлечение refresh токена из cookies.
        2. Добавление refresh токена в черный список.
        3. Очистка cookies (access_token и refresh_token).

        Args:
            request (Request): Объект запроса Django.

        Returns:
            Response: Объект ответа Django Rest Framework с сообщением об успешном выходе или ошибке.
        """
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {"error": "Refresh token missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response(
                {"error": f"Invalid token: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = Response(
            {"message": "Successfully logged out"},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


class UserProfileView(APIView):
    """
    API view для получения и обновления профиля пользователя.

    Этот класс предоставляет два основных метода:
    - GET: Получение профиля текущего пользователя.
    - PATCH: Частичное обновление профиля пользователя.

    Attributes:
        permission_classes (list): Список классов разрешений, требуемых для доступа к этому представлению.
        serializer_class (class): Класс сериализатора, используемый для валидации и сериализации данных профиля.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        """
        Получение профиля текущего пользователя.

        Этот метод возвращает сериализованные данные профиля пользователя,
        ассоциированного с текущим аутентифицированным пользователем.
        Если профиль не существует, он будет создан автоматически.

        Args:
            request (Request): Объект запроса Django.

        Returns:
            Response: Объект ответа Django Rest Framework, содержащий сериализованные данные профиля.
        """
        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    def patch(self, request):
        """
        Обновление профиля пользователя.

        Этот метод позволяет обновить данные профиля пользователя,
        ассоциированного с текущим аутентифицированным пользователем.
        Обновление выполняется на основе данных, переданных в теле запроса.

        Args:
            request (Request): Объект запроса Django.

        Returns:
            Response: Объект ответа Django Rest Framework, содержащий обновленные сериализованные данные профиля.
        """
        user = request.user
        serializer = self.serializer_class(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
