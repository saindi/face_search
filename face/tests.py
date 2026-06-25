from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from face.models import SearchLog

User = get_user_model()


class SearchLogTests(TestCase):
    def test_record_counts_faces_and_matches(self):
        user = User.objects.create_user(
            username="u", email="u@example.com", password="pass12345"
        )
        faces = [
            {"coordinates": "a", "coincidences": [object(), object()]},
            {"coordinates": "b", "coincidences": []},
        ]

        log = SearchLog.record(user, faces)

        self.assertEqual(log.user, user)
        self.assertEqual(log.faces_found, 2)
        self.assertEqual(log.matches_found, 2)

    def test_record_anonymous_user_is_stored_as_null(self):
        log = SearchLog.record(AnonymousUser(), [])

        self.assertIsNone(log.user)
        self.assertEqual(log.faces_found, 0)
        self.assertEqual(log.matches_found, 0)
