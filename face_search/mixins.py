from face_search import settings
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


"""
    Custom Mixins
"""


class WithoutLoginRequiredMixin(object):
    """
        Access only for unauthorized users
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

        return super(WithoutLoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
        Access only for staff members.

        Anonymous users are redirected to the login page; authenticated
        non-staff users get a 403. Used to gate the search analytics /
        audit dashboard, which exposes sensitive log data.
    """
    def test_func(self):
        return self.request.user.is_staff
