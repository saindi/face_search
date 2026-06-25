from django.contrib import admin
from face.models import (
    FaceModel,
    RelatedModel,
    AvatarModel,
    DocumentModel,
    SearchLog,
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


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'faces_found', 'matches_found', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['user', 'faces_found', 'matches_found', 'created_at']