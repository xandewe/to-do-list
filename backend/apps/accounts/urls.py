from django.urls import path

from apps.accounts.views import UserRegistrationView


urlpatterns = [
    path("users/", UserRegistrationView.as_view(), name="user-registration"),
]
