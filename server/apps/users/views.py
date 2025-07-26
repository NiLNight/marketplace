import logging
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.core.services.cache_services import CacheService
from apps.users.cookie_utils import delete_jwt_cookies
from apps.users.services.trottles import CeleryThrottle
from apps.users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer, CustomTokenRefreshSerializer
)
from apps.users.utils import handle_api_errors
from apps.users.cookie_utils import set_jwt_cookies
from apps.users.services.users_services import UserService, ConfirmPasswordService, ConfirmCodeService
from config import settings

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomTokenRefreshView(TokenRefreshView):
    """
    Кастомное представление для обновления токена, которое устанавливает токены в httpOnly cookies.
    """
    serializer_class = CustomTokenRefreshSerializer

    @handle_api_errors
    def post(self, request, *args, **kwargs):
        # Получаем refresh_token из cookie, чтобы потом извлечь из него user_id
        refresh_token_from_cookie = request.COOKIES.get(settings.SIMPLE_JWT['REFRESH_COOKIE'])

        if not refresh_token_from_cookie:
            return Response({"error": "Refresh token не найден в cookie."}, status=status.HTTP_401_UNAUTHORIZED)
        # Вызываем родительский метод, чтобы simple-jwt сделал свою работу
        response = super().post(request, *args, **kwargs)

        # Если обновление прошло успешно (статус 200)
        if response.status_code == 200:
            try:
                # Декодируем старый refresh токен, чтобы безопасно получить ID пользователя
                refresh = RefreshToken(refresh_token_from_cookie, verify=False)
                user_id = refresh.get('user_id')
                user = User.objects.get(id=user_id)

                # Теперь, когда у нас есть пользователь, мы можем сгенерировать для него
                response_with_cookies = set_jwt_cookies(Response(status=status.HTTP_200_OK), user)
                response_with_cookies.data = {"message": "Token refreshed successfully"}
                return response_with_cookies
            except Exception as e:
                logger.error(f"Error updating token after validation: {e}")
                return Response({"error": "Ошибка при обработке токена."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return response


class UserRegistrationView(APIView):
    """API-представление для регистрации новых пользователей.

    Обрабатывает запросы на создание учетной записи и отправку кода подтверждения.

    Attributes:
        permission_classes (list): Список классов разрешений.
        throttle_classes (list): Список классов для ограничения частоты запросов.
        serializer_class (UserRegistrationSerializer): Класс сериализатора для обработки данных.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    serializer_class = UserRegistrationSerializer

    @handle_api_errors
    def post(self, request):
        """Регистрирует нового пользователя.

        Args:
            request (Request): HTTP-запрос с данными пользователя (username, email, password).

        Returns:
            Response: Ответ с сообщением об успешной регистрации или необходимости активации.

        Raises:
            serializers.ValidationError: Если данные некорректны или не прошли валидацию.
            InvalidUserData: Если регистрация не удалась из-за некорректных данных.
        """
        logger.info(f"Processing registration request for email={request.data.get('email')}")
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
    """API-представление для аутентификации пользователей.

    Обрабатывает запросы на вход и слияние корзины/списка желаний из сессии.

    Attributes:
        permission_classes (list): Список классов разрешений.
        throttle_classes (list): Список классов для ограничения частоты запросов.
        serializer_class (UserLoginSerializer): Класс сериализатора для обработки данных.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    serializer_class = UserLoginSerializer

    @handle_api_errors
    def post(self, request):
        """Аутентифицирует пользователя.

        Args:
            request (Request): HTTP-запрос с данными для входа (email, password).

        Returns:
            Response: Ответ с данными пользователя и JWT-токенами.

        Raises:
            serializers.ValidationError: Если данные некорректны.
            AuthenticationFailed: Если аутентификация не удалась.
            AccountNotActivated: Если аккаунт не активирован.
        """
        logger.info(f"Processing login request for email={request.data.get('email')}")
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
        # Слияние корзины из сессии, если она существует
        if request.session.get('cart'):
            # Импортируем сервис корзины только при необходимости, чтобы избежать циклического импорта
            from apps.carts.services.cart_services import CartService
            CartService.merge_cart_on_login(user, request.session['cart'])
            del request.session['cart']
            CacheService.invalidate_cache(prefix=f"cart", pk=user.id)
            logger.info(f"Cart merged for user={user.id}")
        # Слияние списка желаний из сессии, если он существует
        if request.session.get('wishlist'):
            # Импортируем сервис списка желаний только при необходимости, чтобы избежать циклического импорта
            from apps.wishlists.services.wishlist_services import WishlistService
            WishlistService.merge_wishlist_on_login(user, request.session['wishlist'])
            CacheService.invalidate_cache(prefix=f"wishlist", pk=user.id)
            del request.session['wishlist']
            logger.info(f"Wishlist merged for user={user.id}")
        logger.info(f"User {user.id} logged in successfully")
        return set_jwt_cookies(response, user)


class UserLogoutView(APIView):
    """API-представление для выхода пользователей.

    Обрабатывает запросы на завершение сессии и инвалидацию токенов.

    Attributes:
        permission_classes (list): Список классов разрешений.
    """
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request):
        """Выполняет выход пользователя.

        Args:
            request (Request): HTTP-запрос с refresh-токеном.

        Returns:
            Response: Ответ с подтверждением выхода.

        Raises:
            InvalidUserData: Если refresh-токен недействителен.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Processing logout for user={request.user.id}")
        try:
            # Пытаемся добавить refresh_token в черный список
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['REFRESH_COOKIE'])
            UserService.logout_user(refresh_token)
        except Exception as e:
            logger.error(f"Error blacklisting token for user={user_id}, but proceeding with logout: {e}")

        response = Response({"message": "Выход успешно выполнен"}, status=status.HTTP_200_OK)
        delete_jwt_cookies(response)

        logger.info(f"User {user_id} logged out. Cookie deletion headers sent.")
        return response


class UserProfileView(APIView):
    """API-представление для управления профилем пользователя.

    Позволяет получать и обновлять данные профиля аутентифицированного пользователя.

    Attributes:
        permission_classes (list): Список классов разрешений.
        serializer_class (UserSerializer): Класс сериализатора для обработки данных.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @handle_api_errors
    def get(self, request):
        """Возвращает данные профиля пользователя.

        Args:
            request (Request): HTTP-запрос от аутентифицированного пользователя.

        Returns:
            Response: Ответ с данными профиля.

        Raises:
            serializers.ValidationError: Если данные сериализатора некорректны.
        """
        logger.info(f"Fetching profile for user={request.user.id}")
        user_id = request.user.id

        cached_data = CacheService.cache_user_profile(user_id)
        if cached_data:
            return Response(cached_data)
        serializer = self.serializer_class(request.user)
        cache_key = f"user_profile:{user_id}"
        CacheService.set_cached_data(cache_key, serializer.data, timeout=3600)
        return Response(serializer.data)

    @handle_api_errors
    def patch(self, request):
        """Обновляет данные профиля пользователя.

        Args:
            request (Request): HTTP-запрос с частичными данными профиля.

        Returns:
            Response: Ответ с обновленными данными профиля.

        Raises:
            serializers.ValidationError: Если данные некорректны.
            InvalidUserData: Если обновление профиля не удалось.
        """
        logger.info(f"Updating profile for user={request.user.id}")
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        CacheService.invalidate_cache(prefix="user_profile", pk=request.user.id)
        logger.info(f"Profile updated for user={request.user.id}")
        return Response(serializer.data)


class ResendCodeView(APIView):
    """API-представление для повторной отправки кода подтверждения.

    Обрабатывает запросы на повторную отправку кода для активации аккаунта.

    Attributes:
        permission_classes (list): Список классов разрешений.
        throttle_classes (list): Список классов для ограничения частоты запросов.
    """
    permission_classes = [AllowAny]
    throttle_classes = [CeleryThrottle]

    @handle_api_errors
    def post(self, request):
        """Отправляет новый код подтверждения.

        Args:
            request (Request): HTTP-запрос с email пользователя.

        Returns:
            Response: Ответ с подтверждением отправки кода.

        Raises:
            UserNotFound: Если пользователь не найден или уже активирован.
        """
        logger.info(f"Processing resend code request for email={request.data.get('email')}")
        email = request.data.get('email')
        ConfirmCodeService.resend_confirmation_code(email)
        logger.info(f"Confirmation code resent to {email}")
        return Response({"message": "Новый код отправлен"})


class ConfirmView(APIView):
    """API-представление для подтверждения регистрации.

    Активирует аккаунт пользователя по email и коду подтверждения.

    Attributes:
        permission_classes (list): Список классов разрешений.
        throttle_classes (list): Список классов для ограничения частоты запросов.
    """
    permission_classes = [AllowAny]
    throttle_classes = [CeleryThrottle]

    @handle_api_errors
    def post(self, request):
        """Активирует аккаунт пользователя.

        Args:
            request (Request): HTTP-запрос с email и кодом подтверждения.

        Returns:
            Response: Ответ с подтверждением активации.

        Raises:
            UserNotFound: Если пользователь не найден.
            InvalidUserData: Если код неверный или истек срок действия.
        """
        logger.info(f"Processing confirmation request for email={request.data.get('email')}")
        email = request.data.get('email')
        code = request.data.get('code')
        ConfirmCodeService.confirm_account(email=email, code=code)
        logger.info(f"Account confirmed for {email}")
        return Response({'message': 'Аккаунт активирован'})


class PasswordResetRequestView(APIView):
    """API-представление для запроса сброса пароля.

    Обрабатывает запросы на отправку письма для сброса пароля.

    Attributes:
        permission_classes (list): Список классов разрешений.
        serializer_class (PasswordResetSerializer): Класс сериализатора для обработки данных.
        throttle_classes (list): Список классов для ограничения частоты запросов.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer
    throttle_classes = [CeleryThrottle]

    @handle_api_errors
    def post(self, request):
        """Отправляет письмо для сброса пароля.

        Args:
            request (Request): HTTP-запрос с email пользователя.

        Returns:
            Response: Ответ с подтверждением отправки письма.

        Raises:
            serializers.ValidationError: Если email некорректен.
            UserNotFound: Если пользователь не найден.
        """
        logger.info(f"Processing password reset request for email={request.data.get('email')}")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        ConfirmPasswordService.request_password_reset(serializer.validated_data['email'])
        logger.info(f"Password reset requested for {serializer.validated_data['email']}")
        return Response(
            {"detail": "Если указанный email существует, на него отправлено письмо."},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """API-представление для подтверждения сброса пароля.

    Обрабатывает запросы на изменение пароля с использованием uid и token из URL.

    Attributes:
        serializer_class (PasswordResetConfirmSerializer): Класс сериализатора для обработки данных.
        permission_classes (list): Список классов разрешений.
        throttle_classes (list): Список классов для ограничения частоты запросов.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    throttle_classes = [CeleryThrottle]

    @handle_api_errors
    def post(self, request):
        """Изменяет пароль пользователя.

        Args:
            request (Request): HTTP-запрос с new_password в теле и uid, token в GET-параметрах.

        Returns:
            Response: Ответ с подтверждением изменения пароля.

        Raises:
            serializers.ValidationError: Если данные некорректны.
            InvalidUserData: Если uid, token или данные недействительны.
            UserNotFound: Если пользователь не найден.
        """
        logger.info(f"Processing password reset confirmation for uid={request.query_params.get('uid')}")
        uid = request.query_params.get('uid')
        token = request.query_params.get('token')

        # Валидация параметров в сервисе
        ConfirmPasswordService.validate_reset_params(uid, token)

        serializer = self.serializer_class(
            data=request.data,
            context={'uid': uid, 'token': token}
        )
        serializer.is_valid(raise_exception=True)
        ConfirmPasswordService.confirm_password_reset(
            uid=serializer.validated_data['uid'],
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password'],
        )
        logger.info("Password reset confirmed")
        return Response({"detail": "Пароль успешно изменён."}, status=status.HTTP_200_OK)
