from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from face_search.mixins import WithoutLoginRequiredMixin
from user.forms import SignInForm, SignUpForm
from user.models import UserModel
from django.contrib.auth import login


class UserView(LoginRequiredMixin, TemplateView):
    """
        View for user profile
    """
    template_name = 'user/user.html'


class SignInView(WithoutLoginRequiredMixin, LoginView):
    """
        View user login
    """
    template_name = 'user/signin.html'
    form_class = SignInForm

    def form_valid(self, form):
        login(self.request, form.get_user())

        return redirect(reverse_lazy('face:search'))


class SignUpView(WithoutLoginRequiredMixin, CreateView):
    """
        View user registration
    """
    model = UserModel
    template_name = 'user/signup.html'
    form_class = SignUpForm

    def form_valid(self, form):
        form.save(commit=False)

        return redirect(reverse_lazy('user:sign-in'))
