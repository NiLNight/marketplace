from django.urls import path

from apps.users.views import UserRegistration

app_name = 'users'

urlpatterns = [
    path('register/', UserRegistration.as_view(), name='user_registration'),
]
