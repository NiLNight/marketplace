from django.urls import path
from apps.users.views import (UserRegistrationView,
                              UserLoginView,
                              UserLogoutView,
                              UserProfileView,
                              CustomTokenObtainPairView)

app_name = 'users'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user_registration'),
    path('login/', CustomTokenObtainPairView.as_view(), name='user_login'),
    path('logout/', UserLogoutView.as_view(), name='user_logout'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]
