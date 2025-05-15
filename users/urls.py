# accounts/urls.py
from django.urls import path
from .views import (
    profile_manage_view
)

app_name = 'accounts'

urlpatterns = [
    path('profile/', profile_manage_view, name='profile'),
 
]
