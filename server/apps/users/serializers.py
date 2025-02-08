"""
Сериализаторы для работы с пользователями:
- Регистрация
- Авторизация
- Профиль
"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.shortcuts import get_object_or_404
from apps.users.models import UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор регистрации с валидацией пароля"""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        # validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        """Создание пользователя с хешированием пароля"""
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для аутентификации по username/password"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        max_length=128,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Проверка учетных данных и активности пользователя"""
        email = attrs.get('email')
        password = attrs.get('password')
        user = User.objects.filter(email=email).first()
        # Проверка пользователя и пароля
        if user and user.check_password(password):
            user = authenticate(username=user.username, password=password)
        # Если пользователь не найден
        if not user:
            raise serializers.ValidationError("Неверные учетные данные")
        # Если пользователь не активен
        if not user.is_active:
            raise serializers.ValidationError("Учетная запись деактивирована")

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""

    class Meta:
        model = UserProfile
        fields = [
            'public_id',
            'phone',
            'birth_date',
            'avatar',
        ]


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile']

    def update(self, instance, validated_data):
        # Извлекаем данные для профиля (если они есть)
        profile_data = validated_data.pop('profile', {})
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        # Если есть данные профиля – обновляем профиль через его сериализатор
        if profile_data:
            profile_serializer = self.fields['profile']
            profile_serializer.update(instance.profile, profile_data)
        return instance
