from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from face.models import (
    FaceModel,
    RelatedModel,
    DocumentModel,
    AvatarModel,
)

User = get_user_model()


def create_user(**kwargs):
    defaults = {
        "username": "tester",
        "email": "tester@example.com",
        "password": "pass12345",
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


class HealthCheckTests(APITestCase):
    def test_health_ok_without_auth(self):
        response = self.client.get(reverse("api:health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["database"], "ok")


class AuthRequirementTests(APITestCase):
    def test_stats_requires_auth(self):
        response = self.client.get(reverse("api:stats"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_identify_requires_auth(self):
        response = self.client.get(reverse("api:identify"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_face_delete_requires_auth(self):
        response = self.client.delete(reverse("api:face-delete", args=[1]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StatsTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(create_user())

    def test_stats_counts_and_breakdown(self):
        FaceModel.objects.create(face_encoding="0.1 0.2")
        DocumentModel.objects.create(source="passport", document_number="1", name="A")
        DocumentModel.objects.create(source="driver_license", document_number="2", name="B")
        AvatarModel.objects.create(source="vk", profile_id="x", name="C")

        response = self.client.get(reverse("api:stats"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["faces"], 1)
        self.assertEqual(response.data["documents"]["total"], 2)
        self.assertEqual(response.data["documents"]["by_source"]["passport"], 1)
        self.assertEqual(response.data["documents"]["by_source"]["driver_license"], 1)
        self.assertEqual(response.data["avatars"]["total"], 1)
        self.assertEqual(response.data["avatars"]["by_source"]["vk"], 1)


class FaceDeleteTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(create_user())

    def test_delete_removes_face_and_linked_records(self):
        face = FaceModel.objects.create(face_encoding="0.1")
        document = DocumentModel.objects.create(source="passport", document_number="1", name="A")
        avatar = AvatarModel.objects.create(source="vk", profile_id="x", name="C")
        RelatedModel.objects.create(
            face=face, table_name=RelatedModel.TableName.DOCUMENT, record_id=document.id
        )
        RelatedModel.objects.create(
            face=face, table_name=RelatedModel.TableName.AVATAR, record_id=avatar.id
        )

        response = self.client.delete(reverse("api:face-delete", args=[face.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(FaceModel.objects.filter(id=face.id).exists())
        self.assertFalse(DocumentModel.objects.filter(id=document.id).exists())
        self.assertFalse(AvatarModel.objects.filter(id=avatar.id).exists())
        self.assertEqual(RelatedModel.objects.count(), 0)

    def test_delete_missing_face_returns_404(self):
        response = self.client.delete(reverse("api:face-delete", args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TokenTests(APITestCase):
    def test_valid_credentials_return_token(self):
        create_user(username="bob", email="bob@example.com", password="secret12345")

        response = self.client.post(
            reverse("api:token"), {"username": "bob", "password": "secret12345"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.json())

    def test_invalid_credentials_return_401(self):
        response = self.client.post(
            reverse("api:token"), {"username": "ghost", "password": "nope"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
