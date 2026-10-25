from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from inspections.forms import LockoutAuthenticationForm
from inspections.views_auth import PasswordChange

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="inspections/login.html",
                                                authentication_form=LockoutAuthenticationForm,
                                                redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password/", PasswordChange.as_view(), name="password_change"),
    path("django-admin/", admin.site.urls),
    path("", include("inspections.urls")),
]
