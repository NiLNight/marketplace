from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.users.models import UserProfile
from apps.users.exceptions import InvalidUserData
from apps.users.services.users_services import UserService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Сериализатор для получения JWT-токенов.

    Добавляет информацию о статусе активности пользователя в токен.

    Attributes:
        user (User): Пользователь, для которого генерируется токен.
    """

    @classmethod
    def get_token(cls, user):
        """Генерирует JWT-токен с дополнительной информацией.

        Args:
            cls: Класс сериализатора.
            user (User): Пользователь, для которого генерируется токен.

        Returns:
            Token: Сгенерированный токен с дополнительной информацией.
        """
        logger.info(f"Generating token for user={user.id}")
        token = super().get_token(user)
        token['is_active'] = user.is_active
        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя.

    Преобразует данные для создания нового пользователя, включая имя, email и пароль.
    Используется в API для обработки запросов на регистрацию.

    Attributes:
        email (EmailField): Уникальный адрес электронной почты пользователя.
        password (CharField): Пароль пользователя.
        username (CharField): Имя пользователя.
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
        help_text='Уникальный адрес электронной почты пользователя.'
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text='Пароль пользователя.'
    )
    username = serializers.CharField(
        max_length=15,
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
        help_text='Имя пользователя.'
    )

    class Meta:
        """Метаданные сериализатора UserRegistrationSerializer."""
        model = User
        fields = ['username', 'email', 'password']
        read_only_fields = []

    def validate(self, attrs):
        """Проверка корректности данных перед регистрацией.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        logger.info(f"Validating registration data for email={attrs.get('email')}")
        return attrs


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для аутентификации пользователя.

    Обрабатывает данные для входа пользователя, включая email и пароль.
    Используется в API для обработки запросов на вход.

    Attributes:
        email (EmailField): Адрес электронной почты пользователя.
        password (CharField): Пароль пользователя.
    """
    email = serializers.EmailField(
        required=True,
        help_text='Адрес электронной почты пользователя.'
    )
    password = serializers.CharField(
        max_length=128,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Пароль пользователя.'
    )

    class Meta:
        """Метаданные сериализатора UserLoginSerializer."""
        fields = ['email', 'password']

    def validate(self, attrs):
        """Проверка корректности данных для входа.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        logger.info(f"Validating login data for email={attrs.get('email')}")
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя.

    Преобразует данные профиля пользователя, включая публичный ID, телефон, дату рождения и аватар.
    Используется в API для отображения и обновления профиля.

    Attributes:
        public_id (CharField): Уникальный публичный идентификатор профиля.
        phone (CharField): Номер телефона пользователя.
        birth_date (DateField): Дата рождения пользователя.
        avatar (ImageField): Аватар пользователя.
    """
    public_id = serializers.CharField(
        read_only=True,
        help_text='Уникальный публичный идентификатор профиля.'
    )
    phone = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text='Номер телефона пользователя.'
    )
    birth_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text='Дата рождения пользователя.'
    )
    avatar = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text='Аватар пользователя.'
    )

    class Meta:
        """Метаданные сериализатора UserProfileSerializer."""
        model = UserProfile
        fields = ['public_id', 'phone', 'birth_date', 'avatar']
        read_only_fields = ['public_id']

    def validate(self, attrs):
        """Проверка корректности данных профиля.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        logger.info(f"Validating profile data for user={self.instance.user.id if self.instance else 'new'}")
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя с вложенным профилем.

    Преобразует данные пользователя и его профиля для API-ответов.
    Используется для отображения и обновления информации о пользователе.

    Attributes:
        profile (UserProfileSerializer): Данные профиля пользователя.
        username (CharField): Имя пользователя.
        email (EmailField): Адрес электронной почты пользователя.
        first_name (CharField): Имя пользователя.
        last_name (CharField): Фамилия пользователя.
    """
    profile = UserProfileSerializer(
        required=False,
        help_text='Данные профиля пользователя.'
    )
    username = serializers.CharField(
        help_text='Имя пользователя.'
    )
    email = serializers.EmailField(
        read_only=True,
        help_text='Адрес электронной почты пользователя.'
    )
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Имя пользователя.'
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Фамилия пользователя.'
    )

    class Meta:
        """Метаданные сериализатора UserSerializer."""
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['email']

    def validate(self, attrs):
        """Проверка корректности данных пользователя.

        Проверяет уникальность username при обновлении.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если username уже занят другим пользователем.
        """
        logger.info(f"Validating user data for user={self.instance.id if self.instance else 'new'}")
        username = attrs.get('username')
        if username and self.instance:
            # Проверяем уникальность имени пользователя, исключая текущего пользователя
            if User.objects.exclude(id=self.instance.id).filter(username=username).exists():
                logger.warning(f"Username {username} already taken for user={self.instance.id}")
                raise serializers.ValidationError({"username": "Имя пользователя уже занято."})
        return attrs

    def update(self, instance, validated_data):
        """Обновляет пользователя и его профиль.

        Args:
            instance (User): Пользователь.
            validated_data (dict): Проверенные данные.

        Returns:
            User: Обновленный пользователь.

        Raises:
            InvalidUserData: Если данные некорректны или обновление не удалось.
            serializers.ValidationError: Если валидация данных не прошла.
        """
        logger.info(f"Updating user={instance.id} with validated data")
        try:
            updated_user = UserService.update_user_and_profile(instance, validated_data)
            logger.info(f"User={instance.id} updated successfully")
            return updated_user
        except InvalidUserData as e:
            logger.error(f"Failed to update user={instance.id}: {str(e)}")
            raise serializers.ValidationError(str(e))


class PasswordResetSerializer(serializers.Serializer):
    """Сериализатор для запроса сброса пароля.

    Обрабатывает email для отправки ссылки на сброс пароля.
    """
    email = serializers.EmailField(
        required=True,
        help_text='Адрес электронной почты пользователя.'
    )

    class Meta:
        """Метаданные сериализатора PasswordResetSerializer."""
        fields = ['email']

    def validate(self, attrs):
        """Проверка корректности данных для запроса сброса пароля.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если email некорректен.
        """
        logger.info(f"Validating password reset request for email={attrs.get('email')}")
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Сериализатор для подтверждения сброса пароля.

    Обрабатывает новый пароль из тела запроса, uid и token из параметров запроса.
    """
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        help_text='Новый пароль пользователя.'
    )

    class Meta:
        """Метаданные сериализатора PasswordResetConfirmSerializer."""
        fields = ['new_password']

    def validate(self, attrs):
        """Проверка корректности данных для подтверждения сброса пароля.

        Args:
            attrs (dict): Данные для сериализации (new_password).

        Returns:
            dict: Валидированные данные, включая uid и token.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        logger.info(f"Validating password reset confirmation data")
        uid = self.context.get('uid')
        token = self.context.get('token')
        attrs['uid'] = uid
        attrs['token'] = token
        return attrs
