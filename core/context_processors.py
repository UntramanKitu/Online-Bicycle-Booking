from django.db import DatabaseError

from .models import Maintenance


def nav_counts(request):
    """Number of maintenance reports waiting for triage, shown as a badge in the sidebar."""
    try:
        pending = Maintenance.objects.filter(status=Maintenance.Status.PENDING).count()
    except DatabaseError:
        pending = 0
    return {"nav_pending": pending}
