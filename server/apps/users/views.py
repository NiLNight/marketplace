from django.conf import settings
from tokenize import TokenError
from django.contrib.auth.models import User
from apps.users.models import UserProfile

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.users.serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from apps.users.utils import set_jwt_cookies
from django.shortcuts import get_object_or_404


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super(CustomTokenObtainPairView, self).post(request, *args, **kwargs)
        access_token = response.data['access']
        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE'],
            value=access_token,
            domain=settings.SIMPLE_JWT['AUTH_COOKIE_DOMAIN'],
            path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
            expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        )
        return response


class UserRegistrationView(APIView):
    serializer_class = UserRegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.create_user(serializer.validated_data['username'],
                                        serializer.validated_data['email'],
                                        serializer.validated_data['password'])
        response = Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email}
        },
            status=status.HTTP_201_CREATED
        )
        return set_jwt_cookies(response, user)


class UserLoginView(APIView):
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        response = Response(
            {
                'message': 'Login successful',
                'id': user.id,
                'user': user.username,
                'email': user.email
            }
        )
        return set_jwt_cookies(response, user)


class UserLogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            response = Response(
                {'message': 'Logged out successfully'}, status=status.HTTP_200_OK
            )
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            return response
        except TokenError as e:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
