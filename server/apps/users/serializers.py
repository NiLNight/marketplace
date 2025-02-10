"""
Сериализаторы для работы с пользователями:
- Регистрация
- Авторизация
- Профиль
"""

import random
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.users.models import UserProfile, EmailVerified
from apps.users.tasks import send_confirmation_email

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор регистрации пользователя с валидацией пароля.
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        # Если необходимо, можно добавить валидацию пароля:
        # validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        """
        Создает пользователя с хешированием пароля, сохраняет код подтверждения,
        и отправляет письмо с подтверждением на email.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False,  # Аккаунт будет активирован после подтверждения
        )
        # Генерация кода подтверждения
        code = str(random.randint(100000, 999999))
        email_verified = EmailVerified(
            user=user,
            confirmation_code=code,
            code_created_at=timezone.now()
        )
        email_verified.save()

        # Запуск асинхронной задачи для отправки письма
        send_confirmation_email.delay(email=user.email, code=code)
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Сериализатор для аутентификации пользователя по email и password.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        max_length=128,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """
        Проверяет учетные данные: если пользователь с данным email существует,
        его аккаунт активен и пароль корректен.
        """
        email = attrs.get('email')
        password = attrs.get('password')
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("Неверные учетные данные")

        if not user.is_active:
            raise serializers.ValidationError("Аккаунт не активирован. Проверьте почту")

        if not user.check_password(password):
            raise serializers.ValidationError("Неверные учетные данные")

        # Дополнительная аутентификация для корректной работы с backend'ом
        user = authenticate(username=user.username, password=password)
        if not user:
            raise serializers.ValidationError("Неверные учетные данные")

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для профиля пользователя.
    """
    class Meta:
        model = UserProfile
        fields = ['public_id', 'phone', 'birth_date', 'avatar']


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пользователя, включающий вложенный профиль.
    """
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile']

    def update(self, instance, validated_data):
        """
        Обновляет поля пользователя и, если присутствуют данные профиля, обновляет
        или создает профиль через вложенный сериализатор.
        """
        profile_data = validated_data.pop('profile', None)
        # Обновляем поля пользователя
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Если данные профиля переданы, обновляем или создаем профиль
        if profile_data:
            if hasattr(instance, 'profile') and instance.profile is not None:
                profile_serializer = UserProfileSerializer(
                    instance=instance.profile, data=profile_data, partial=True
                )
                profile_serializer.is_valid(raise_exception=True)
                profile_serializer.save()
            else:
                UserProfile.objects.create(user=instance, **profile_data)
        return instance
