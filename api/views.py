from django.db import connection
from django.db.models import Count
from django.http import JsonResponse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken

from api.serializers import (
    ResultSerializers,
    UploadPhotoSerializers,
    UploadDataSerializers,
)

from face.models import load_data, FaceModel, DocumentModel, AvatarModel
from user.models import UserModel

from services import FaceCompare


class HealthCheckAPIView(APIView):
    """
        Liveness/readiness probe. Reports whether the app is up and the
        database is reachable. Intended for Docker / nginx / monitoring,
        so it is intentionally unauthenticated.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            database_ok = True
        except Exception:
            database_ok = False

        return Response(
            {
                'status': 'ok' if database_ok else 'error',
                'database': 'ok' if database_ok else 'unreachable',
            },
            status=status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class GenerateTokenView(APIView):
    """
        View for jwt access_token generation
    """
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            user = UserModel.objects.get(username=username)
            if user.check_password(password):
                access_token = AccessToken.for_user(user)
                return JsonResponse({'access_token': str(access_token)})
        except UserModel.DoesNotExist:
            pass

        return JsonResponse({'error': 'Invalid credentials'}, status=401)


class StatsAPIView(APIView):
    """
        View for database statistics: how many faces / documents / avatars
        are stored and how they are split by source.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, TokenAuthentication]

    @staticmethod
    def _by_source(queryset):
        return {
            row['source']: row['count']
            for row in queryset.values('source').annotate(count=Count('id')).order_by('source')
        }

    def get(self, request):
        return Response({
            'faces': FaceModel.objects.count(),
            'documents': {
                'total': DocumentModel.objects.count(),
                'by_source': self._by_source(DocumentModel.objects),
            },
            'avatars': {
                'total': AvatarModel.objects.count(),
                'by_source': self._by_source(AvatarModel.objects),
            },
        })


class IdentifyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, TokenAuthentication]

    def get(self, request):
        """
            Find a match for the photo
        """
        serializer = UploadPhotoSerializers(data=request.data)

        if serializer.is_valid():

            faces_on_upload_img = FaceCompare(serializer.validated_data['photo'], FaceModel.objects.all()).compare()

            FaceModel.get_info_on_faces(faces_on_upload_img)

            s = ResultSerializers({
                'number_people_uploaded_photo': len(faces_on_upload_img),
                'faces': faces_on_upload_img
            })

            return Response(s.data)
        else:
            return Response(serializer.errors)

    def post(self, request):
        """
            Downloading new data
        """
        serializer = UploadDataSerializers(data=request.data)

        if serializer.is_valid():
            result = load_data(serializer.validated_data['photo'], serializer.validated_data['info'])
            return Response(result)
        else:
            return Response(serializer.errors)
