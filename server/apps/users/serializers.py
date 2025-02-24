"""
Сериализаторы для работы с пользователями:
- Регистрация
- Авторизация
- Профиль
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import UserProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['is_active'] = user.is_active
        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор регистрации пользователя с валидацией пароля.
    """
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')


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


class PasswordResetSerializer(serializers.Serializer):
    """
    Сериализатор для получения почты, для отправки ссылки на сброс пароля.
    """
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Сериализатор для сброса пароля.
    """
    uid = serializers.IntegerField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

