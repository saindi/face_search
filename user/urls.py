from django.contrib.auth.views import LogoutView
from django.urls import path
from user import views


app_name = 'user'

urlpatterns = [
    path('user/', views.UserView.as_view(), name='profile'),
    path('signin/', views.SignInView.as_view(), name='sign-in'),
    path('signup/', views.SignUpView.as_view(), name='sign-up'),
    path('logout/', LogoutView.as_view(next_page='face:home'), name='logout'),
]