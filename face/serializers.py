from rest_framework import serializers
from face.models import (
    FaceModel,
    RelatedModel,
    AvatarModel,
    DocumentModel,
)


class FaceSerializers(serializers.ModelSerializer):
    """
        Face model serializer
    """
    class Meta:
        model = FaceModel
        fields = ["face_encoding"]


class RelatedSerializers(serializers.ModelSerializer):
    """
        Link serializer
    """
    class Meta:
        model = RelatedModel
        fields = ["face_id", "table_name", "record_id"]


class AvatarSerializers(serializers.ModelSerializer):
    """
        Avatar serializer
    """
    class Meta:
        model = AvatarModel
        fields = ["source", "profile_id", "name"]


class DocumentSerializers(serializers.ModelSerializer):
    """
        Document model serializer
    """
    class Meta:
        model = DocumentModel
        fields = ["source", "document_number", "name"]
