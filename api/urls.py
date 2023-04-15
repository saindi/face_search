from django.urls import path
from rest_framework.authtoken.views import ObtainAuthToken

from api import views


app_name = 'api'

urlpatterns = [
    path('api/token/', views.GenerateTokenView.as_view(), name='token'),
    path('api/token-auth/', ObtainAuthToken.as_view(), name='api-token-auth'),

    path('api/identify/', views.IdentifyAPIView.as_view(), name="identify"),
]