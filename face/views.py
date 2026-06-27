import csv
from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from face_search.mixins import StaffRequiredMixin

from face.forms import LoadPhotoForm
from face.models import AvatarModel, DocumentModel, FaceModel, SearchLog

from services import FaceCompare

# How many days the dashboard covers by default when no range is given.
DEFAULT_RANGE_DAYS = 30
# Cap on rows shown in the recent-searches table (export has no cap).
RECENT_LIMIT = 100


def _parse_date(raw):
    """Parse a YYYY-MM-DD query param, returning None on anything invalid."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def filter_search_logs(request):
    """
        Build a SearchLog queryset from the request's filter query params,
        shared by the dashboard and the CSV export so both honour the same
        filters.

        Supported params:
          date_from / date_to  YYYY-MM-DD (default: last DEFAULT_RANGE_DAYS days)
          user                 username contains (case-insensitive)
          matches              "with" / "without" (default: any)

        :return: (queryset, filters_dict) where filters_dict echoes the
                 resolved values back for the template / CSV headers.
    """
    today = timezone.localdate()

    date_to = _parse_date(request.GET.get("date_to")) or today
    date_from = _parse_date(request.GET.get("date_from")) or (
        date_to - timedelta(days=DEFAULT_RANGE_DAYS - 1)
    )
    if date_from > date_to:
        date_from, date_to = date_to, date_from

    username = (request.GET.get("user") or "").strip()
    matches = (request.GET.get("matches") or "").strip()

    queryset = SearchLog.objects.select_related("user").filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )

    if username:
        queryset = queryset.filter(user__username__icontains=username)

    if matches == "with":
        queryset = queryset.filter(matches_found__gt=0)
    elif matches == "without":
        queryset = queryset.filter(matches_found=0)

    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "user": username,
        "matches": matches,
    }
    return queryset, filters


class FaceSearchView(LoginRequiredMixin, View):
    """
        View for finding a face
    """
    def get(self, request):
        context = {"form": LoadPhotoForm()}
        return render(request, 'face/search.html', context)

    def post(self, request):
        form = LoadPhotoForm(request.POST, request.FILES)

        if form.is_valid():
            faces_on_upload_img = FaceCompare(form.img, FaceModel.objects.all()).compare()

            SearchLog.record(request.user, faces_on_upload_img)

            FaceModel.get_info_on_faces(faces_on_upload_img)

            context = {
                "faces": faces_on_upload_img,
            }

            return render(request, 'face/result.html', context)

        else:
            context = {"form": form}
            return render(request, 'face/search.html', context)


class DashboardView(StaffRequiredMixin, View):
    """
        Staff-only analytics & audit dashboard.

        Summarises search activity (totals, success rate, daily trend, top
        users) over the selected date range together with the current size
        of the database, broken down by source.
    """
    @staticmethod
    def _by_source(model):
        return list(
            model.objects.values("source")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

    def _daily_series(self, queryset, date_from, date_to):
        """
            Searches-per-day over the whole range, with empty days filled
            in as zeros so the bar chart has no gaps. Each entry carries a
            percentage height for the CSS bars.
        """
        counts = {
            row["day"]: row["count"]
            for row in queryset.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
        }

        series = []
        day = date_from
        while day <= date_to:
            series.append({"day": day, "count": counts.get(day, 0)})
            day += timedelta(days=1)

        peak = max((entry["count"] for entry in series), default=0)
        for entry in series:
            entry["height"] = round(entry["count"] / peak * 100) if peak else 0

        return series

    def get(self, request):
        queryset, filters = filter_search_logs(request)

        totals = queryset.aggregate(
            total_searches=Count("id"),
            faces_detected=Sum("faces_found"),
            matches=Sum("matches_found"),
            searches_with_matches=Count("id", filter=Q(matches_found__gt=0)),
        )
        total_searches = totals["total_searches"] or 0
        searches_with_matches = totals["searches_with_matches"] or 0
        success_rate = (
            round(searches_with_matches / total_searches * 100, 1)
            if total_searches
            else 0
        )

        top_users = list(
            queryset.filter(user__isnull=False)
            .values("user__username")
            .annotate(searches=Count("id"), matches=Sum("matches_found"))
            .order_by("-searches")[:10]
        )

        context = {
            "filters": filters,
            "summary": {
                "total_searches": total_searches,
                "searches_with_matches": searches_with_matches,
                "success_rate": success_rate,
                "faces_detected": totals["faces_detected"] or 0,
                "matches": totals["matches"] or 0,
            },
            "database": {
                "faces": FaceModel.objects.count(),
                "documents": DocumentModel.objects.count(),
                "avatars": AvatarModel.objects.count(),
                "documents_by_source": self._by_source(DocumentModel),
                "avatars_by_source": self._by_source(AvatarModel),
            },
            "daily": self._daily_series(queryset, filters["date_from"], filters["date_to"]),
            "top_users": top_users,
            "recent": queryset[:RECENT_LIMIT],
            "recent_limit": RECENT_LIMIT,
        }
        return render(request, "face/dashboard.html", context)


class SearchLogExportView(StaffRequiredMixin, View):
    """
        Stream the filtered search log as CSV for compliance / offline
        analysis. Honours the same query params as the dashboard.
    """
    def get(self, request):
        queryset, filters = filter_search_logs(request)

        filename = f"search_log_{filters['date_from']}_{filters['date_to']}.csv"
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(["id", "user", "faces_found", "matches_found", "created_at"])
        for log in queryset.iterator():
            writer.writerow([
                log.id,
                log.user.username if log.user else "",
                log.faces_found,
                log.matches_found,
                log.created_at.isoformat(),
            ])

        return response
