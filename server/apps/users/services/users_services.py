import random
import logging
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import EmailVerified, UserProfile
from apps.users.services.tasks import send_confirmation_email, send_password_reset_email
from apps.users.exceptions import UserServiceException, UserNotFound
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from config import settings

User = get_user_model()
logger = logging.getLogger(__name__)


class UserService:
    """Сервис для управления пользователями.

    Предоставляет методы для регистрации, аутентификации, выхода и обновления профиля.
    """

    @staticmethod
    def register_user(username: str, email: str, password: str) -> User:
        """Регистрирует нового пользователя.

        Args:
            username: Имя пользователя.
            email: Email пользователя.
            password: Пароль пользователя.

        Returns:
            Созданный объект User.

        Raises:
            UserServiceException: Если регистрация не удалась.
        """
        logger.info(f"Registering user with email={email}, username={username}")
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=False
            )
            code = str(random.randint(100000, 999999))
            EmailVerified.objects.create(
                user=user,
                confirmation_code=code,
                code_created_at=timezone.now()
            )
            send_confirmation_email.delay(email, code)
            logger.info(f"User {user.id} registered successfully, confirmation email sent")
            return user
        except Exception as e:
            logger.error(f"Failed to register user with email={email}: {str(e)}")
            raise UserServiceException(f"Ошибка регистрации пользователя: {str(e)}")

    @staticmethod
    def login_user(email: str, password: str) -> User:
        """Аутентифицирует пользователя.

        Args:
            email: Email пользователя.
            password: Пароль пользователя.

        Returns:
            Аутентифицированный объект User.

        Raises:
            AuthenticationFailed: Если аутентификация не удалась.
            UserNotFound: Если пользователь не найден.
        """
        logger.info(f"Attempting login for email={email}")
        try:
            user = User.objects.filter(email=email).first()
            if user is None:
                logger.warning(f"User with email={email} not found")
                raise UserNotFound("Пользователь с таким email не найден")
            if not user.is_active:
                logger.warning(f"User {user.id} is inactive")
                raise AuthenticationFailed("Аккаунт не активирован")
            if not user.check_password(password):
                logger.warning(f"Invalid password for user {user.id}")
                raise AuthenticationFailed("Неверные учетные данные")
            user = authenticate(username=user.username, password=password)
            if not user:
                logger.error(f"Authentication failed for user {user.id}")
                raise AuthenticationFailed("Ошибка аутентификации")
            logger.info(f"User {user.id} logged in successfully")
            return user
        except Exception as e:
            logger.error(f"Login error for email={email}: {str(e)}")
            raise UserServiceException(f"Ошибка входа: {str(e)}")

    @staticmethod
    def logout_user(refresh_token: str) -> None:
        """Добавляет refresh-токен в черный список.

        Args:
            refresh_token: Refresh-токен пользователя.

        Raises:
            UserServiceException: Если токен недействителен или операция не удалась.
        """
        logger.info(f"Attempting logout with refresh_token={refresh_token[:10]}...")
        try:
            if not refresh_token:
                logger.warning("No refresh token provided")
                raise UserServiceException("Требуется refresh-токен")
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("User logged out successfully")
        except TokenError as e:
            logger.error(f"Invalid token during logout: {str(e)}")
            raise UserServiceException("Неправильный токен")
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            raise UserServiceException(f"Ошибка выхода: {str(e)}")

    @staticmethod
    def update_user_and_profile(user: User, validated_data: dict) -> User:
        """Обновляет данные пользователя и его профиля.

        Args:
            user: Объект User для обновления.
            validated_data: Проверенные данные, включая данные профиля.

        Returns:
            Обновленный объект User.

        Raises:
            UserServiceException: Если обновление не удалось.
        """
        user_id = user.id
        logger.info(f"Updating user {user_id} with data={validated_data}")
        try:
            profile_data = validated_data.pop('profile', None)
            for attr, value in validated_data.items():
                setattr(user, attr, value)
            user.save()

            if profile_data:
                from apps.users.serializers import UserProfileSerializer
                if hasattr(user, 'profile') and user.profile is not None:
                    profile_serializer = UserProfileSerializer(
                        instance=user.profile,
                        data=profile_data,
                        partial=True
                    )
                    profile_serializer.is_valid(raise_exception=True)
                    profile_serializer.save()
                else:
                    UserProfile.objects.create(user=user, **profile_data)

            logger.info(f"User {user_id} updated successfully")
            return user
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise UserServiceException(f"Ошибка обновления пользователя: {str(e)}")


class ConfirmCodeService:
    """Сервис для управления подтверждением email."""

    @staticmethod
    def resend_confirmation_code(email: str) -> bool:
        """Повторно отправляет код подтверждения.

        Args:
            email: Email пользователя.

        Returns:
            True, если код отправлен.

        Raises:
            UserNotFound: Если пользователь не найден или уже активирован.
            UserServiceException: Если операция не удалась.
        """
        logger.info(f"Resending confirmation code to {email}")
        try:
            user = User.objects.filter(email=email, is_active=False).first()
            if not user:
                logger.warning(f"User with email={email} not found or already active")
                raise UserNotFound("Аккаунт не найден или уже активирован")
            code = str(random.randint(100000, 999999))
            EmailVerified.objects.update_or_create(
                user=user,
                defaults={
                    'confirmation_code': code,
                    'code_created_at': timezone.now()
                }
            )
            send_confirmation_email.delay(email, code)
            logger.info(f"Confirmation code resent to {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to resend confirmation code to {email}: {str(e)}")
            raise UserServiceException(f"Ошибка отправки кода подтверждения: {str(e)}")

    @staticmethod
    def confirm_account(email: str, code: str) -> bool:
        """Подтверждает аккаунт по коду.

        Args:
            email: Email пользователя.
            code: Код подтверждения.

        Returns:
            True, если аккаунт подтвержден.

        Raises:
            UserNotFound: Если пользователь не найден.
            UserServiceException: Если код неверный или просрочен.
        """
        logger.info(f"Confirming account for email={email}, code={code}")
        try:
            user = User.objects.filter(email=email).first()
            if not user:
                logger.warning(f"User with email={email} not found")
                raise UserNotFound("Пользователь с таким email не найден")
            email_verified = EmailVerified.objects.filter(user=user, confirmation_code=code).first()
            if not email_verified:
                logger.warning(f"Invalid confirmation code for user {user.id}")
                raise UserServiceException("Неверный код подтверждения")
            time_diff = (timezone.now() - email_verified.code_created_at).total_seconds()
            if time_diff > 86400:  # 24 часа
                logger.warning(f"Confirmation code expired for user {user.id}")
                raise UserServiceException("Срок действия кода истек")
            user.is_active = True
            user.save()
            email_verified.confirmation_code = None
            email_verified.save()
            logger.info(f"Account confirmed for user {user.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to confirm account for email={email}: {str(e)}")
            raise UserServiceException(f"Ошибка подтверждения аккаунта: {str(e)}")


class ConfirmPasswordService:
    """Сервис для управления сбросом пароля."""

    @staticmethod
    def request_password_reset(email: str) -> bool:
        """Запрашивает сброс пароля.

        Args:
            email: Email пользователя.

        Returns:
            True, если запрос отправлен.

        Raises:
            UserNotFound: Если пользователь не найден.
            UserServiceException: Если операция не удалась.
        """
        logger.info(f"Requesting password reset for email={email}")
        try:
            user = User.objects.filter(email=email).first()
            if not user:
                logger.warning(f"User with email={email} not found")
                raise UserNotFound("Пользователь с таким email не найден")
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            reset_url = f"{settings.FRONTEND_URL}/reset-password/?token={token}&uid={uid}"
            send_password_reset_email.delay(email, reset_url)
            logger.info(f"Password reset requested for user {user.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to request password reset for email={email}: {str(e)}")
            raise UserServiceException(f"Ошибка запроса сброса пароля: {str(e)}")

    @staticmethod
    def confirm_password_reset(uid: str, token: str, new_password: str) -> User:
        """Подтверждает сброс пароля.

        Args:
            uid: Закодированный ID пользователя.
            token: Токен сброса пароля.
            new_password: Новый пароль.

        Returns:
            Обновленный объект User.

        Raises:
            UserNotFound: Если пользователь не найден.
            UserServiceException: Если токен недействителен или операция не удалась.
        """
        logger.info(f"Confirming password reset for uid={uid}")
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.filter(id=user_id).first()
            if not user:
                logger.warning(f"User with id={user_id} not found")
                raise UserNotFound("Пользователь не найден")
            if not PasswordResetTokenGenerator().check_token(user, token):
                logger.warning(f"Invalid or expired token for user {user.id}")
                raise UserServiceException("Неверный или просроченный токен")
            user.set_password(new_password)
            user.save()
            logger.info(f"Password reset confirmed for user {user.id}")
            return user
        except Exception as e:
            logger.error(f"Failed to confirm password reset for uid={uid}: {str(e)}")
            raise UserServiceException(f"Ошибка сброса пароля: {str(e)}")
