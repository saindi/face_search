from django.http import JsonResponse

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

from services import FaceCompare


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
