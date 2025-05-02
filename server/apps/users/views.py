import logging
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer
)
from apps.users.utils import set_jwt_cookies, handle_user_api_errors
from apps.users.services.users_services import UserService, ConfirmPasswordService, ConfirmCodeService
from apps.wishlists.services.wishlist_services import WishlistService
from apps.carts.services.cart_services import CartService
from config import settings

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRegistrationView(APIView):
    """Представление для регистрации нового пользователя."""
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @handle_user_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для регистрации пользователя.

        Args:
            request: HTTP-запрос с данными пользователя.

        Returns:
            Response с сообщением об успешной регистрации.

        Raises:
            UserServiceException: Если данные некорректны или регистрация не удалась.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Registering new user, user={user_id}, path={request.path}")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.register_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        logger.info(f"User {user.id} registered, awaiting email confirmation")
        return Response(
            {"detail": "Требуется активация аккаунта. Код подтверждения отправлен на ваш email."},
            status=status.HTTP_201_CREATED
        )


class UserLoginView(APIView):
    """Представление для аутентификации пользователя."""
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @handle_user_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для входа пользователя.

        Args:
            request: HTTP-запрос с email и паролем.

        Returns:
            Response с данными пользователя и JWT-токенами в cookies.

        Raises:
            AuthenticationFailed: Если аутентификация не удалась.
            UserServiceException: Если произошла ошибка входа.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Attempting login, user={user_id}, path={request.path}")
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = UserService.login_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        response_data = {
            "message": "Вход выполнен успешно",
            "user": {"id": user.id, "username": user.username, "email": user.email}
        }
        response = Response(response_data)
        if request.session.get('cart'):
            CartService.merge_cart_on_login(user, request.session['cart'])
            del request.session['cart']
        if request.session.get('wishlist'):
            WishlistService.merge_wishlist_on_login(user, request.session['wishlist'])
            del request.session['wishlist']
        logger.info(f"User {user.id} logged in, setting JWT cookies")
        return set_jwt_cookies(response, user)


class UserLogoutView(APIView):
    """Представление для выхода пользователя."""
    permission_classes = [IsAuthenticated]

    @handle_user_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для выхода пользователя.

        Args:
            request: HTTP-запрос с refresh-токеном.

        Returns:
            Response с подтверждением выхода.

        Raises:
            UserServiceException: Если выход не удался.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Logging out user {user_id}, path={request.path}")
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['REFRESH_COOKIE'])
        UserService.logout_user(refresh_token)
        response = Response({"message": "Выход успешно выполнен"}, status=status.HTTP_200_OK)
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
        response.delete_cookie(settings.SIMPLE_JWT['REFRESH_COOKIE'])
        logger.info(f"User {user_id} logged out successfully")
        return response


class UserProfileView(APIView):
    """Представление для получения и обновления профиля пользователя."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @handle_user_api_errors
    def get(self, request):
        """Обрабатывает GET-запрос для получения профиля пользователя.

        Args:
            request: HTTP-запрос.

        Returns:
            Response с данными пользователя и профиля.
        """
        user_id = request.user.id
        logger.info(f"Retrieving profile for user {user_id}, path={request.path}")
        serializer = self.serializer_class(request.user)
        logger.info(f"Profile retrieved for user {user_id}")
        return Response(serializer.data)

    @handle_user_api_errors
    def patch(self, request):
        """Обрабатывает PATCH-запрос для обновления профиля пользователя.

        Args:
            request: HTTP-запрос с данными для обновления.

        Returns:
            Response с обновленными данными пользователя.

        Raises:
            UserServiceException: Если обновление не удалось.
        """
        user_id = request.user.id
        logger.info(f"Updating profile for user {user_id}, path={request.path}")
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Profile updated for user {user_id}")
        return Response(serializer.data)


class ResendCodeView(APIView):
    """Представление для повторной отправки кода подтверждения."""
    permission_classes = [AllowAny]

    @handle_user_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для повторной отправки кода.

        Args:
            request: HTTP-запрос с email.

        Returns:
            Response с подтверждением отправки.

        Raises:
            UserNotFound: Если пользователь не найден или активирован.
            UserServiceException: Если отправка не удалась.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Resending confirmation code, user={user_id}, path={request.path}")
        email = request.data.get('email')
        ConfirmCodeService.resend_confirmation_code(email)
        logger.info(f"Confirmation code resent to {email}")
        return Response({"message": "Новый код отправлен"})


class ConfirmView(APIView):
    """Представление для подтверждения аккаунта."""
    permission_classes = [AllowAny]

    @handle_user_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для подтверждения аккаунта.

        Args:
            request: HTTP-запрос с email и кодом.

        Returns:
            Response с подтверждением активации.

        Raises:
            UserNotFound: Если пользователь не найден.
            UserServiceException: Если код неверный или просрочен.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Confirming account, user={user_id}, path={request.path}")
        email = request.data.get('email')
        code = request.data.get('code')
        ConfirmCodeService.confirm_account(email=email, code=code)
        logger.info(f"Account confirmed for email={email}")
        return Response({'message': 'Аккаунт активирован'})


class PasswordResetRequestView(APIView):
    """Представление для запроса сброса пароля."""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    @handle_user_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для запроса сброса пароля.

        Args:
            request: HTTP-запрос с email.

        Returns:
            Response с подтверждением отправки.

        Raises:
            UserNotFound: Если пользователь не найден.
            UserServiceException: Если запрос не удался.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Requesting password reset, user={user_id}, path={request.path}")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        ConfirmPasswordService.request_password_reset(serializer.validated_data['email'])
        logger.info(f"Password reset requested for email={serializer.validated_data['email']}")
        return Response({"detail": "Если указанный email существует, на него отправлено письмо."})


class PasswordResetConfirmView(APIView):
    """Представление для подтверждения сброса пароля."""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    @handle_user_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для сброса пароля.

        Args:
            request: HTTP-запрос с uid, token и новым паролем.

        Returns:
            Response с подтверждением сброса.

        Raises:
            UserNotFound: Если пользователь не найден.
            UserServiceException: Если токен недействителен или операция не удалась.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Confirming password reset, user={user_id}, path={request.path}")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        ConfirmPasswordService.confirm_password_reset(
            uid=serializer.validated_data['uid'],
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password']
        )
        logger.info(f"Password reset confirmed")
        return Response({"detail": "Пароль успешно изменён."})
