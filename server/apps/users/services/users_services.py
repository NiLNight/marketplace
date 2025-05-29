import logging
import binascii
import secrets
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from apps.users.models import EmailVerified, UserProfile
from apps.users.services.tasks import send_confirmation_email, send_password_reset_email
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from apps.users.exceptions import UserNotFound, InvalidUserData, AuthenticationFailed, AccountNotActivated
from django.db import transaction

User = get_user_model()
logger = logging.getLogger(__name__)


class UserService:
    """Сервис для управления пользователями.

    Предоставляет методы для регистрации, аутентификации, выхода и обновления данных пользователя.

    Methods:
        register_user: Регистрация нового пользователя.
        login_user: Аутентификация пользователя.
        logout_user: Выход пользователя с инвалидацией refresh-токена.
        update_user_and_profile: Обновление пользователя и его профиля.
    """

    @staticmethod
    def register_user(username: str, email: str, password: str) -> User:
        """Регистрация нового пользователя.

        Args:
            username (str): Имя пользователя.
            email (str): Адрес электронной почты.
            password (str): Пароль пользователя.

        Returns:
            User: Созданный пользователь.

        Raises:
            InvalidUserData: Если регистрация не удалась.
        """
        logger.info(f"Registering user with email={email}")
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=False
                )
                code = str(secrets.randbelow(1000000)).zfill(6)  # Генерируем случайный 6-значный код для подтверждения
                EmailVerified.objects.create(
                    user=user,
                    confirmation_code=code,
                    code_created_at=timezone.now()
                )
                send_confirmation_email.delay(email, code)
            logger.info(f"User registered successfully, email={email}")
            return user
        except Exception as e:
            logger.error(f"Failed to register user: {str(e)}, email={email}")
            raise InvalidUserData(f"Ошибка регистрации: {str(e)}")

    @staticmethod
    def login_user(email: str, password: str) -> User:
        """Аутентификация пользователя.

        Args:
            email (str): Адрес электронной почты.
            password (str): Пароль пользователя.

        Returns:
            User: Аутентифицированный пользователь.

        Raises:
            AuthenticationFailed: Если аутентификация не удалась.
            AccountNotActivated: Если аккаунт не активирован.
        """
        logger.info(f"Attempting to log in user with email={email}")
        user = User.objects.select_related('profile').filter(email=email).first()
        if user is None:
            logger.warning(f"User not found with email={email}")
            raise AuthenticationFailed("Неверные учетные данные")
        if not user.is_active:
            logger.warning(f"Account not activated for email={email}")
            raise AccountNotActivated("Аккаунт не активирован")
        if not user.check_password(password):
            logger.warning(f"Invalid password for email={email}")
            raise AuthenticationFailed("Неверные учетные данные")
        user = authenticate(username=user.username, password=password)
        if not user:
            logger.error(f"Authentication failed for email={email}")
            raise AuthenticationFailed("Ошибка аутентификации")
        logger.info(f"User logged in successfully, email={email}")
        return user

    @staticmethod
    def logout_user(refresh_token: str) -> None:
        """Выход пользователя с инвалидацией refresh-токена.

        Args:
            refresh_token (str): Refresh-токен для инвалидации.

        Raises:
            InvalidUserData: Если токен недействителен.
        """
        if not refresh_token:
            logger.warning("Refresh token is required")
            raise InvalidUserData("Требуется refresh токен")
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("User logged out successfully")
        except TokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise InvalidUserData("Неправильный токен")

    @staticmethod
    def update_user_and_profile(user: User, validated_data: dict) -> User:
        """Обновление пользователя и его профиля.

        Запрещает изменение email и public_id.

        Args:
            user (User): Пользователь для обновления.
            validated_data (dict): Проверенные данные.

        Returns:
            User: Обновленный пользователь.

        Raises:
            InvalidUserData: Если данные некорректны.
        """
        logger.info(f"Updating user and profile for user={user.id}")
        profile_data = validated_data.pop('profile', None)

        # Игнорировать попытки изменения email
        if 'email' in validated_data:
            logger.warning(f"Attempt to change email for user={user.id}, ignored")
            validated_data.pop('email')

        # Обновление полей пользователя
        for attr, value in validated_data.items():
            setattr(user, attr, value)
        user.save()

        # Обновление профиля
        if profile_data:
            from apps.users.serializers import UserProfileSerializer
            profile_data.pop('public_id', None)
            if hasattr(user, 'profile') and user.profile:
                profile_serializer = UserProfileSerializer(
                    instance=user.profile,
                    data=profile_data,
                    partial=True
                )
                if profile_serializer.is_valid(raise_exception=True):
                    profile_serializer.save()
            else:
                UserProfile.objects.create(user=user, **profile_data)
        logger.info(f"User and profile updated successfully for user={user.id}")
        return user


class ConfirmCodeService:
    """Сервис для управления кодами подтверждения.

    Предоставляет методы для отправки и подтверждения кодов активации аккаунта.

    Methods:
        resend_confirmation_code: Повторная отправка кода подтверждения.
        confirm_account: Подтверждение аккаунта.
    """

    @staticmethod
    def resend_confirmation_code(email: str) -> None:
        """Повторная отправка кода подтверждения.

        Args:
            email (str): Адрес электронной почты.

        Raises:
            UserNotFound: Если пользователь не найден или уже активирован.
        """
        logger.info(f"Resending confirmation code to email={email}")
        try:
            user = User.objects.get(email=email, is_active=False)
            code = str(secrets.randbelow(1000000)).zfill(6)
            EmailVerified.objects.update_or_create(
                user=user,
                defaults={
                    'confirmation_code': code,
                    'code_created_at': timezone.now()
                }
            )
            send_confirmation_email.delay(email, code)
            logger.info(f"Confirmation code resent to email={email}")
        except User.DoesNotExist:
            logger.warning(f"User not found or already activated for email={email}")
            raise UserNotFound("Аккаунт не найден или уже активирован")

    @staticmethod
    def confirm_account(email: str, code: str) -> None:
        """Подтверждение аккаунта.

        Проверяет код подтверждения и активирует аккаунт пользователя.
        Код должен быть действительным и не просрочен.

        Args:
            email (str): Адрес электронной почты.
            code (str): Код подтверждения.

        Returns:
            None: Метод ничего не возвращает.

        Raises:
            UserNotFound: Если пользователь не найден.
            InvalidUserData: Если код неверный или просрочен.
        """
        logger.info(f"Confirming account for email={email} with code={code}")
        try:
            user = User.objects.get(email=email)
            email_verified = EmailVerified.objects.filter(user=user, confirmation_code=code).first()
            if not email_verified:
                logger.warning(f"Invalid confirmation code for email={email}")
                raise InvalidUserData("Неверный код")
            time_diff = (timezone.now() - email_verified.code_created_at).total_seconds()
            if time_diff > 86400:  # 24 часа
                logger.warning(f"Confirmation code expired for email={email}")
                raise InvalidUserData("Срок действия кода истек")
            user.is_active = True
            user.save()
            email_verified.confirmation_code = None
            email_verified.save()
            logger.info(f"Account confirmed successfully for email={email}")
        except User.DoesNotExist:
            logger.warning(f"User not found for email={email}")
            raise UserNotFound("Пользователь не найден")


class ConfirmPasswordService:
    """Сервис для управления сбросом пароля.

    Предоставляет методы для запроса, валидации и подтверждения сброса пароля.

    Methods:
        request_password_reset: Запрос на сброс пароля.
        validate_reset_params: Проверка параметров сброса пароля.
        confirm_password_reset: Подтверждение сброса пароля.
    """

    @staticmethod
    def request_password_reset(email: str) -> None:
        """Запрос на сброс пароля.

        Args:
            email (str): Адрес электронной почты.

        Raises:
            UserNotFound: Если пользователь с указанным email не найден в системе.
        """
        logger.info(f"Requesting password reset for email={email}")
        try:
            user = User.objects.get(email=email)
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            logger.info(f"Generated uid={uid} for user={user.id}")
            reset_url = f"http://localhost:8000/user/password-reset-confirm/?token={token}&uid={uid}"
            send_password_reset_email.delay(email, reset_url)
            logger.info(f"Password reset requested for email={email}")
        except User.DoesNotExist:
            logger.warning(f"User not found for email={email}")
            raise UserNotFound("Пользователь не найден")

    @staticmethod
    def validate_reset_params(uid: str, token: str) -> str:
        """Проверка параметров для сброса пароля.

        Проверяет наличие uid и token, а также валидность uid как строки base64.

        Args:
            uid (str): Уникальный идентификатор пользователя (base64).
            token (str): Токен для сброса пароля.

        Returns:
            str: Валидированный uid (с восстановленным padding, если необходимо).

        Raises:
            InvalidUserData: Если uid или token отсутствуют или uid не в формате base64.
        """
        logger.info(f"Validating reset parameters for uid={uid}")
        if not uid or not token:
            logger.warning(f"Missing uid or token: uid={uid}, token={token}")
            raise InvalidUserData("Требуются uid и token для сброса пароля")
        try:
            force_str(urlsafe_base64_decode(uid))
            logger.debug(f"Validated uid: {uid}")
            return uid
        except (binascii.Error, TypeError, ValueError):
            logger.warning(f"Invalid base64 uid: {uid}")
            raise InvalidUserData("Идентификатор пользователя должен быть в формате base64")

    @staticmethod
    def confirm_password_reset(uid: str, token: str, new_password: str) -> User:
        """Подтверждение сброса пароля.

        Args:
            uid (str): Уникальный идентификатор пользователя (base64).
            token (str): Токен для сброса пароля.
            new_password (str): Новый пароль.

        Returns:
            User: Пользователь с обновленным паролем.

        Raises:
            InvalidUserData: Если uid, токен или данные некорректны.
            UserNotFound: Если пользователь не найден.
        """
        logger.info(f"Confirming password reset for uid={uid}")
        # Валидация параметров
        validated_uid = ConfirmPasswordService.validate_reset_params(uid, token)
        try:
            user_id = force_str(urlsafe_base64_decode(validated_uid))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                logger.warning(f"Invalid or expired token for user={user_id}")
                raise InvalidUserData("Неверный или просроченный токен")
            user.set_password(new_password)
            user.save()
            logger.info(f"Password reset successfully for user={user_id}")
            return user
        except (binascii.Error, ValueError):
            logger.warning(f"Invalid base64 uid after validation: {validated_uid}")
            raise InvalidUserData("Идентификатор пользователя должен быть в формате base64")
        except User.DoesNotExist:
            logger.warning(f"User not found for uid={validated_uid}")
            raise UserNotFound("Пользователь не найден")
        except Exception as e:
            logger.error(f"Failed to reset password: {str(e)}")
            raise InvalidUserData(f"Ошибка сброса пароля: {str(e)}")
