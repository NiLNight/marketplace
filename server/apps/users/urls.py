from django.urls import path
from apps.users.views import UserRegistration, UserLogin, UserLogout

app_name = 'users'

urlpatterns = [
    path('register/', UserRegistration.as_view(), name='user_registration'),
    path('login/', UserLogin.as_view(), name='user_login'),
    path('logout/', UserLogout.as_view(), name='user_logout'),
]
