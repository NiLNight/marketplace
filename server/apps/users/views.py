import logging
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer
)
from apps.users.utils import set_jwt_cookies, handle_api_errors
from apps.users.services.users_services import UserService, ConfirmPasswordService, ConfirmCodeService
from config import settings

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRegistrationView(APIView):
    """Представление для регистрации нового пользователя."""
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для регистрации пользователя."""
        logger.info("Processing user registration request")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.register_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        if user.is_active:
            response = Response(status=status.HTTP_201_CREATED)
            return set_jwt_cookies(response, user)
        logger.info(f"User {user.id} registered, awaiting email confirmation")
        return Response(
            {"detail": "Требуется активация аккаунта. Код подтверждения отправлен на ваш email."},
            status=status.HTTP_201_CREATED
        )


class UserLoginView(APIView):
    """Представление для аутентификации пользователя."""
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для входа пользователя."""
        logger.info("Processing user login request")
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = UserService.login_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        if not user.is_active:
            logger.warning(f"User {user.id} login attempt with inactive account")
            return Response(
                {"error": "Требуется активация аккаунта"},
                status=status.HTTP_403_FORBIDDEN
            )
        response_data = {
            "message": "Login successful",
            "user": {"id": user.id, "username": user.username, "email": user.email}
        }
        response = Response(response_data)
        if request.session.get('cart'):
            from apps.carts.services.cart_services import CartService
            CartService.merge_cart_on_login(user, request.session['cart'])
            del request.session['cart']
            logger.info(f"Cart merged for user={user.id}")
        if request.session.get('wishlist'):
            from apps.wishlists.services.wishlist_services import WishlistService
            WishlistService.merge_wishlist_on_login(user, request.session['wishlist'])
            del request.session['wishlist']
            logger.info(f"Wishlist merged for user={user.id}")
        logger.info(f"User {user.id} logged in successfully")
        return set_jwt_cookies(response, user)


class UserLogoutView(APIView):
    """Представление для выхода пользователя."""
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для выхода пользователя."""
        logger.info(f"Processing logout for user={request.user.id}")
        refresh_token = request.COOKIES.get('refresh_token')
        UserService.logout_user(refresh_token)
        response = Response({"message": "Выход успешно выполнен"}, status=status.HTTP_200_OK)
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
        response.delete_cookie(settings.SIMPLE_JWT['REFRESH_COOKIE'])
        logger.info(f"User {request.user.id} logged out successfully")
        return response


class UserProfileView(APIView):
    """Представление для получения и обновления профиля пользователя."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @handle_api_errors
    def get(self, request):
        """Обрабатывает GET-запрос для получения профиля."""
        logger.info(f"Fetching profile for user={request.user.id}")
        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    @handle_api_errors
    def patch(self, request):
        """Обрабатывает PATCH-запрос для обновления профиля."""
        logger.info(f"Updating profile for user={request.user.id}")
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Profile updated for user={request.user.id}")
        return Response(serializer.data)


class ResendCodeView(APIView):
    """Представление для повторной отправки кода подтверждения."""
    permission_classes = [AllowAny]

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для повторной отправки кода."""
        logger.info("Processing resend confirmation code request")
        email = request.data.get('email')
        ConfirmCodeService.resend_confirmation_code(email)
        logger.info(f"Confirmation code resent to {email}")
        return Response({"message": "Новый код отправлен"})


class ConfirmView(APIView):
    """Представление для подтверждения регистрации пользователя."""
    permission_classes = [AllowAny]

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для активации аккаунта."""
        logger.info("Processing account confirmation request")
        email = request.data.get('email')
        code = request.data.get('code')
        ConfirmCodeService.confirm_account(email=email, code=code)
        logger.info(f"Account confirmed for {email}")
        return Response({'message': 'Аккаунт активирован'})


class PasswordResetRequestView(APIView):
    """Представление для запроса сброса пароля."""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для запроса сброса пароля."""
        logger.info("Processing password reset request")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        ConfirmPasswordService.request_password_reset(serializer.validated_data['email'])
        logger.info(f"Password reset requested for {serializer.validated_data['email']}")
        return Response(
            {"detail": "Если указанный email существует, на него отправлено письмо."},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """Представление для подтверждения сброса пароля."""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для изменения пароля."""
        logger.info("Processing password reset confirmation")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        ConfirmPasswordService.confirm_password_reset(
            uid=serializer.validated_data['uid'],
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password'],
        )
        logger.info("Password reset confirmed")
        return Response({"detail": "Пароль успешно изменён."}, status=status.HTTP_200_OK)
