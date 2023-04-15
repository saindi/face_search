from django.core.management.base import BaseCommand
import json
from face.models import (
    FaceModel,
    RelatedModel,
    AvatarModel,
    DocumentModel,
)


class Command(BaseCommand):
    """
        Creating fixtures for all tables in the database

        Example:
            python manage.py dump_data
    """

    def get_face(self):
        data_for_json = []

        models = FaceModel.objects.all()
        for model in models:
            info = {}
            info['model'] = 'face.facemodel'
            info['pk'] = model.pk
            info['fields'] = {
                "face_encoding": model.face_encoding,
            }

            data_for_json.append(info)

        with open('face/fixtures/faces.json', 'w') as outfile:
            json.dump(data_for_json, outfile, indent=4)

    def get_related(self):
        data_for_json = []

        models = RelatedModel.objects.all()
        for model in models:
            info = {}
            info['model'] = 'face.relatedmodel'
            info['pk'] = model.pk
            info['fields'] = {
                "face_id": model.face.id,
                "table_name": model.table_name,
                "record_id": model.record_id,
            }

            data_for_json.append(info)

        with open('face/fixtures/related.json', 'w') as outfile:
            json.dump(data_for_json, outfile, indent=4)

    def get_document(self):
        data_for_json = []

        models = DocumentModel.objects.all()
        for model in models:
            info = {}
            info['model'] = 'face.documentmodel'
            info['pk'] = model.pk
            info['fields'] = {
                "source": model.source,
                "document_number": model.document_number,
                "name": model.name,
            }

            data_for_json.append(info)

        with open('face/fixtures/documents.json', 'w') as outfile:
            json.dump(data_for_json, outfile, indent=4)

    def get_avatar(self):
        data_for_json = []

        models = AvatarModel.objects.all()
        for model in models:
            info = {}
            info['model'] = 'face.avatarmodel'
            info['pk'] = model.pk
            info['fields'] = {
                "source": model.source,
                "profile_id": model.profile_id,
                "name": model.name,
            }

            data_for_json.append(info)

        with open('face/fixtures/avatars.json', 'w') as outfile:
            json.dump(data_for_json, outfile, indent=4)


    def handle(self, *args, **options):

        self.get_face()
        self.get_related()
        self.get_document()
        self.get_avatar()

        self.stdout.write(f'Success')
