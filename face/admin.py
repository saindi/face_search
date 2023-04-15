from django.contrib import admin
from face.models import (
    FaceModel,
    RelatedModel,
    AvatarModel,
    DocumentModel,
)


@admin.register(FaceModel)
class FaceModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'face_encoding']


@admin.register(RelatedModel)
class RelatedModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'face', 'record_id']


@admin.register(DocumentModel)
class DocumentModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'source', 'document_number', 'name']


@admin.register(AvatarModel)
class AvatarModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'source', 'profile_id', 'name']