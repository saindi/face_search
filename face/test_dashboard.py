"""
Tests for the staff-only analytics / audit dashboard and its CSV export.

These exercise access control, metric aggregation, the filter params
shared by both views, and the CSV output. No face recognition is
involved — SearchLog rows are created directly.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from face.models import SearchLog

User = get_user_model()


class DashboardAccessTests(TestCase):
    def setUp(self):
        self.url = reverse("face:dashboard")
        self.staff = User.objects.create_user(
            username="boss", email="boss@example.com", password="pass12345", is_staff=True
        )
        self.member = User.objects.create_user(
            username="member", email="m@example.com", password="pass12345"
        )

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/signin/", response.url)

    def test_non_staff_forbidden(self):
        self.client.force_login(self.member)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_staff_allowed(self):
        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "face/dashboard.html")


class DashboardMetricsTests(TestCase):
    def setUp(self):
        self.url = reverse("face:dashboard")
        self.staff = User.objects.create_user(
            username="boss", email="boss@example.com", password="pass12345", is_staff=True
        )
        self.client.force_login(self.staff)

        # 2 searches with matches, 1 without.
        SearchLog.objects.create(user=self.staff, faces_found=2, matches_found=3)
        SearchLog.objects.create(user=self.staff, faces_found=1, matches_found=1)
        SearchLog.objects.create(user=self.staff, faces_found=1, matches_found=0)

    def test_summary_totals(self):
        response = self.client.get(self.url)
        summary = response.context["summary"]

        self.assertEqual(summary["total_searches"], 3)
        self.assertEqual(summary["searches_with_matches"], 2)
        self.assertEqual(summary["faces_detected"], 4)
        self.assertEqual(summary["matches"], 4)
        self.assertEqual(summary["success_rate"], round(2 / 3 * 100, 1))

    def test_matches_filter(self):
        with_matches = self.client.get(self.url, {"matches": "with"})
        without = self.client.get(self.url, {"matches": "without"})

        self.assertEqual(with_matches.context["summary"]["total_searches"], 2)
        self.assertEqual(without.context["summary"]["total_searches"], 1)

    def test_date_range_excludes_old_logs(self):
        old = SearchLog.objects.create(user=self.staff, faces_found=9, matches_found=9)
        # auto_now_add ignores assignment on create, so backdate via update().
        SearchLog.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=90)
        )

        response = self.client.get(self.url)

        # Default range is the last DEFAULT_RANGE_DAYS days -> the 90-day-old
        # row is excluded, leaving the 3 created in setUp.
        self.assertEqual(response.context["summary"]["total_searches"], 3)

    def test_user_filter(self):
        other = User.objects.create_user(
            username="other", email="o@example.com", password="pass12345"
        )
        SearchLog.objects.create(user=other, faces_found=1, matches_found=1)

        response = self.client.get(self.url, {"user": "other"})

        self.assertEqual(response.context["summary"]["total_searches"], 1)


class DashboardExportTests(TestCase):
    def setUp(self):
        self.url = reverse("face:dashboard-export")
        self.staff = User.objects.create_user(
            username="boss", email="boss@example.com", password="pass12345", is_staff=True
        )
        self.member = User.objects.create_user(
            username="member", email="m@example.com", password="pass12345"
        )

    def test_export_requires_staff(self):
        self.client.force_login(self.member)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_export_returns_csv(self):
        self.client.force_login(self.staff)
        SearchLog.objects.create(user=self.staff, faces_found=2, matches_found=1)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment; filename=", response["Content-Disposition"])

        body = response.content.decode("utf-8")
        self.assertIn("id,user,faces_found,matches_found,created_at", body)
        self.assertIn("boss", body)
