from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from face.serializers import DocumentSerializers, AvatarSerializers


STATUS = ['success', 'error']
DETAIL = ['На фото нема людей', 'Немає відповідності запису та фотографії', 'Незареєстрований вид джерела']


class InfoSerializers(serializers.Serializer):
    """
        Serializer for found-face records
    """
    documents = DocumentSerializers(many=True, required=False)
    avatars = AvatarSerializers(many=True, required=False)


class FacesSerializers(serializers.Serializer):
    """
        Сериализатор найденого лица на загруженной фотки
    """
    coordinates = serializers.CharField()
    info = InfoSerializers(required=False)


class ResultSerializers(serializers.Serializer):
    """
        Face finder on the uploaded photo
    """
    number_people_uploaded_photo = serializers.IntegerField()
    faces = FacesSerializers(many=True, required=False)


class UploadPhotoSerializers(serializers.Serializer):
    """
        Serializer to retrieve a photo for searching
    """
    photo = serializers.ImageField(write_only=True)


class UploadDataSerializers(serializers.Serializer):
    """
        A serializer to load data from the user (to load data into the database)
    """
    photo = serializers.FileField()
    info = serializers.FileField()

    def validate_photo(self, value):
        if value.content_type != 'application/zip':
            raise ValidationError('Sent data is not an archive')
        return value

    def validate_info(self, value):
        if value.content_type != 'text/plain':
            raise ValidationError('The sent data is not a text file')
        return value
