from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def age(value):
    """Short relative time for lists: "just now", "10 hours", "3 days", "2 weeks"."""
    if not value:
        return ""
    seconds = int((timezone.now() - value).total_seconds())
    if seconds < 60:
        return "just now"
    for size, unit in ((86400 * 365, "year"), (86400 * 30, "month"), (86400 * 7, "week"),
                       (86400, "day"), (3600, "hour"), (60, "minute")):
        if seconds >= size:
            count = seconds // size
            return f"{count} {unit}{'' if count == 1 else 's'}"
    return "just now"
