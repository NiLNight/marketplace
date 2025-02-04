from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.auth.models import User

from apps.users.models import UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, label='Повторить пароль')

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError('Пароли не совпадают')
        return data


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20, required=True, write_only=True)
    password = serializers.CharField(max_length=50, required=True, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=username,
            password=password
        )
        if not user:
            raise serializers.ValidationError("Неверные учетные данные")
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

    def get(self):
        return self.context.get('user')
