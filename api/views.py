from django.db import connection
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

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

from services import FaceCompare, DEFAULT_TOLERANCE


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


class FaceDeleteAPIView(APIView):
    """
        View for deleting a face and everything related to it.

        RelatedModel rows are removed via the FaceModel CASCADE, but the
        DocumentModel / AvatarModel rows they point to live in separate
        tables (linked by record_id, not a FK), so they have to be cleaned
        up explicitly to avoid orphaned records.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, TokenAuthentication]

    def delete(self, request, pk):
        face = get_object_or_404(FaceModel, pk=pk)

        relations = face.related.all()

        document_ids = [
            r.record_id for r in relations
            if r.table_name == RelatedModel.TableName.DOCUMENT
        ]
        avatar_ids = [
            r.record_id for r in relations
            if r.table_name == RelatedModel.TableName.AVATAR
        ]

        deleted_documents, _ = DocumentModel.objects.filter(id__in=document_ids).delete()
        deleted_avatars, _ = AvatarModel.objects.filter(id__in=avatar_ids).delete()

        face.delete()  # cascades the RelatedModel rows

        return Response(
            {
                'deleted_face_id': pk,
                'deleted_documents': deleted_documents,
                'deleted_avatars': deleted_avatars,
            },
            status=status.HTTP_200_OK,
        )


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

            Optional query param ?tolerance=<float> overrides the matching
            threshold (must be in the (0, 1] range). Lower is stricter.
        """
        serializer = UploadPhotoSerializers(data=request.data)

        if serializer.is_valid():

            tolerance = DEFAULT_TOLERANCE
            raw_tolerance = request.query_params.get('tolerance')
            if raw_tolerance is not None:
                try:
                    tolerance = float(raw_tolerance)
                except ValueError:
                    return Response(
                        {'tolerance': 'Must be a number in the (0, 1] range.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not 0 < tolerance <= 1:
                    return Response(
                        {'tolerance': 'Must be in the (0, 1] range.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            faces_on_upload_img = FaceCompare(
                serializer.validated_data['photo'], FaceModel.objects.all()
            ).compare(tolerance=tolerance)

            SearchLog.record(request.user, faces_on_upload_img)

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
