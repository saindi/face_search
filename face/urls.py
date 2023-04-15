from django.urls import path
from django.views.generic import TemplateView, RedirectView
from face import views


app_name = "face"

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='face:search'), name="home"),
    path('search/', views.FaceSearchView.as_view(), name="search"),
]
