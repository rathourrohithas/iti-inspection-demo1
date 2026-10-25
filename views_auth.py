from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

from . import audit


class PasswordChange(PasswordChangeView):
    template_name = "inspections/password_change.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        resp = super().form_valid(form)
        prof = getattr(self.request.user, "profile", None)
        if prof and prof.must_change_password:
            prof.must_change_password = False
            prof.save(update_fields=["must_change_password"])
        audit.log(self.request, "PASSWORD_CHANGED")
        messages.success(self.request, "Your password has been changed.")
        return resp
