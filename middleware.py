from django.shortcuts import redirect
from django.urls import reverse


class SecurityHeadersMiddleware:
    """Adds a Content-Security-Policy and Permissions-Policy suited to the portal."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        response.setdefault("Permissions-Policy", "geolocation=(self), camera=(self), microphone=()")
        return response


class ForcePasswordChangeMiddleware:
    """Users created by the administrator must change their password at first login."""

    ALLOWED = ("password_change", "logout", "login")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            prof = getattr(user, "profile", None)
            if prof and prof.must_change_password:
                allowed = [reverse(n) for n in self.ALLOWED]
                if request.path not in allowed and not request.path.startswith("/static/"):
                    return redirect("password_change")
        return self.get_response(request)
