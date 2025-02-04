from django.urls import path
from apps.users.views import (UserRegistrationView,
                              UserLoginView,
                              UserLogoutView,
                              UserProfileView)

app_name = 'users'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user_registration'),
    path('login/', UserLoginView.as_view(), name='user_login'),
    path('logout/', UserLogoutView.as_view(), name='user_logout'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]
