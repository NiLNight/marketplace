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
            password=validated_data['password'],
            is_active=False,
        )
        # Генерация и сохранение кода
        code = str(random.randint(100000, 999999))
        email_verified = EmailVerified(user=user,
                                       confirmation_code=code,
                                       code_created_at=timezone.now())
        email_verified.save()

        # Запуск асинхронной задачи для отправки письма
        # send_confirmation_email.delay(
        #     email=user.email,
        #     code=code
        # )
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

        # Если пользователь не найден
        if not user:
            raise serializers.ValidationError("Неверные учетные данные")

        # Если пользователь не активен
        if not user.is_active:
            raise serializers.ValidationError("Аккаунт не активирован. Проверьте почту")

        # Проверка пользователя и пароля
        if user and user.check_password(password):
            user = authenticate(username=user.username, password=password)

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


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(source='user.email')
