from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.accounts.views import CurrentUserView, UserRegistrationView


urlpatterns = [
    path(
        "auth/token/",
        TokenObtainPairView.as_view(),
        name="token-obtain-pair",
    ),
    path(
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "auth/token/blacklist/",
        TokenBlacklistView.as_view(),
        name="token-blacklist",
    ),
    path("users/me/", CurrentUserView.as_view(), name="current-user"),
    path("users/", UserRegistrationView.as_view(), name="user-registration"),
]
