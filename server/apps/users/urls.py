from django.urls import path
from apps.users.views import UserRegistration, UserLogin

app_name = 'users'

urlpatterns = [
    path('register/', UserRegistration.as_view(), name='user_registration'),
    path('login/', UserLogin.as_view(), name='user_login'),
]
