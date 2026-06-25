from django.http import JsonResponse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken

from api.serializers import (
    ResultSerializers,
    UploadPhotoSerializers,
    UploadDataSerializers,
)

from face.models import load_data, FaceModel
from user.models import UserModel

from services import FaceCompare, DEFAULT_TOLERANCE


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
