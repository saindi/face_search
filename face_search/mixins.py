from face_search import settings
from django.http import HttpResponseRedirect


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
