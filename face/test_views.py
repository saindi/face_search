"""
Tests for the web FaceSearchView.

FaceCompare and FaceModel are mocked in the view module so the request
cycle (auth gating, form validation, template selection) is exercised
without running real face recognition or hitting the database for faces.
"""
import io
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

User = get_user_model()


def _png_upload(name="photo.png"):
    buf = io.BytesIO()
    Image.new("RGB", (2, 2)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


class FaceSearchViewTests(TestCase):
    def setUp(self):
        self.url = reverse("face:search")
        self.user = User.objects.create_user(
            username="searcher", email="s@example.com", password="pass12345"
        )

    def test_get_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/signin/", response.url)

    def test_get_renders_form_for_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "face/search.html")

    @mock.patch("face.views.FaceModel")
    @mock.patch("face.views.FaceCompare")
    def test_post_valid_photo_runs_search(self, face_compare, _face_model):
        face_compare.return_value.compare.return_value = []
        self.client.force_login(self.user)

        response = self.client.post(self.url, {"img": _png_upload()})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "face/result.html")
        face_compare.assert_called_once()
        face_compare.return_value.compare.assert_called_once_with()

    @mock.patch("face.views.FaceCompare")
    def test_post_without_photo_redisplays_form(self, face_compare):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "face/search.html")
        face_compare.assert_not_called()
