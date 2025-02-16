from django.urls import path
from apps.users.views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    ResendCodeView,
    ConfirmView,
    PasswordResetRequestView,
    PasswordResetConfirmView
)

app_name = 'users'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user_registration'),
    path('login/', UserLoginView.as_view(), name='user_login'),
    path('logout/', UserLogoutView.as_view(), name='user_logout'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('resend-code/', ResendCodeView.as_view(), name='resend_code'),
    path('confirm-code/', ConfirmView.as_view(), name='confirm_code'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
