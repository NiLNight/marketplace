from rest_framework import serializers
from django.contrib.auth.models import User


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

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if user.check_password(password):
                data['user'] = user
                return data
            else:
                raise serializers.ValidationError("Неверный пароль")
        else:
            raise serializers.ValidationError("Неверные учетные данные")
