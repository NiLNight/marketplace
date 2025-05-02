import logging
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.users.models import UserProfile
from apps.users.exceptions import UserServiceException

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Сериализатор для генерации JWT-токенов с дополнительными данными."""

    @classmethod
    def get_token(cls, user):
        logger.debug(f"Generating token for user {user.id}")
        token = super().get_token(user)
        token['is_active'] = user.is_active
        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя.

    Валидирует username, email и password.
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email уже зарегистрирован")]
    )
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def validate(self, data):
        """Проверяет данные для регистрации.

        Args:
            data: Данные для валидации.

        Returns:
            Проверенные данные.

        Raises:
            UserServiceException: Если данные некорректны.
        """
        logger.debug(f"Validating registration data: {data}")
        try:
            return data
        except Exception as e:
            logger.error(f"Validation error during registration: {str(e)}")
            raise UserServiceException(f"Ошибка валидации данных: {str(e)}")


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для аутентификации пользователя.

    Валидирует email и password.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        max_length=128,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        """Проверяет данные для входа.

        Args:
            data: Данные для валидации.

        Returns:
            Проверенные данные.

        Raises:
            UserServiceException: Если данные некорректны.
        """
        logger.debug(f"Validating login data: {data}")
        try:
            return data
        except Exception as e:
            logger.error(f"Validation error during login: {str(e)}")
            raise UserServiceException(f"Ошибка валидации данных: {str(e)}")


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя."""

    class Meta:
        model = UserProfile
        fields = ['public_id', 'phone', 'birth_date', 'avatar']
        read_only_fields = ['public_id']


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя с вложенным профилем."""
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['email']

    def validate(self, data):
        """Проверяет данные для обновления пользователя.

        Args:
            data: Данные для валидации.

        Returns:
            Проверенные данные.

        Raises:
            UserServiceException: Если данные некорректны.
        """
        logger.debug(f"Validating user data: {data}")
        try:
            return data
        except Exception as e:
            logger.error(f"Validation error during user update: {str(e)}")
            raise UserServiceException(f"Ошибка валидации данных: {str(e)}")


class PasswordResetSerializer(serializers.Serializer):
    """Сериализатор для запроса сброса пароля."""
    email = serializers.EmailField(required=True)

    def validate(self, data):
        """Проверяет email для сброса пароля.

        Args:
            data: Данные для валидации.

        Returns:
            Проверенные данные.

        Raises:
            UserServiceException: Если email некорректен.
        """
        logger.debug(f"Validating password reset data: {data}")
        try:
            return data
        except Exception as e:
            logger.error(f"Validation error during password reset: {str(e)}")
            raise UserServiceException(f"Ошибка валидации данных: {str(e)}")


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Сериализатор для подтверждения сброса пароля."""
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate(self, data):
        """Проверяет данные для сброса пароля.

        Args:
            data: Данные для валидации.

        Returns:
            Проверенные данные.

        Raises:
            UserServiceException: Если данные некорректны.
        """
        logger.debug(f"Validating password reset confirm data: {data}")
        try:
            return data
        except Exception as e:
            logger.error(f"Validation error during password reset confirm: {str(e)}")
            raise UserServiceException(f"Ошибка валидации данных: {str(e)}")
